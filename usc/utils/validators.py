import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from utils.data import get_collection_name
from utils.general import invalid_str


def validate_special_char(value):
    if invalid_str(value):
        raise ValidationError(
            _('%(value)s contains special characters'),
            params={'value': value},
        )


def validate_digits(value: str):
    if not value.isdigit():
        raise ValidationError(
            message="Invalid input provided",
        )


def validate_phone(phone=''):
    pattern = r'^\+(?:[0-9] ?){6,14}[0-9]$'
    s = re.match(pattern, phone)
    if s is not None:
        return True


def validate_collection_code(code: str):
    name = get_collection_name(code.upper())
    if name is None:
        raise ValidationError("Invalid collection code")
