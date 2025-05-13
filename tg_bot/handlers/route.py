# route.py

from .finance import FinanceHandler
from .debt import Debt
from aiogram.types import BufferedInputFile
from account.models import CustomUser
from tg_bot.utils.translator import get_text

finance_actions = [
    "create_income", "create_expense", "edit_finance", "list_finance",
    "excel_data", "dollar_course", "user_session", "powered_by",
]

debt_actions = [
    "create_debt", "repay_debt", "update_debt_due", "delete_debt",
    "list_debt", "report_debt",
]


async def route_intent(user_id: int, intent: dict) -> str | BufferedInputFile | None:
    action = intent.get("action")
    user = CustomUser.objects.filter(chat_id=user_id).first()

    if not action:
        return get_text(user, "unknown_command")

    # Finance actions routing
    if action in finance_actions:
        return await FinanceHandler(user_id=user_id).route(intent)

    # Debt actions routing
    if action in debt_actions:
        return await Debt(user_id=user_id).route(intent)

    return get_text(user, "unsupported_action")
