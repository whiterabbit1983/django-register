from django.test import TestCase, RequestFactory
from django.core import mail
from django.db import IntegrityError
from django.forms import ValidationError
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from register.models import EmailUser, DEFAULT_KEY
from register.forms import EmailUserForm, ActivateUserForm
from register.mixins import ActivateMixin
from register.views import ActivateUserView
from register.signals import user_registered, user_activated
import re

class EmailUserModelTest(TestCase):
    def test_user_not_active_by_default(self):
        user = EmailUser.objects.create_user("mail@example.com")
        self.assertFalse(user.is_active)

    def test_superuser_active_by_default(self):
        user = EmailUser.objects.create_superuser("supermail@example.com", "secret")
        self.assertTrue(user.is_active)

    def test_user_not_su_by_default(self):
        user = EmailUser.objects.create_user("mail@example.com")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_user_password(self):
        user = EmailUser.objects.create_user("mail@example.com", password="secret")
        self.assertTrue(user.check_password("secret"))

    def test_user_short_name(self):
        user = EmailUser.objects.create_user("mail@example.com", password="secret")
        self.assertEqual(user.get_short_name(), "mail@example.com")

    def test_user_full_name(self):
        user = EmailUser.objects.create_user("mail@example.com", password="secret", full_name="New User")
        self.assertEqual(user.get_full_name(), "New User")

    def test_user_to_string(self):
        user = EmailUser.objects.create_user("mail@example.com", password="secret")
        self.assertEqual(str(user), "mail@example.com")

    def test_user_must_have_email_1(self):
        with self.assertRaises(ValueError):
            user = EmailUser.objects.create_user("")

    def test_user_must_have_email_2(self):
        with self.assertRaises(ValueError):
            user = EmailUser.objects.create_user(None)

    def test_superuser_must_have_email_1(self):
        with self.assertRaises(ValueError):
            user = EmailUser.objects.create_superuser("", "secret")

    def test_superuser_must_have_email_2(self):
        with self.assertRaises(ValueError):
            user = EmailUser.objects.create_superuser(None, "secret")

    def test_superuser_must_have_password(self):
        with self.assertRaises(TypeError):
            EmailUser.objects.create_superuser("supermail@example.com")

    def test_superuser_is_staff_and_su(self):
        su = EmailUser.objects.create_superuser(
            "supermail@example.com",
            "supersecret"
            )
        self.assertTrue(su.is_staff)
        self.assertTrue(su.is_superuser)

    def test_user_email_is_unique(self):
        EmailUser.objects.create_user("mail@example.com")
        with self.assertRaises(IntegrityError):
            EmailUser.objects.create_user("mail@example.com")

    def test_superuser_email_is_unique(self):
        EmailUser.objects.create_superuser(
            "supermail@example.com",
            "supersecret"
            )
        with self.assertRaises(IntegrityError):
            EmailUser.objects.create_superuser(
                "supermail@example.com",
                "supersecret"
                )

    def test_user_activate(self):
        user = EmailUser.objects.create_user("mail@example.com", activation_key="1"*64)
        EmailUser.objects.activate("1"*64)
        user = EmailUser.objects.get(email="mail@example.com")
        self.assertTrue(user.is_active)
        self.assertEqual(user.activation_key, DEFAULT_KEY)

    def test_user_gen_correct_key(self):
        user = EmailUser.objects.create_user("mail@example.com")
        import re
        self.assertTrue(re.match("^[a-fA-F0-9]{64}$", user.gen_activation_key()))

