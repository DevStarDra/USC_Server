from typing import List, Optional, Type, Union

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import (SearchQuery, SearchRank,
                                            SearchVectorField)
from django.db import models, transaction
from django.db.models import F
from django.db.models.manager import Manager
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.safestring import mark_safe
from utils.data import (get_collection_name, get_content_text,
                        get_content_title_css_file, request_data)
from utils.sort import is_a_gt_b
from utils.validators import validate_collection_code


class NodeManager(Manager):
    def full_text_search(self, query: str):
        to_query = SearchQuery(query)
        rank = SearchRank(F('vector_column'), to_query)

        # Get the latest year
        year_nodes = Collection.objects.first().get_child_nodes()
        max_year = int(max(year_nodes, key=lambda x: x.title).title)
        # max_year = 1994

        return self.get_queryset()\
            .filter(selected_year_from=max_year)\
            .filter(vector_column=to_query)\
            .annotate(rank=rank)\
            .order_by('-rank')[:settings.SEARCH_MAX_RESULTS]


class Collection(models.Model):
    """A processing code for a node"""

    code = models.CharField(
        max_length=200, validators=[validate_collection_code])
    name = models.CharField(max_length=200, default='', editable=False)

    def __str__(self):
        return self.code

    class Meta:
        verbose_name_plural = "Collections"

    def start_scraper(self):
        with transaction.atomic():
            years_nodes = self.get_child_nodes()

            # Get the lastest year node
            max_year = 0
            lastest_year: Optional[Node] = None
            for year in years_nodes:
                if int(year.title) > max_year:
                    lastest_year = year
                    max_year = int(year.title)

            if lastest_year is None:
                return

            lastest_year.scrape_it_all()

    def get_full_path(self):
        """Get the full path of the collection"""
        return f"{settings.GOV_URL}/{self.code}"

    def get_child_nodes(self) -> models.query.QuerySet['Node']:
        """Get all the child nodes of the collection"""
        nodes = self.node_set.all()

        if len(nodes) > 0:
            return nodes

        # If there are no children, get the children from the API
        return self.new_child_nodes()

    def new_child_nodes(self):
        """Get and create new child nodes"""

        url = self.get_full_path()

        # Get the child nodes from the API
        data: dict = request_data(url)
        if data:
            # Create the child nodes
            childNodes: List[dict] = data.get('childNodes')
            for child_node in childNodes:
                self.add_child_node(child_node['nodeValue'])

            # Return the child nodes
            return self.node_set.all()

        return Node.objects.none()

    def add_child_node(self, child_node: dict):
        # Create a child node
        node = Node(
            collection=self,
            collection_code=self,
            root_node=True,
            title=child_node.get('title'),
            level=child_node.get('level'),
            browse_path=child_node.get('browsePath'),
            node_type=child_node.get('nodetype'),
        )
        node.save()
        return node

    def get_absolute_url(self):
        """Get the url to the collection"""
        return reverse(f'{settings.USCODE}:collection')

    def get_bread_crumbs(self):
        """Get single crumb"""
        return mark_safe(f"""
        <li class="breadcrumb-item">
            <a href='{self.get_absolute_url()}'>{self.name}</a>
        </li>
        """)


