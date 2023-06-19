from django import forms
from .models import Node


class SearchForm(forms.Form):
    """Form for searching"""
    title = forms.IntegerField(min_value=1)
    section = forms.CharField(max_length=100)

    node: Node = None

    def clean_title(self):
        title = self.cleaned_data['title']

        if not self.node:
            raise forms.ValidationError("Node is not set")

        max_length = self.node.get_root_node().get_child_nodes().count()
        if title > max_length:
            raise forms.ValidationError(
                f"Title is too big. Max value is {max_length}")

        return title

    def clean_section(self):
        section: str = self.cleaned_data['section']

        # Section can only have letters, numbers and dashes
        def is_valid(s: str):
            return s.isalnum() or s == '-'

        for char in section:
            if not is_valid(char):
                raise forms.ValidationError(
                    "Section can only have letters, numbers and dashes")

        return section
