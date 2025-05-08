from decimal import Decimal
from django.db import models
from account.models import CustomUser


class ActionType(models.TextChoices):
    GIVE = "give", "Give Money"
    BORROW = "borrow", "Borrow Money"
    SPEND = "spend", "Spend Money"
    RECEIVE = "receive", "Receive Income"
    REMIND = "remind", "Set Reminder"
    TRANSFER = "transfer", "Transfer Money"
    PLAN = "plan", "Plan Expense"


class FinanceAction(models.Model):
    """
    A financial action representing any money-related intent from the user.
    """

    user: CustomUser = models.ForeignKey(
        "account.CustomUser",
        on_delete=models.CASCADE,
        related_name="finance_actions"
    )
    action_type: str = models.CharField(
        max_length=20,
        choices=ActionType.choices
    )
    amount: Decimal = models.DecimalField(max_digits=12, decimal_places=2)
    currency: str = models.CharField(max_length=10, default="UZS")
    target_person: str = models.CharField(max_length=100, blank=True, null=True)
    note: str = models.TextField(blank=True, null=True)
    date: models.DateField = models.DateField(blank=True, null=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user} | {self.action_type} {self.amount} {self.currency}"

    def __repr__(self) -> str:
        return (
            f"<FinanceAction {self.action_type} {self.amount} {self.currency} "
            f"to {self.target_person or '-'} on {self.date or 'N/A'}>"
        )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Finance Action"
        verbose_name_plural = "Finance Actions"
