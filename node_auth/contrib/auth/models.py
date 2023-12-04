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

class AnonymousNode:
    id = None
    pk = None
    vsn = ""
    mac = ""

    def __str__(self):
        return "AnonymousNode"

    def __eq__(self, other):
        return isinstance(other, self.__class__)

    def __hash__(self):
        return 1  # instances always return the same hash value

    def __int__(self):
        raise TypeError(
            "Cannot cast AnonymousNode to int. Are you trying to use it in place of "
            "Node?"
        )

    def save(self):
        raise NotImplementedError(
            "Django doesn't provide a DB representation for AnonymousNode."
        )

    def delete(self):
        raise NotImplementedError(
            "Django doesn't provide a DB representation for AnonymousNode."
        )

    @property
    def is_anonymous(self):
        return True

    @property
    def is_authenticated(self):
        return False

    def get_vsn(self):
        return self.vsn