
from django import template
from Main.models import PlaceholderInput
from random import choice

register = template.Library()


@register.simple_tag()
def get_random_placeholder():
    """Get a random placeholder"""
    qset = PlaceholderInput.objects.all()
    default = "Enter a source name, citation, or terms."
    if qset.count() == 0:
        return default
    return choice(qset).name
