import datetime
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from icecream import ic

from account.models import CustomUser
from debt.models import Debt
from tg_bot.utils.exchange import get_exchange_rates


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
        due_date_input = data.get("due_date")
        time_str = data.get("time")

        try:
            amount = int(amount)
        except ValueError:
            return "Amount must be an integer."

        date = None
        time = None

        if time_str:
            day, time = time_str.split(" ")
            if time == "":
                time = datetime.now()
            else:
                time = datetime.datetime.strptime(time, "%H:%M")

        due_date = None
        if due_date_input:
            if due_date_input.split(" ").__len__() != 2:
                due_date = due_date_input + datetime.now().time()
                ic(due_date)
            else:
                due_date = datetime.strptime(due_date_input, "%d/%m/%Y %H:%M")
                ic(due_date)

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

        text = (
            f"✅ Qarz muvaffaqiyatli saqlandi!\n\n"
            f"⌨️ Turi: {"Qarz berish" if debt_type == "GIVE" else "Qarz olish"}\n"
            f"👤 Shaxs: {target_person_name}\n"
            f"💰 Miqdori: {amount} {currency}\n"
        )
        if debt.due_date:
            text += f"📅 Qaytarish muddati: {due_date.strftime('%d/%m/%Y %H:%M') if due_date else '—'}"

        if debt:
            return text

    async def repay_debt(self, data: dict):
        amount = data.get('amount')
        debt_type = data.get("type")  # "GIVE"
        currency = data.get("currency", "SUM")
        target_person_name = data.get('target_person')
        due_date_input = data.get("due_date")
        time_str = data.get("time")

        try:
            amount = int(amount)
        except ValueError:
            return "Amount must be an integer."

        date = None
        time = None

        if time_str:
            day, time = time_str.split(" ")
            if time == "":
                time = datetime.now()
            else:
                time = datetime.datetime.strptime(time, "%H:%M")

        due_date = None
        if due_date_input:
            if due_date_input.split(" ").__len__() != 2:
                due_date = due_date_input + datetime.now().time()
                ic(due_date)
            else:
                due_date = datetime.strptime(due_date_input, "%d/%m/%Y %H:%M")
                ic(due_date)

        total_debt = Debt.objects.filter(target_person=target_person_name, type="TAKE").aggregate(Sum('amount'))[
            'amount__sum']

        print(total_debt)

        if total_debt:
            debt = total_debt - amount
            if debt > 0:
                update_field = Debt.objects.filter(
                    user__chat_id=self.user_id,
                    target_person_icontains=target_person_name,
                    amount=total_debt,
                    currency=currency,
                ).first()
                if update_field:
                    update_field.amount = debt
                    update_field.save()
                return f"Umumiy qolgan qarzingiz - {debt}"
            else:
                return f"{target_person_name}dan olingan qarzingiz qolmadi!!!"

        else:
            return f"Qarz topilmadi"

    async def update_debt(self, intent: dict):
        try:
            debt = Debt.objects.get(
                user__chat_id=self.user_id,
                target_person__icontains=intent.get("target_person"),
                amount=intent.get("amount"),
                type=intent.get("type"),
                currency=intent.get("currency")
            )
        except ObjectDoesNotExist:
            # Handle if the debt entry does not exist
            return "❌ Qarz topilmadi. Iltimos, ma'lumotlarni tekshiring."

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
                debt.due_date = datetime.strptime(intent["due_date"], "%d-%m-%Y")
            except ValueError:
                return "❌ Noto'g'ri sana formati. Iltimos, DD-MM-YYYY formatda kiriting."

        debt.save()
        return "✅ Qarz muvaffaqiyatli yangilandi!"

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
        action_type = data.get("type").upper()
        time_range = data.get("time", "").strip()

        # --- Parse dates ---
        try:
            if "-" in date_str:
                start_str, end_str = date_str.split("-")
                date_start = datetime.strptime(start_str.strip(), "%d/%m/%Y").date()
                date_end = datetime.strptime(end_str.strip(), "%d/%m/%Y").date()
            else:
                date_start = datetime.strptime(date_str.strip(), "%d/%m/%Y").date()
                date_end = date_start
        except ValueError:
            return "❌ Sana formati noto‘g‘ri. Namuna: 10/05/2025 yoki 01/04/2025-10/04/2025"

        # --- Parse times ---
        try:
            if time_range and "-" in time_range:
                start_time_str, end_time_str = time_range.split("-")
                start_time = datetime.strptime(start_time_str.strip(), "%H:%M").time()
                end_time = datetime.strptime(end_time_str.strip(), "%H:%M").time()
            else:
                start_time = datetime.time.min
                end_time = datetime.time.max
        except ValueError:
            return "❌ Vaqt formati noto‘g‘ri. Namuna: 09:00-18:00"

        # --- Construct datetime boundaries ---
        start_datetime = datetime.combine(date_start, start_time)
        end_datetime = datetime.combine(date_end, end_time)

        # --- Filter queryset ---
        queryset = Debt.objects.filter(
            user__chat_id=self.user_id,
            date__range=(date_start, date_end),
        ).filter(
            time__range=(start_datetime, end_datetime)
        )

        if action_type != "ALL":
            queryset = queryset.filter(action=action_type)

        if not queryset.exists():
            return "⚠️ Ko‘rsatilgan mezonlar bo‘yicha hech qanday ma’lumot topilmadi."

        # --- Fetch exchange rates ---
        exchange_rates, error = await get_exchange_rates()
        if error:
            return f"❌ Valyuta kurslarini olishda xatolik: {error}"

        exchange_rates["UZS"] = 1  # fallback

        # --- Format results ---
        response_lines = ["📊 Qarizdorlik yozuvlaringiz:\n"]
        total_by_currency = {}

        for i, record in enumerate(queryset.order_by("date", "time"), start=1):
            time_str = record.time.strftime("%H:%M") if record.time else "--:--"
            date_str = record.date.strftime("%d/%m/%Y")
            sign = 1 if record.action == "INCOME" else -1

            # Track totals
            total_by_currency.setdefault(record.currency, 0)
            total_by_currency[record.currency] += sign * float(record.amount)

            response_lines.append(
                f"{i}. {record.amount} {record.currency} | {date_str} {time_str}\n"
                f"📌 Turi: {'Qarz olish' if record.action == 'TAKE' else 'Qarz berish'}\n"
                f"📝 Sabab: {record.reason}\n"
            )

        # --- Summary conversion ---
        total_uzs = 0
        summary_lines = ["\n💰 Jami hisob:\n"]
        for currency, amount in total_by_currency.items():
            amount_rounded = round(amount, 2)
            status = "🟢 Olingan qarizlar" if amount_rounded > 0 else "🔴 Berilgan qarizlar" if amount_rounded < 0 else "⚪️ Neytral"

            summary_lines.append(f"• {currency}: {amount_rounded}   ({status})")

            rate = exchange_rates.get(currency.upper())
            if rate:
                total_uzs += amount * rate

        summary_lines.append(f"\n📌 Umumiy qiymat: {round(total_uzs):,} so‘m")

        return "\n".join(response_lines + summary_lines)

    async def report_debt(self, data: dict):
        pass
