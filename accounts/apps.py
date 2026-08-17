from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "accounts"

    def ready(self) -> None:
        from django.db.models.signals import post_save
        from .models import User
        from .signals import post_save_account_receiver, social_login_creates_student

        post_save.connect(post_save_account_receiver, sender=User)

        from allauth.account.signals import user_signed_up

        user_signed_up.connect(social_login_creates_student)

        return super().ready()
