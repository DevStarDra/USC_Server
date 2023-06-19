from functools import reduce
from typing import Type

from django.conf import settings
from django.db import models, transaction
from django.db.models.manager import Manager
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from utils.data import (cfr_full_text_search, get_cfr_html, get_cfr_json,
                        get_cfr_pdf_link, get_cfr_titles)


def merge(a, b):
    """Merge two queryset"""
    return a | b


class CFRNodeManager(Manager):
    def get_queryset(self) -> models.QuerySet['CFRNode']:
        return super().get_queryset().select_related('parent')

    def full_text_search(self, query: str) -> models.QuerySet['CFRNode']:
        """Full text search"""
        results = cfr_full_text_search(query)

        # get the titles
        titles = self.get_titles()

        sections: list[models.query.QuerySet['CFRNode']] = []

        worked_on = {}

        for res in results:

            _t = res['title']
            _s = res['section']

            _check_t = worked_on.get(_t)
            if _check_t is not None:
                if _s == _check_t:
                    continue

            title = titles.get(identifier=_t)
            title.get_child_nodes()
            section = title.title_nodes.filter(identifier=_s)
            if section.exists():
                sections.append(section)

            worked_on[_t] = _s

        if not sections:
            return self.none()

        return reduce(merge, sections).distinct()[:settings.SEARCH_MAX_RESULTS]

    def search(self, title: str, section: str):
        """Search for a node"""
        return self.get_titles().get(
            identifier=title,
        ).search(section)

    def get_titles(self):
        """Get the titles"""
        titles = self.get_queryset().filter(parent__isnull=True)
        if not titles:

            with transaction.atomic():
                self.create_titles()
                titles = self.get_queryset().filter(parent__isnull=True)

        return titles

    def create_titles(self):
        """Create base titles for the CFR"""
        titles = get_cfr_titles()

        for title in titles:

            self.create(
                identifier=title['number'],
                label_description=title['name'],
                reserved=title['reserved'],
                up_to_date_as_of=title['up_to_date_as_of'],
                node_type='title',
                parent=None
            )


