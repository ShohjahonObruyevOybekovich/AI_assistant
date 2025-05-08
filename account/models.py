from decimal import Decimal
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from account.managers import UserManager



class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    full_name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=255, unique=True, blank=True, null=True)
    chat_id = models.CharField(max_length=255, blank=True, null=True)

    # photo : 'File' = models.ForeignKey('upload.File', on_delete=models.SET_NULL, blank=True, null=True)

    language = models.CharField(choices=[
        ('en', 'English'),
        ('uz', 'Uzbek'),
        ("ru", "Russian"),
    ],max_length=10, blank=True, null=True)

    date_of_birth = models.DateField(blank=True, null=True)

    ROLE_CHOICES = (
        ("User", "User"),
        ("Admin", "Admin"),
    )

    role = models.CharField(choices=ROLE_CHOICES, max_length=30, default="User")

    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    is_blocked = models.BooleanField(default=False)

    is_deleted = models.BooleanField(default=False)

    BOT_STATUS_CHOICES = (
        ("active", "Active"),
        ("blocked", "Blocked"),
        ("deleted", "Deleted"),
        ("banned", "Banned"),
    )
    bot_status = models.CharField(choices=BOT_STATUS_CHOICES, max_length=10, default="active")

    last_active_at = models.DateTimeField(null=True, blank=True)

    is_premium = models.BooleanField(default=False)

    USERNAME_FIELD = 'phone'
    # REQUIRED_FIELDS = ['phone']

    objects = UserManager()

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return self.full_name or self.phone


