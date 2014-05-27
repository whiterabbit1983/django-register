from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from .signals import user_activated

class UserEmailMixin:
    def form_valid(self, form):
        self.request.session["user_email"] = form.cleaned_data["email"]
        return super(UserEmailMixin, self).form_valid(form)

class ActivateMixin:
    def render_result(self, ctx):
        key = ctx.get("activation_key", "")
        user = self.activate(key)
        if not user:
            return redirect(reverse("activation_error"))
        return redirect(reverse("activation_complete"))

    def activate(self, key):
        user_model = get_user_model()
        user = user_model.objects.activate(key)
        if user:
            user_activated.send(sender=get_user_model(), user=user)

        return user
