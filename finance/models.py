from typing import TYPE_CHECKING

from django.db import models

from django.contrib import admin

from command.models import BaseModel

if TYPE_CHECKING:
    from account.models import CustomUser

# Create your models here.


class FinanceAction(BaseModel):

    user: "CustomUser" = models.ForeignKey(
        "account.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="finance_actions",
    )

    reason = models.CharField(max_length=255)

    action = models.CharField(
        choices=[
            ("INCOME", "Kirim"),
            ("EXPENSE", "Chiqim"),
        ],
        max_length=255,
    )
    currency = models.CharField(
        max_length=10,null=True,blank=True,
    )

    amount = models.IntegerField()

    draft = models.BooleanField(default=False)
    date = models.DateField(null=True,blank=True)
    time = models.TimeField(null=True,blank=True)
