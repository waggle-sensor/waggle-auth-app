from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.core.management import call_command

@receiver(post_migrate)
def run_collectstatic(sender, **kwargs):
    """Run collectstatic if it's the first migration"""
    
    if kwargs.get('app') and kwargs.get('created_models'):
        call_command('collectstatic', interactive=False)
