from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class UpdateSSHPublicKeysForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["ssh_public_keys"]


class UpdateUsernameForm(forms.ModelForm):
    confirm_username = forms.CharField(max_length=255)

    class Meta:
        model = User
        fields = ["username", "confirm_username"]

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        confirm_username = cleaned_data.get("confirm_username")
        if username != confirm_username:
            raise forms.ValidationError("usernames don't match")
