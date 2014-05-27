from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils.translation import ugettext as _
from .models import EmailUser
from .forms import EmailUserForm

class UserCreationForm(EmailUserForm):
    class Meta(EmailUserForm.Meta):
        fields = ["email", "full_name", "is_active", "is_superuser"]

class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = EmailUser
        fields = ["email", "full_name", "password", "is_active", "is_superuser"]

    def clean_password(self):
        return self.initial["password"]

class EmailUserAdmin(UserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ("email", "full_name", "activation_key", "is_active", "is_superuser")
    list_filter = ("is_superuser",)
    fieldsets = (
        (None, {"fields": ("email", "password", "is_active")}),
        (_("Personal Info"), {"fields": ("full_name",)}),
        (_("Permissions"), {"fields": ("is_superuser",)}),
    )
    add_fieldsets = (
        (None,{
            "classes": ("wide",),
            "fields": ("email", "full_name", "password1", "password2", "is_active", "is_superuser")}
        ),
    )
    search_fields = ("email",)
    ordering = ("email",)
    filter_horizontal = ()

admin.site.register(EmailUser, EmailUserAdmin)
admin.site.unregister(Group)