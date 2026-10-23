import re

from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

USERNAME_RE = re.compile(r"^[a-z][a-z0-9]{2,}$")


class UpdateSSHPublicKeysForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["ssh_public_keys"]
        widgets = {
            "ssh_public_keys": forms.Textarea(attrs={"cols": 80, "rows": 10}),
        }


class CompleteLoginForm(forms.Form):
    username = forms.CharField(max_length=30)
    confirm_username = forms.CharField(max_length=30)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        confirm_username = cleaned_data.get("confirm_username")
        if username != confirm_username:
            raise forms.ValidationError("usernames don't match")
        if username and not USERNAME_RE.match(username):
            raise forms.ValidationError(
                "usernames must start with a letter and can only contain "
                "lowercase letters and numbers"
            )
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("username already exists")