class EmailUserFormTest(TestCase):
    def test_form_shown_fields(self):
        f = EmailUserForm()
        self.assertEqual(
            set(f.fields),
            set({"email", "full_name", "password1", "password2"}))

    def test_form_empty_is_not_valid(self):
        f = EmailUserForm()
        self.assertFalse(f.is_valid())

    def test_form_required_fields(self):
        f = EmailUserForm()
        self.assertTrue(f.fields["email"].required)
        self.assertTrue(f.fields["full_name"].required)
        self.assertTrue(f.fields["password1"].required)
        self.assertTrue(f.fields["password2"].required)

    def test_form_email_is_not_valid(self):
        data = {
        "email": "wrong email",
        "full_name": "full name",
        "password1": "secret",
        "password2": "secret",
        }
        f = EmailUserForm(data)
        self.assertFalse(f.is_valid())

    def test_form_full_name_is_not_set(self):
        data = {
        "email": "user@mail.com",
        "password1": "secret",
        "password2": "secret",
        }
        f = EmailUserForm(data)
        self.assertFalse(f.is_valid())

    def test_form_password_mismatch(self):
        data = {
        "email": "user@mail.com",
        "full_name": "full name",
        "password1": "secret",
        "password2": "wrong",
        }
        f = EmailUserForm(data)
        self.assertFalse(f.is_valid())

    def test_form_errors_password_mismatch(self):
        data = {
        "email": "user@mail.com",
        "full_name": "full name",
        "password1": "secret",
        "password2": "wrong",
        }
        f = EmailUserForm(data)
        self.assertFalse(f.is_valid())
        self.assertIn("Passwords mismatch", f.non_field_errors())

    def test_form_is_completely_valid(self):
        data = {
        "email": "user@mail.com",
        "full_name": "full name",
        "password1": "secret",
        "password2": "secret",
        }
        f = EmailUserForm(data)
        self.assertTrue(f.is_valid())

    def test_form_user_password(self):
        data = {
        "email": "user@mail.com",
        "full_name": "full name",
        "password1": "secret",
        "password2": "secret",
        }
        f = EmailUserForm(data)
        user = f.save()
        self.assertTrue(user.check_password("secret"))

    def test_form_user_short_name(self):
        data = {
        "email": "user@mail.com",
        "full_name": "full name",
        "password1": "secret",
        "password2": "secret",
        }
        f = EmailUserForm(data)
        user = f.save()
        self.assertEqual(user.get_short_name(), "user@mail.com")

    def test_form_user_full_name(self):
        data = {
        "email": "user@mail.com",
        "full_name": "full name",
        "password1": "secret",
        "password2": "secret",
        }
        f = EmailUserForm(data)
        user = f.save()
        self.assertEqual(user.get_full_name(), "full name")

    def test_form_user_to_string(self):
        data = {
        "email": "user@mail.com",
        "full_name": "full name",
        "password1": "secret",
        "password2": "secret",
        }
        f = EmailUserForm(data)
        user = f.save()
        self.assertEqual(str(user), "user@mail.com")

class ActivateUserFormTest(TestCase):
    def test_form_key_is_required(self):
        f = ActivateUserForm()
        self.assertFalse(f.is_valid())

    def test_form_empty_key(self):
        data = {"activation_key": ""}
        f = ActivateUserForm(data)
        self.assertFalse(f.is_valid())

    def test_form_wrong_activation_key_symbols(self):
        data = {"activation_key": "a1"*16 + "-"*32}
        f = ActivateUserForm(data)
        self.assertFalse(f.is_valid())

    def test_form_wrong_activation_key_letters(self):
        data = {"activation_key": "a1"*16 + "g"*32}
        f = ActivateUserForm(data)
        self.assertFalse(f.is_valid())

    def test_form_is_valid(self):
        user = EmailUser()
        data = {"activation_key": user.gen_activation_key()}
        f = ActivateUserForm(data)
        self.assertTrue(f.is_valid())

