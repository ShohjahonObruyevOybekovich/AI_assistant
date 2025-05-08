from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model

from account.models import CustomUser

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = (
            "phone", "full_name", "language", "date_of_birth", "role",
            "balance", "chat_id", "bot_status", "is_blocked", "is_premium"
        )

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = (
            "phone", "full_name", "language", "date_of_birth", "role",
            "balance", "chat_id", "bot_status", "is_blocked", "is_premium",
            "last_active_at", "is_active", "is_staff", "is_superuser",
            "groups", "user_permissions"
        )