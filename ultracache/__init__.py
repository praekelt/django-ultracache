from django.conf import settings


SETTINGS = {}
try:
    SETTINGS.update(settings.ULTRACACHE)
except AttributeError:
    # No overrides
    pass
