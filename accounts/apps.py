from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # Signals import (agar signals.py banana ho to yahan import karna)
        # import accounts.signals
        pass
