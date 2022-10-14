from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class UpdateSSHPublicKeysForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["ssh_public_keys"]
