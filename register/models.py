from django.db import models
from django.conf import settings
from django.dispatch import receiver
from django.template import Context, loader
from django.core.mail import send_mail
from django.utils.translation import ugettext as _
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
import os, sys, hashlib, binascii, re
from .signals import user_registered

DEFAULT_KEY = "USER_ACTIVATED"
PY34 = (sys.version_info >= (3,4))

class EmailUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("User must have an email address"))

        user = self.model(
            email=self.normalize_email(email),
            **extra_fields
            )
        user.set_password(password)
        if not "is_active" in extra_fields.keys():
            user.is_active = False
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        user = self.create_user(email, password, **extra_fields)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save(using=self._db)
        return user

    def activate(self, key):
        key_search_re = re.compile("^[a-fA-F0-9]{64}$")
        if key_search_re.search(key):
            try:
                user = self.get(activation_key=key)
            except self.model.DoesNotExist:
                return False
            user.is_active = True
            user.activation_key = DEFAULT_KEY
            user.save()
            return user
        return False

class EmailUser(AbstractBaseUser):
    email = models.EmailField(max_length=254, unique=True)
    full_name = models.CharField(max_length=1000)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    activation_key = models.CharField(max_length=64)

    objects = EmailUserManager()

    USERNAME_FIELD = "email"

    def get_short_name(self):
        return self.email

    def get_full_name(self):
        return self.full_name

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    def gen_activation_key(self):
        salt = os.urandom(16)
        if PY34:
            k = hashlib.pbkdf2_hmac(
                "sha256",
                bytes(self.email, "utf-8"),
                salt,
                100000)
            key = binascii.hexlify(k).decode("utf-8")
        else:
            s = "{}{}".format(self.email, salt.decode(errors="ignore"))
            key = hashlib.sha256(bytes(s, "utf-8")).hexdigest()
        return key

@receiver(post_save, sender=EmailUser)
def send_confirmation_email(sender, **kwargs):
    user = kwargs["instance"]
    recpt = user.email
    activation_key = user.activation_key
    msg_template = loader.get_template("register/activation_email.txt")
    ctx = Context({"activation_key": activation_key})
    msg_body = msg_template.render(ctx)
    subject = getattr(settings, "REGISTER_ACTIVATION_SUBJECT", _("Activation code"))
    from_email = getattr(settings, "REGISTER_FROM_EMAIL", "noreply@example.com")
    user_registered.send(sender=EmailUser, user=user)
    send_mail(
        subject,
        msg_body,
        from_email,
        [recpt],
        fail_silently=True)
