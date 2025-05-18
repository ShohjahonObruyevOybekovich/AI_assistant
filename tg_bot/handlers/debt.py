import datetime

from icecream import ic

from account.models import CustomUser
from debt.models import Debt
from tg_bot.util import parse_datetime_or_date, parse_date


class Debt_Finance:
    def __init__(self, user_id: int):
        self.user_id: int = user_id

    async def route(self, data: dict):
        action = data.get('action')

        if action == 'create_debt':
            return await self.create_debt(data)

        if action == 'repay_debt':
            return await self.repay_debt(data)

        if action == 'update_debt':
            return await self.update_debt(data)

        if action == 'delete_debt':
            return await self.delete_debt(data)

        if action == 'list_debt':
            return await self.list_debt(data)

        if action == 'report_debt':
            return await self.report_debt(data)

        else:
            return "⚠️ Tanlangan qarzdorlik amali mavjud emas."

    async def create_debt(self, data: dict):
        amount = data.get("amount")
        debt_type = data.get("type")  # "GIVE" or "TAKE"
        currency = data.get("currency", "SUM")
        reason = data.get("reason")
        target_person_name = data.get("target_person")
        due_date_input = data.get("due_date")  # Expecting DD/MM/YYYY or DD/MM/YYYY HH:MM
        time_str = data.get("time")  # Expecting DD/MM/YYYY or DD/MM/YYYY HH:MM

        # Basic field validation
        if not all([amount, debt_type, reason, target_person_name, time_str]):
            return "Missing one or more required fields: amount, type, reason, target_person, time."

        try:
            amount = int(amount)
        except ValueError:
            return "Amount must be an integer."

        # Parse time_str into date and time
        dt = parse_datetime_or_date(time_str)
        if not dt:
            return "Invalid date format for time. Use DD/MM/YYYY or DD/MM/YYYY HH:MM."

        date = dt.date()
        time = dt.time()

        due_date = None
        if due_date_input:
            due_date = parse_date(due_date_input)


        user = CustomUser.objects.filter(chat_id=self.user_id).first()

        debt = Debt.objects.create(
            user=user,
            target_person=target_person_name,
            amount=amount,
            type=debt_type,
            currency=currency,
            due_date=due_date,
            reason=reason,
            date=date,
            time=time,
        )

        return (
            f"✅ Qarz muvaffaqiyatli saqlandi!\n"
            f"👤 Shaxs: {target_person_name}\n"
            f"💰 Miqdori: {amount} {currency}\n"
            f"📅 Qaytarish muddati: {due_date.strftime('%d/%m/%Y %H:%M') if due_date else '—'}"
        )

    async def repay_debt(self, data: dict):
        pass

    async def update_debt(self, intent: dict):
        debt_id = intent.get("id")
        if not debt_id:
            return {"error": "❗️Debt ID is required to update."}

        try:
            debt = Debt.objects.get(id=debt_id)
        except Debt.DoesNotExist:
            return {"error": f"❌ Debt with ID {debt_id} not found."}

        # Optional updates
        if "amount" in intent:
            debt.amount = intent["amount"]
        if "type" in intent:
            debt.type = intent["type"]
        if "currency" in intent:
            debt.currency = intent["currency"]
        if "reason" in intent:
            debt.reason = intent["reason"]
        if "target_person" in intent:
            debt.target_person = intent["target_person"]
        if "due_date" in intent:
            try:
                debt.due_date = datetime.strptime(intent["due_date"], "%d/%m/%Y %H:%M")
            except ValueError:
                return {"error": "⚠️ Invalid due_date format. Use DD/MM/YYYY or DD/MM/YYYY HH:MM."}

        debt.save()

        return {
            "success": True,
            "message": f"✅ Qarz ma'lumotlari yangilandi. ID: {debt.id}"
        }

    async def delete_debt(self, data: dict):
        pass

    async def list_debt(self, data: dict):
        """
        data = {
            "date": "2024-01-01 - 2024-12-31",
            "user_id": optional
        }
        """
        date_str = data.get("date", "")
        user_id = data.get("user_id")

        try:
            if "-" in date_str:
                start_date, end_date = [datetime.strptime(d.strip(), "%Y-%m-%d") for d in date_str.split("-")]
            else:
                start_date = end_date = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        except Exception as e:
            return {"error": f"Sana formati noto‘g‘ri: {e}"}

        query = Debt.objects.filter(created_at__range=(start_date, end_date))
        if user_id:
            query = query.filter(user_id=user_id)

        result = []
        for debt in query.select_related("user"):
            result.append({
                "user": f"{debt.user.first_name} {debt.user.last_name}",
                "amount": float(debt.amount),
                "note": debt.reason,
                "date": debt.created_at.strftime("%Y-%m-%d"),
            })

        return {"debts": result}

    async def report_debt(self, data: dict):
        pass