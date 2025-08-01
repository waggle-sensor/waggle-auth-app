from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from node_auth.utils import wireguard as wg
from node_auth.models import Token

@receiver(pre_delete, sender=Token)
def handle_token_pre_delete(sender, instance, **kwargs):
    """
    Handle pre-delete signal for Token model to remove WireGuard peer.
    """
    if wg.wg_enabled():
        wg.delete_peer(instance.key)

@receiver(post_save, sender=Token)
def handle_token_post_save(sender, instance, created, **kwargs):
    """
    Handle post-save signal for Token model to generate WireGuard keys and create peer if necessary.
    """
    if wg.wg_enabled() and (not instance.wg_pub_key or not instance.wg_priv_key):
        priv, pub = wg.gen_keys()
        instance.wg_priv_key = priv
        instance.wg_pub_key = pub
        instance.save(update_fields=['wg_priv_key', 'wg_pub_key'])
        wg.create_peer(instance.key)