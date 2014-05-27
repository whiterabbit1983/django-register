from django.dispatch import Signal

user_registered = Signal(providing_args=["user"])

user_activated = Signal(providing_args=["user"])