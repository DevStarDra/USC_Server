from django.http import Http404
from django.shortcuts import redirect
from django.views import generic
from django.contrib import messages
from django.conf import settings

from .models import Collection, Node
from .forms import SearchForm


class CollectionView(generic.DetailView):
    model = Collection
    template_name = 'Data/collection.html'
    slug_field: str = 'code'
    slug_url_kwarg: str = 'collection_code'

    object: Collection

    def get_object(self, queryset=None):
        queryset = Collection.objects.all()
        return queryset.get(code=settings.USCODE)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nodes'] = self.object.get_child_nodes()
        return context


class NodeView(generic.DetailView):
    model = Node
    template_name = 'Data/node.html'
    slug_field: str = 'slug_id'
    slug_url_kwarg: str = 'slug_id'

    object: Node

    def search_node(self, title: int, section: str) -> Node:
        """Search for a node in collection tree by title and section"""
        return self.object.search(title, section)

    def get(self, request, *args, **kwargs):
        """Handle GET requests: instantiate a blank version of the form."""
        self.object = self.get_object()


        search = request.GET.get('search')
        form = None
        if search:
            form = SearchForm(request.GET)
            form.node = self.object
            if form.is_valid():
                title = form.cleaned_data['title']
                section = form.cleaned_data['section']
                node = self.search_node(title, section)

                if node:
                    return redirect(node.get_view_document_link())

                messages.warning(
                    request, "Resource with title and section not found")

        context = self.get_context_data(object=self.object)
        context['form'] = form
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nodes'] = self.object.get_child_nodes()
        return context


class LeafView(NodeView):
    template_name: str = 'Data/leaf.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title, css, html = self.object.get_document()
        context["title"] = title
        context["css"] = css
        context["html"] = html

        return context

    def get(self, request, *args, **kwargs):
        """Check if the node is a leaf"""
        node = self.get_object()
        if not node.htmlfile:
            raise Http404("Resource not found")
        return super().get(request, *args, **kwargs)
