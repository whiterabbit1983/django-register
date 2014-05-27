from django.conf.urls import patterns, url
from django.views.generic import TemplateView
from .views import NewUserView, ActivateUserView

urlpatterns = patterns('',
    url(r'^new/$', NewUserView.as_view(), name='register_new'),
    url(r'^activate/', ActivateUserView.as_view(), name='activate_user'),
    url(r'^activated/', TemplateView.as_view(
        template_name="register/activation_complete.html"
        ), name='activation_complete'),
    url(r'^error/$', TemplateView.as_view(
        template_name="register/activation_error.html"
        ), name='activation_error'),
)