class CFRNode(models.Model):
    """A node in the CFR tree."""

    objects = CFRNodeManager()

    slug_id = models.SlugField(
        max_length=1024,
        unique=True,
        editable=False
    )

    up_to_date_as_of = models.CharField(max_length=20, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    identifier = models.CharField(max_length=225)
    label = models.CharField(max_length=1024)
    label_level = models.CharField(max_length=255)
    label_description = models.CharField(max_length=1024)
    reserved = models.BooleanField(default=False)
    volumes = models.CharField(max_length=1024, blank=True, null=True)

    descendant_range_start = models.CharField(max_length=1024, null=True)
    descendant_range_end = models.CharField(max_length=1024, null=True)

    node_type = models.CharField(max_length=20)

    parent: Type['CFRNode'] = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True)
    title_node: Type['CFRNode'] = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True,
        blank=True, related_name='title_nodes'
    )

    def __str__(self):
        return self.label_description

    def get_unique_id(self):
        """Get a unique id for the node"""
        return slugify(self.get_title())

    def get_collection_name(self):
        """Get the collection name"""
        return settings.CFR

    def search(self, section: str):
        """Search for a node"""

        if self.reserved:
            return None

        move_on = False

        # check if the desendant range contains the
        # section, then search the child
        if self.descendant_range_start and self.descendant_range_end:
            if float(
                self.descendant_range_start
            ) <= float(section) <= float(self.descendant_range_end):
                move_on = True
            else:
                return None


        if self.node_type == 'title' or move_on:

            for child in self.get_child_nodes():

                if child.has_children():
                    node = child.search(section)
                    if node is not None:
                        return node

                elif (
                    child.node_type == 'section'
                ) and (child.identifier == section):
                    return child

        return None

    class Meta:
        verbose_name = 'CFR Node'
        verbose_name_plural = "CFR Nodes"
        db_table = 'cfr_node'

    def html_link(self):
        pass

    def get_html_url(self):
        """Get the url to the html"""
        return str(reverse(f'{settings.CFR}:html', kwargs={
            'slug_id': self.slug_id
        }))


    def get_node_url(self):
        """Get the url to the node"""
        return str(reverse(f'{settings.CFR}:node', kwargs={
            'slug_id': self.slug_id
        }))

    def get_html_content(self):
        return mark_safe(
            get_cfr_html(
                self.title_node.identifier,
                self.title_node.up_to_date_as_of,
                self.node_type,
                self.identifier
            )
        )

    @cached_property
    def pdf_link(self):

        nodes_with_pdf = (
            'part',
            'subpart',
            'section',
            'appendix',
        )

        if self.node_type in nodes_with_pdf:
            title = self.title_node.identifier

            part = self.identifier
            if self.node_type == 'subpart':
                part = self.parent.identifier

            if self.node_type == 'appendix':
                part = part.split(' ')[-1]

            section_num = None

            if part.find('.') > -1:
                part, section_num = part.split('.')

            volume = self.volumes

            return get_cfr_pdf_link(
                title=title,
                part=part,
                section_num=section_num,
                volume=volume
            )

    def has_children(self):
        """Does this node have children?"""
        return self.node_type not in ('section', 'appendix')

    def has_html_paper(self):
        """Does this node have a paper version?"""
        return self.node_type in ('part', 'subpart', 'section', 'appendix')

    def get_title(self):
        if self.node_type == 'title':
            return self.label_description

        return self.label

    @property
    def children(self) -> models.query.QuerySet['CFRNode']:
        """Get the child nodes"""
        return self.cfrnode_set.all()

    def get_child_nodes(self) -> models.query.QuerySet['CFRNode']:
        """Get all the child nodes of the collection"""
        nodes = self.children

        if len(nodes) > 0:
            return nodes

        with transaction.atomic():
            # If there are no children, get the children from the API
            nodes = self.new_child_nodes()

        return nodes

    def get_json_data(self):
        return get_cfr_json(
            self.identifier,
            self.up_to_date_as_of
        )

    def create_nodes(
        self, nodes: dict, parent: Type["CFRNode"],
        title_node: Type["CFRNode"]
    ):
        """Create the nodes for the collection"""
        children = nodes.get('children', [])

        print("adding nodes")

        if nodes.get('type') != 'title':
            descendant_range = nodes.get('descendant_range')
            start, end = None, None

            if descendant_range:
                descendant_range = descendant_range.replace(
                    ' – ', '-').split('-')

                if len(descendant_range) == 2:
                    start, end = descendant_range
                else:
                    start = descendant_range[0]

            volumes = nodes.get('volumes')
            if volumes:
                volumes = volumes[0]

            identifier = nodes.get('identifier')

            if identifier is not None:
                parent = CFRNode(
                    identifier=nodes.get('identifier'),
                    label=nodes.get('label'),
                    label_level=nodes.get('label_level'),
                    label_description=nodes.get('label_description'),
                    reserved=nodes.get('reserved'),
                    node_type=nodes.get('type'),
                    volumes=volumes,
                    parent=parent,
                    title_node=title_node,
                    descendant_range_start=start,
                    descendant_range_end=end,
                )
                parent.save()
        else:
            # Update title
            parent.identifier = nodes.get('identifier')
            parent.label = nodes.get('label')
            parent.label_level = nodes.get('label_level')
            parent.label_description = nodes.get('label_description')
            parent.reserved = nodes.get('reserved')
            parent.save()


        if children:
            for child in children:
                self.create_nodes(child, parent, title_node)

    def new_child_nodes(self):
        """Get and create new child nodes"""

        if self.node_type == 'title':
            with transaction.atomic():
                data = self.get_json_data()

                if data:
                    # Create the child nodes
                    self.create_nodes(data, self, self)

                    # Return the child nodes
                    return self.children

        return CFRNode.objects.none()

    def get_absolute_url(self):
        """Get the url to the collection"""
        return reverse('collection', kwargs={'collection_code': self.code})

    def get_crumb(self):
        """Get single crumb"""
        return mark_safe(f"""
        <li class="breadcrumb-item">
            <a href='{self.get_node_url()}'>{self.get_title()}</a>
        </li>
        """)

    def get_bread_crumbs(self):
        """Get the breadcrumbs to get to this node"""

        parent = ''
        if self.parent is not None:
            parent = self.parent.get_bread_crumbs()

        return mark_safe("".join([
            parent,
            self.get_crumb()
        ]))


# Receiver to automatically create a
# unique slug_id for each node when it is created
@receiver(pre_save, sender=CFRNode)
def create_slug_id(sender, instance: CFRNode, **kwargs):
    if not instance.id:
        instance.slug_id = f"{instance.get_unique_id()}-{get_random_string(5)}"
