import json
import logging

from django.conf import settings
import requests

# Create the logger and set the logging level
logger = logging.getLogger('basic')
err_logger = logging.getLogger('basic.error')


def invalid_str(value):
    # This checks if a string contains special chars or not
    for i in '@#$%^&*+=://;?><}{[]()':
        if i in value:
            return True
    return False


def choices_to_dict(dicts=None):
    if dicts is None:
        dicts = {}

    return [{'value': a[0], 'name':a[1]} for a in dicts]


# Print that only works when on
def printt(*args, **kwargs):
    if settings.PRINT_LOG:
        return print(*args, **kwargs)


def send_email(email, subject, message, fail=True):
    """
    Send mail function
    """

    if settings.PRINT_LOG:
        print(message)

    if settings.OFF_EMAIL:
        return True

    try:
        headers = {
            'Authorization': f'Bearer {settings.SENDGRID_KEY}'
        }

        data = {
            "personalizations": [{"to": [{"email": email}]}],
            "from": {"email": settings.SENDGRID_EMAIL},
            "subject": subject,
            "content": [{"type": "text/html", "value": message}]}

        requests.post(
            url='https://api.sendgrid.com/v3/mail/send',
            json=data, headers=headers)

        return True

    except Exception:
        pass

    return False


# Code to remover session if it exists
def remove_session(request, name):
    session = request.session.get(name, None)
    if session is not None:
        del request.session[name]


# Code to convert tuple that looks like a dict to a list of python dictionary
def tup_to_dict(tup: tuple) -> dict:
    jsonObj = []

    for key, value in tup:
        obj = dict()
        obj['key'] = key
        obj['value'] = value
        jsonObj.append(obj)

    return json.dumps(jsonObj)