class RegisterViewsTest(TestCase):
    urls = "register.urls"

    def setup_view(self, view, request, *args, **kwargs):
        view.request = request
        view.args = args
        view.kwargs = kwargs
        return view

    def test_activate_form_ok_if_no_email(self):
        resp = self.client.get(reverse("activate_user"), follow=True)
        self.assertEqual(resp.status_code, 200)

    def test_activation_form_display_context(self):
        request = RequestFactory().get(reverse("activate_user"), follow=True)
        request.session = dict()
        request.session["user_email"] = "user@mail.com"
        view = ActivateUserView()
        form = ActivateUserForm()
        view = self.setup_view(view, request, form=form)
        context = view.get_context_data()
        #self.assertTrue(isinstance(context["form"], ActivateUserForm))
        self.assertEqual(context["user_email"], "user@mail.com")

    def test_activation_form_display_get_success_url(self):
        request = RequestFactory().get(reverse("activate_user"), follow=True)
        view = ActivateUserView()
        view = self.setup_view(view, request)
        url = view.get_success_url()
        self.assertEqual(url, reverse("activation_complete"))

    def test_new_user_view_get_status_ok(self):
        response = self.client.get(reverse("register_new"), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_new_user_view_post_status_ok(self):
        response = self.client.post(
            reverse("register_new"),
            {
            "email": "user@mail.com",
            "full_name": "user name",
            "password1": "secret",
            "password2": "secret",
            },
            follow=True)
        self.assertEqual(response.status_code, 200)

    def test_new_user_send_mail(self):
        response = self.client.post(
            reverse("register_new"),
            {
            "email": "user@mail.com",
            "full_name": "user name",
            "password1": "secret",
            "password2": "secret",
            },
            follow=True)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Activation code")

    def test_new_user_session_has_user_email(self):
        self.client.post(
            reverse("register_new"),
            {
            "email": "user@mail.com",
            "full_name": "user name",
            "password1": "secret",
            "password2": "secret",
            },
            follow=True)
        self.assertIn("user_email", self.client.session.keys())

    def test_new_user_session_user_email_is_valid(self):
        self.client.post(
            reverse("register_new"),
            {
            "email": "user@mail.com",
            "full_name": "user name",
            "password1": "secret",
            "password2": "secret",
            },
            follow=True)
        self.assertEqual(self.client.session["user_email"], "user@mail.com")

    def test_activation_get_wrong_key_status_code_ok(self):
        key = "1"*64
        url = "{}?activation_key={}".format(reverse("activate_user"), key)
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_activation_post_wrong_key_status_code_ok(self):
        key = "1"*64
        url = reverse("activate_user")
        response = self.client.post(url, {"activation_key": key}, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_activation_get_wrong_key_error_template(self):
        key = "1"*64
        url = "{}?activation_key={}".format(reverse("activate_user"), key)
        response = self.client.get(url, follow=True)
        self.assertContains(response, "does not exist or already activated")

    def test_activation_post_wrong_key_error_template(self):
        key = "1"*64
        url = reverse("activate_user")
        response = self.client.post(url, {"activation_key": key}, follow=True)
        self.assertContains(response, "does not exist or already activated")

    def test_activation_get_right_key_status_code_ok(self):
        self.client.post(
            reverse("register_new"),
            {
            "email": "user@mail.com",
            "full_name": "user name",
            "password1": "secret",
            "password2": "secret",
            },
            follow=True
            )
        user = EmailUser.objects.get(email="user@mail.com")
        key = user.activation_key
        url = "{}?activation_key={}".format(reverse("activate_user"), key)
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_activation_post_right_key_status_code_ok(self):
        self.client.post(
            reverse("register_new"),
            {
            "email": "user@mail.com",
            "full_name": "user name",
            "password1": "secret",
            "password2": "secret",
            },
            follow=True
            )
        user = EmailUser.objects.get(email="user@mail.com")
        key = user.activation_key
        url = reverse("activate_user")
        response = self.client.post(url, {"activation_key": key},follow=True)
        self.assertEqual(response.status_code, 200)

    def test_activation_get_right_key_show_complete_message(self):
        self.client.post(
            reverse("register_new"),
            {
            "email": "user@mail.com",
            "full_name": "user name",
            "password1": "secret",
            "password2": "secret",
            },
            follow=True
            )
        user = EmailUser.objects.get(email="user@mail.com")
        key = user.activation_key
        url = "{}?activation_key={}".format(reverse("activate_user"), key)
        response = self.client.get(url, follow=True)
        self.assertContains(response, "Activation complete")

    def test_activation_post_right_key_show_complete_message(self):
        self.client.post(
            reverse("register_new"),
            {
            "email": "user@mail.com",
            "full_name": "user name",
            "password1": "secret",
            "password2": "secret",
            },
            follow=True
            )
        user = EmailUser.objects.get(email="user@mail.com")
        key = user.activation_key
        url = reverse("activate_user")
        response = self.client.post(url, {"activation_key": key},follow=True)
        self.assertContains(response, "Activation complete")

class SignalTest(TestCase):
    def test_user_registered_signal(self):
        def handler(sender, user, **kwargs):
            self.user = user

        user_registered.connect(handler, sender=get_user_model())
        self.client.post(
            reverse("register_new"),
            {
            "email": "user@mail.com",
            "full_name": "user name",
            "password1": "secret",
            "password2": "secret",
            },
            follow=True
            )
        self.assertEqual(self.user.email, "user@mail.com")
        self.assertEqual(self.user.full_name, "user name")
        self.assertTrue(self.user.check_password("secret"))
        key_re = re.compile("^[a-fA-F0-9]{64}$")
        self.assertTrue(key_re.search(self.user.activation_key))

    def test_user_activated_signal(self):
        def handler(sender, user, **kwargs):
            self.user = user
            
        user_activated.connect(handler, sender=get_user_model())
        self.client.post(
            reverse("register_new"),
            {
            "email": "user@mail.com",
            "full_name": "user name",
            "password1": "secret",
            "password2": "secret",
            },
            follow=True
            )
        user = EmailUser.objects.get(email="user@mail.com")
        key = user.activation_key
        url = reverse("activate_user")
        response = self.client.post(url, {"activation_key": key},follow=True)
        self.assertEqual(self.user.email, "user@mail.com")
        self.assertEqual(self.user.full_name, "user name")
        self.assertTrue(self.user.check_password("secret"))
        self.assertEqual(self.user.activation_key, DEFAULT_KEY)