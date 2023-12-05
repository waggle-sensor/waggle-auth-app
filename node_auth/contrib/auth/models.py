"""
Used django.contrib.auth.models as a Template
"""
from node_auth.contrib.auth.base_node import AbstractBaseNode
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db import models

class AbstractNode(AbstractBaseNode):
    """
    An abstract base class implementing a fully featured Node model.

    Vsn is required. Other fields are optional.
    """
    vsn = models.CharField("VSN", max_length=10, unique=True)
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this node should be treated as active. "
            "Unselect this instead of deleting nodes."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    REQUIRED_FIELDS = ["vsn"]
    VSN_FIELD = "vsn"

    class Meta:
        verbose_name = _("node")
        verbose_name_plural = _("nodes")
        abstract = True

    def __str__(self):
        return self.vsn

    def get_by_vsn(self, vsn):
        return self.get(vsn=vsn)