from django.conf import settings


# Ensure request context processor is active. Handle all styles of the setting.
try:
    tcp = settings.TEMPLATES[0]["OPTIONS"]["context_processors"]
except (AttributeError, KeyError):
    try:
        tcp = settings.TEMPLATE_CONTEXT_PROCESSORS
    except AttributeError:
        tcp = []

if ("django.core.context_processors.request" not in tcp) \
    and ("django.template.context_processors.request" not in tcp):
    raise RuntimeError(
        "django.template.context_processors.request is required"
    )

import ultracache.monkey
