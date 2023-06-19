# flake8: noqa
from .base import *

ALLOWED_HOSTS = ["deeplegal.org", "www.deeplegal.org"]

STATIC_ROOT = BASE_DIR / "static"

PRINT_LOG = False
OFF_EMAIL = False

# Deployment security settings
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
