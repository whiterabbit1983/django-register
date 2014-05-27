from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.core.urlresolvers import reverse_lazy, reverse
from django.views.generic import View
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth import get_user_model
from .forms import EmailUserForm, ActivateUserForm
from .models import DEFAULT_KEY
from .mixins import UserEmailMixin, ActivateMixin

class NewUserView(UserEmailMixin, CreateView):
    model = get_user_model()
    form_class = EmailUserForm
    template_name = "register/new_user.html"
    success_url = reverse_lazy("activate_user")

class ActivateUserView(ActivateMixin, FormView):
    template_name = "register/activate_user.html"
    http_method_names = ["get", "post"]
    form_class = ActivateUserForm

    def get(self, request, *args, **kwargs):
        if not "activation_key" in request.GET:
            return super(ActivateUserView, self).get(request, *args, **kwargs)
        return self.render_result(request.GET)

    def post(self, request, *args, **kwargs):
        return self.render_result(request.POST)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_email"] = self.request.session.get("user_email", "")
        return context

    def get_success_url(self):
        return reverse("activation_complete")
