from django import forms
from .models import CFRNode


class SearchForm(forms.Form):
    """Form for searching"""
    title = forms.IntegerField(min_value=1)
    section = forms.CharField(max_length=100)

    def clean_title(self):
        title = self.cleaned_data['title']

        max_length = CFRNode.objects.get_titles().count()
        if title > max_length:
            raise forms.ValidationError(
                f"Title is too big. Max value is {max_length}")

        return title

    def clean_section(self):
        section: str = self.cleaned_data['section']

        # Section can only have numbers and dots
        if not section.replace('.', '', 1).isdigit():
            raise forms.ValidationError("Section is not valid")

        return section