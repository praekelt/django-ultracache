from django.apps import AppConfig


class UltracacheAppConfig(AppConfig):
    name = "ultracache"
    verbose_name = "Ultracache"

    def ready(self):
        from ultracache import signals
