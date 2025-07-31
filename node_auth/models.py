import binascii
import os
from django.db import models
from django.utils.translation import gettext_lazy as _

class Token(models.Model):
    """
    Authorization token model.
    """
    key = models.CharField(_("Key"), max_length=40, primary_key=True)
    wg_pub_key = models.CharField(_("WireGuard Public Key"), max_length=44, blank=True, null=True)
    wg_priv_key = models.CharField(_("WireGuard Private Key"), max_length=44, blank=True, null=True)
    node = models.OneToOneField(
        "app.Node",
        related_name="auth_token",
        on_delete=models.CASCADE,
        verbose_name=_("node"),
    )
    created = models.DateTimeField(_("Created"), auto_now_add=True)

    def save(self, *args, **kwargs):
        from node_auth.utils import wireguard as wg

        creating = self._state.adding
        if not self.key:
            self.key = self.generate_key()

        if not wg.wg_enabled():
            priv, pub = wg.gen_keys()
            self.wg_priv_key = priv
            self.wg_pub_key = pub

        super().save(*args, **kwargs)

        if creating and not wg.wg_enabled():
            wg.create_peer(self.pk)

    def delete(self, *args, **kwargs):
        from node_auth.utils import wireguard as wg
        if not wg.wg_enabled():
            wg.delete_peer(self.pk)
        super().delete(*args, **kwargs)

    @classmethod
    def generate_key(cls):
        return binascii.hexlify(os.urandom(20)).decode()

    def __str__(self):
        return self.key
