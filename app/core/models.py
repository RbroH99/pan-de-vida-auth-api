from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)

from .rabbitmq import send_user_notification

import asyncio


class UserManager(BaseUserManager):
    """Manager for the users."""

    def create_user(self, email, password=None, **extra_fields):
        """Create, save and return a new user."""
        if not email:
            raise ValueError('User must have an email!.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        user_info = {
            "id": user.id,
            "email": email
        }
        asyncio.run(send_user_notification('user_created', user_info))

        return user

    def create_superuser(self, email, password, name):
        """Create superuser with given details."""
        user = self.model(email=email, name=name)

        user.is_superuser = True
        user.is_staff = True
        user.set_password(password)
        user.save(using=self._db)

        user_info = {
            "id": user.id,
            "email": user.email,
            "is_superuser": True,
            "password": user.password
        }
        asyncio.run(send_user_notification('user_created', user_info))

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User in the system."""
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    def __str__(self):
        """Returns the user string representation."""
        return self.email


@receiver(post_save, sender=User)
def notify_password_changed(sender, instance, created, **kwargs):
    if not created:
        user_info = {
            'id': instance.id,
            'email': instance.email,
            'password': instance.password,
        }
        asyncio.run(send_user_notification('user_modified', user_info))
