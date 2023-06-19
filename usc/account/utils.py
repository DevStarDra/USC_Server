from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from .tokens import account_token


def verification_message(request: HttpRequest, user, template):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_token.make_token(user)

    message = compose_email(
        request,
        template,
        {
            'user': user,
            'uid': uid,
            'token': token,
            'name': user.profile.get_fullname,
        }
    )
    return message


def compose_email(request: HttpRequest, template: str, context: dict):
    site = get_current_site(request)

    protocol = 'http'
    if request.is_secure():
        protocol = 'https'

    context.update({
        'domain': site.domain,
        'from': settings.DEFAULT_FROM_EMAIL,
        'app_name': settings.APP_NAME,
        'protocol': protocol,
    })

    message = render_to_string(template, context)
    return message
