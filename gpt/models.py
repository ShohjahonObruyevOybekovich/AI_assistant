from typing import TYPE_CHECKING

from django.db import models


from command.models import BaseModel

# Create your models here.

if TYPE_CHECKING:
    from account.models import CustomUser


class GptSession(BaseModel):

    user: "CustomUser" = models.ForeignKey(
        "account.CustomUser", on_delete=models.CASCADE, related_name="gpt_sessions"
    )

    messages: "models.QuerySet[GptMessage]"


class GptMessage(BaseModel):

    # session = models.ForeignKey(
    #     GptSession, on_delete=models.CASCADE, related_name="messages"
    # )

    content = models.TextField()

    role = models.CharField(
        choices=[
            ("SYSTEM", "Sistema"),
            ("USER", "Foydalanuvchi"),
            ("ASSISTANT", "Gpt"),
        ],
        max_length=255,
        default="USER",
    )
