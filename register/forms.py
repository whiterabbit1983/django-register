from django import forms
from django.utils.translation import ugettext as _
from .models import EmailUser
import re

class EmailUserForm(forms.ModelForm):
    password1 = forms.CharField(
        label=_("Password"),
        max_length=255,
        required=True,
        widget=forms.PasswordInput)
    password2 = forms.CharField(
        label=_("Password confirmation"),
        max_length=255,
        required=True,
        widget=forms.PasswordInput)

    class Meta:
        model = EmailUser
        fields = ["email", "full_name"]

    def clean(self):
        cleaned_data = super(EmailUserForm, self).clean()
        p1 = cleaned_data.get("password1", "")
        p2 = cleaned_data.get("password2", "")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError(_("Passwords mismatch"))
        cleaned_data["password"] = p2
        return cleaned_data

    def save(self, commit=True):
        user = super(EmailUserForm, self).save(commit=False)
        user.activation_key = user.gen_activation_key()
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class ActivateUserForm(forms.Form):
    activation_key = forms.CharField(max_length=64, required=True)

    def clean_activation_key(self):
        k = self.cleaned_data["activation_key"]
        if not re.match("^[a-fA-F0-9]{64}$", k):
            raise forms.ValidationError(_("Activation code has wrong format"))
        return k

    def clean(self):
        cleaned_data = super(ActivateUserForm, self).clean()
        k = cleaned_data.get("activation_key", "")
        if not k:
            raise forms.ValidationError(_("Activation code required"))
        return cleaned_data
