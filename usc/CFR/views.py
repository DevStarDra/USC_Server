from django.shortcuts import redirect
from django.views import generic
from django.contrib import messages

from .models import CFRNode
from .forms import SearchForm



class SearchMixin(generic.DetailView):
    def get(self, request, *args, **kwargs):
        """Handle GET requests: instantiate a blank version of the form."""
        search = request.GET.get('search')
        form = None
        if search:
            form = SearchForm(request.GET)
            if form.is_valid():
                title = form.cleaned_data['title']
                section = form.cleaned_data['section']
                node = CFRNode.objects.search(title, section)

                if node:
                    return redirect(node.get_html_url())

                messages.warning(
                    request, "CFR document with title and section not found")

        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)


class CollectionView(SearchMixin):
    model = CFRNode
    template_name = 'CFR/node.html'
    slug_field: str = 'code'
    slug_url_kwarg: str = 'collection_code'

    object: CFRNode

    def get_object(self, queryset=None):
        return None

    def get_queryset(self):
        return CFRNode.objects.get_titles()

    def get_context_data(self, **kwargs):
        self.object = None
        context = super().get_context_data(**kwargs)
        context['nodes'] = self.get_queryset()
        return context


class NodeView(SearchMixin):
    model = CFRNode
    template_name = 'CFR/node.html'
    slug_field: str = 'slug_id'
    slug_url_kwarg: str = 'slug_id'

    object: CFRNode

    def search_node(self, title: int, section: str) -> CFRNode:
        """Search for a node in collection tree by title and section"""
        return self.object.search(title, section)

    def get_context_data(self, **kwargs):
        self.object = self.get_object(self.get_queryset())
        context = super().get_context_data(**kwargs)
        context['nodes'] = self.object.get_child_nodes()
        return context


class Content(NodeView):
    template_name: str = 'CFR/content.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["html"] = self.object.get_html_content()
        return context
