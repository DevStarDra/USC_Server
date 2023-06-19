from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six
from typing import Optional
from django.contrib.auth.models import AbstractBaseUser
from .models import UsedResetToken


class EmailConfirmationToken(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) +
            six.text_type(timestamp) +
            six.text_type(user.active)
        )

    def mark_used(self, user: AbstractBaseUser, token: str):
        UsedResetToken.objects.create(user=user, token=token)

    def check_token(
        self, user: Optional[AbstractBaseUser],
        token: Optional[str]
    ) -> bool:
        valid = super().check_token(user, token)
        if valid:
            qset = UsedResetToken.objects.filter(
                user=user, token=token
            )
            if qset.exists():
                return False
        return valid


account_token = EmailConfirmationToken()