class Node(models.Model):
    """A node in the govinfo.gov graph"""

    objects = NodeManager()

    node_set: models.query.QuerySet['Node']

    NODE_TYPES = (
        ('node', 'node'),
        ('leaf', 'leaf'),
    )

    SECTION_TYPES = (
        ('TOC', 'TOC'),
        ('FRONTMATTER', 'FRONTMATTER'),
        ('TOPPARENT', 'TOPPARENT'),
        ('LEAF', 'LEAF')
    )

    slug_id = models.CharField(max_length=1024, unique=True)

    package_id = models.CharField(max_length=200, null=True, blank=True)
    granule_id = models.CharField(max_length=200, null=True, blank=True)

    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE, null=True, blank=True)
    collection_code = models.ForeignKey(
        Collection, on_delete=models.CASCADE, related_name="collectionCode")
    selected_year_from = models.IntegerField(null=True, blank=True)

    root_node = models.BooleanField()

    title = models.CharField(max_length=1024)
    title_number = models.IntegerField(null=True, blank=True)
    heading = models.CharField(max_length=1024)
    section = models.CharField(max_length=20, choices=SECTION_TYPES)

    textfile = models.CharField(max_length=1024)
    htmlfile = models.CharField(max_length=1024)
    pdffile = models.CharField(max_length=1024)
    level = models.IntegerField()
    parent: Type['Node'] = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True)
    browse_path = models.CharField(max_length=1024)
    browse_path_alias = models.CharField(max_length=1024)

    node_type = models.CharField(
        max_length=4,
        choices=NODE_TYPES,
    )
    this_node = models.CharField(max_length=1024)
    leaf_number_from = models.CharField(max_length=20, null=True, blank=True)
    leaf_number_to = models.CharField(max_length=20, null=True, blank=True)

    content = models.CharField(max_length=1_000_000, blank=True, null=True)

    vector_column = SearchVectorField(null=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Nodes"
        indexes = (GinIndex(fields=["vector_column"]),)
        db_table = 'uscode_node'

    def get_collection_name(self):
        """Get the collection name"""
        return settings.USCODE

    def has_children(self):
        """Check if the node has children"""
        return self.node_type == 'node'

    def get_browse_path(self):
        return self.browse_path or self.join_paths(
            str(self.selected_year_from), self.browse_path_alias
        )

    def scrape_it_all(self):
        """Run recursively through available
        results and call get child nodes"""
        children = self.get_child_nodes() or []

        for child in children:
            child.scrape_it_all()

    def new_child_nodes(self):
        """Get and create new child nodes"""

        path = self.get_browse_path()

        url = self.join_paths(
            self.collection_code.get_full_path(),
            path
        )

        # Get the child nodes from the API
        data: dict = request_data(url)
        if data:
            # Create the child nodes
            childNodes: List[dict] = data.get('childNodes')
            for child_node in childNodes:
                self.add_child_node(child_node['nodeValue'])

            # Return the child nodes
            return self.node_set.all()

        return Node.objects.none()

    def add_child_node(self, child_node: dict):
        # Create a child node
        print("added", child_node.get('heading'))

        title = child_node.get('title')

        if title:
            node = Node(
                package_id=child_node.get('packageid'),
                granule_id=child_node.get('granuleid'),
                collection_code=self.collection_code,
                root_node=False,
                title=title,
                title_number=child_node.get('titlenumber'),
                heading=child_node.get('heading') or "",
                section=child_node.get('section') or "",
                textfile=child_node.get('textfile'),
                htmlfile=child_node.get('htmlfile'),
                pdffile=child_node.get('pdffile'),
                level=child_node.get('level'),
                selected_year_from=child_node.get('selectedYearFrom'),
                parent=self,
                browse_path_alias=child_node.get('browsePathAlias'),
                node_type=child_node.get('nodetype'),
                this_node=child_node.get('thisnode'),
                leaf_number_from=child_node.get('leafnumberfrom'),
                leaf_number_to=child_node.get('leafnumberto'),
            )

            if node.node_type == 'leaf' and node.section == 'LEAF':
                text = get_content_text(node.get_document_link())
                node.content = text

            node.save()
            return node

    def get_child_nodes(self):
        """Get the children of the node"""
        if self.has_children():
            print(f"Getting child nodes for {str(self)}")
            nodes = self.node_set.all()

            if len(nodes) > 0:
                return nodes

            with transaction.atomic():
                return self.new_child_nodes()

        return None

    def section_within_node(self, section: str):
        """Check if the section is within the node"""
        leaf_from = self.leaf_number_from
        leaf_to = self.leaf_number_to

        if is_a_gt_b(leaf_from, section):
            return False

        if is_a_gt_b(section, leaf_to):
            return False

        return True

    def drill_down_to_section_leaf(self, section: str):
        """Drill down to a section leaf"""
        nodes = self.get_child_nodes()

        # Filter for nodes that section type is not TOC or FRONTMATTER
        nodes = nodes.exclude(section__in=['TOC', 'FRONTMATTER'])

        if not nodes:
            return None

        # Check if any node in the nodes has a node_type of leaf
        test_node = nodes[0]
        if test_node.node_type == 'leaf':
            for node in nodes:
                if node.leaf_number_from == node.leaf_number_to:
                    if node.leaf_number_from == section:
                        return node
                elif node.section_within_node(section):
                    return node
            return None

        # If there are no nodes with a node_type of leaf, drill down
        for node in nodes:
            if node.section_within_node(section):
                section_node: Node = node.drill_down_to_section_leaf(section)
                if section_node:
                    return section_node

        return None

    def get_root_node(self):
        """Get the selected year node, root node for this node"""
        if self.root_node:
            return self
        top_nodes = self.collection_code.get_child_nodes()
        return top_nodes.filter(
            title=self.selected_year_from,
        ).first()

    def search(self, titlenumber: str, section: int):
        """Search for a section"""

        root_node = self.get_root_node()

        title_node = root_node.get_child_nodes()\
            .filter(title_number=titlenumber)\
            .filter(node_type='node')\
            .first()

        if not title_node:
            return None

        return title_node.drill_down_to_section_leaf(section)

    def get_sections_text(self):
        """Get the text of the sections"""
        num = self.leaf_number_from
        if self.leaf_number_to:
            num = f"{self.leaf_number_from} - {self.leaf_number_to}"
        return f"(Sections {num})"

    def get_title(self):
        """Get the full title of the node"""

        texts = []

        if (
            self.section == "TOC" or
            self.section == "FRONTMATTER" or
            self.root_node
        ):
            texts = [self.title]

        elif self.level == 1:
            texts = [self.this_node, self.title, self.get_sections_text()]

        elif self.node_type == "leaf":
            texts = [self.heading, self.title]

        else:
            texts = [self.heading, self.title, self.get_sections_text()]

        return " - ".join(texts)

    def join_paths(self, *args) -> str:
        """Join paths together"""
        return "/".join(args)

    def get_parent(self) -> Union["Node", Collection]:
        """Get the parent of the node"""
        if self.collection:
            return self.collection
        return self.parent

    def get_full_path(self):
        """Get the full path of the node"""
        path = self.get_browse_path()
        return self.join_paths(
            self.collection_code.get_full_path(),
            path
        )

    def get_unique_id(self):
        """Get a unique id for the node"""
        if self.root_node:
            return self.title

        return self.granule_id or self.package_id

    def get_document_link(self):
        """Get the link to the leaf"""
        return self.join_paths(
            settings.GOV_CONTENT_URL,
            self.htmlfile
        )

    def get_pdf_link(self):
        """Get the link to the leaf"""
        return self.join_paths(
            settings.GOV_CONTENT_URL,
            self.pdffile
        )

    def pdf_link(self):
        return self.get_pdf_link()

    def get_css_base_link(self):
        """Get the base link for the css"""
        link = self.get_document_link().split('/')
        link.pop()
        return '/'.join(link)

    def get_document(self):
        """Get the html content of the leaf"""
        title, css, html = get_content_title_css_file(self.get_document_link())
        full_css_link = self.join_paths(self.get_css_base_link(), css)
        return title, full_css_link, mark_safe(html)

    def get_document_iframe_link(self):
        """Get the link to the leaf html"""
        return str(
            reverse(
                f'{settings.USCODE}:leaf_content',
                kwargs={'slug_id': self.slug_id}
            )
        )

    def get_view_document_link(self):
        """Get link to help view text html document"""
        return str(reverse(f'{settings.USCODE}:leaf', kwargs={
            'slug_id': self.slug_id
        }))

    def get_html_url(self):
        return self.get_view_document_link()

    def get_node_url(self):
        """Get the url to the node"""
        return str(reverse(f'{settings.USCODE}:node', kwargs={
            'slug_id': self.slug_id
        }))

    def get_crumb(self):
        """Get single crumb"""
        return mark_safe(f"""
        <li class="breadcrumb-item">
            <a href='{self.get_node_url()}'>{self.title}</a>
        </li>
        """)

    def get_bread_crumbs(self):
        """Get the breadcrumbs to get to this node"""
        return mark_safe("".join([
            self.get_parent().get_bread_crumbs(),
            self.get_crumb()
        ]))


# Receiver to automatically create a
# unique slug_id for each node when it is created
@receiver(pre_save, sender=Node)
def create_slug_id(sender, instance: Node, **kwargs):
    if not instance.id:
        instance.slug_id = f"{instance.get_unique_id()}-{get_random_string(5)}"


@receiver(post_save, sender=Collection)
def save_collection_name(sender, instance: Collection, created, **kwargs):
    instance.code = instance.code.upper()
    if created:
        name = get_collection_name(instance.code)
        instance.name = name
        instance.save()
