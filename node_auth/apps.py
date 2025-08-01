from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AuthTokenConfig(AppConfig):
    name = "node_auth"  # used rest_framework.authtoken as template
    verbose_name = _("Node Auth Token")

    def ready(self):
        import node_auth.signals