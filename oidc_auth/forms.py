from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class CreateUserForm(forms.Form):
    username = forms.CharField(max_length=255)
    confirm_username = forms.CharField(max_length=255)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        confirm_username = cleaned_data.get("confirm_username")
        if username != confirm_username:
            raise forms.ValidationError("usernames don't match")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("username already exists")
