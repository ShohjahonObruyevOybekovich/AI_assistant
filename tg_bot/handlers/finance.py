import io
from datetime import datetime

import httpx
import pandas as pd
from aiogram.types import BufferedInputFile
from django.db.models import Sum, ExpressionWrapper, F, DateTimeField, Func, Value, CharField
from django.db.models.functions import Cast, Concat
from icecream import ic
from datetime import time as dtime

from pandas.io.clipboard import paste

from account.models import CustomUser
from finance.models import FinanceAction
from tg_bot.utils.translator import get_text


class FinanceHandler:
    def __init__(self, user_id: int):
        self.user_id = user_id

    async def route(self, data: dict):
        action = data.get("action")

        if action == "create_income":
            return await self.create_income(data)

        elif action == "create_expense":
            return await self.create_expense(data)

        elif action == "list_finance":
            return await self.list_finance(data)

        elif action == "edit_finance":
            return await self.edit_finance(data)

        elif action == "excel_data":
            return await self.excel_data(data)

        elif action == "dollar_course":
            return await self.dollar_course(data)

        else:
            return "⚠️ Tanlangan moliyaviy amal mavjud emas."

    async def create_income(self, data):
        # Example: save to DB
        amount = data.get("amount", 0)
        currency = data.get("currency", "UZS")
        reason = data.get("reason", "")
        time = data.get("time", "")
        ic(data.get("time_empty"))

        date_obj = None
        time_obj = None

        if time:
            date_part, time_part = time.split(" ")
            date_obj = datetime.strptime(date_part, "%d/%m/%Y").date()

            if time_part.strip() and not data.get("time_empty", False):
                time_obj = datetime.strptime(time_part, "%H:%M").time()

        user = CustomUser.objects.filter(chat_id=self.user_id).first()

        finance = FinanceAction.objects.create(
            user=user,
            amount=amount,
            currency=currency,
            reason=reason,
            action="INCOME",
            date=date_obj or datetime.today().date(),
            time=time_obj if not data.get("time_empty", False) else datetime.today().time(),
        )
        if finance:
            return f"✅ {amount} {currency} daromad sifatida saqlandi.\n Sabab: {reason} | Sana: {time}"

    async def create_expense(self, data):
        amount = data.get("amount", 0)
        currency = data.get("currency", "UZS")
        reason = data.get("reason", "")
        time = data.get("time", "")

        date_obj = None
        time_obj = None

        if time:
            date_part, time_part = time.split(" ")
            date_obj = datetime.strptime(date_part, "%d/%m/%Y").date()

            if time_part.strip() and not data.get("time_empty", False):
                time_obj = datetime.strptime(time_part, "%H:%M").time()

        user = CustomUser.objects.filter(chat_id=self.user_id).first()

        finance = FinanceAction.objects.create(
            user=user,
            amount=amount,
            currency=currency,
            reason=reason,
            action="EXPENSE",
            date=date_obj or datetime.today().date(),
            time=time_obj if not data.get("time_empty", False) else datetime.today().time(),
        )

        if finance:
            formatted_time = f"{date_obj} {time_obj.strftime('%H:%M')}" if time_obj else f"{date_obj}"
            return f"📉 {amount} {currency} xarajat sifatida saqlandi.\nSabab: {reason} | Sana: {formatted_time}"

    async def edit_finance(self, data: dict):
        fin_type = data.get("type", "")
        old_value = data.get("from", "")
        new_value = data.get("to", "")
        changed = data.get("changed", "")

        if not all([fin_type, old_value, new_value, changed]):
            return "❌ Kerakli ma'lumotlar to‘liq emas."

        # Get user
        user = CustomUser.objects.filter(chat_id=self.user_id).first()
        if not user:
            return "❌ Foydalanuvchi topilmadi."

        # Find the most recent matching FinanceAction
        record = FinanceAction.objects.filter(
            user=user,
            action=fin_type,
            amount=old_value,
        ).order_by("-date", "-created_at").first()

        if not record:
            return "❌ Mos yozuv topilmadi."

        # Change logic
        if changed == "amount":
            record.amount = int(new_value)
            record.save()
            return f"✏️ Miqdor o‘zgartirildi: {old_value} ➡️ {new_value}"

        elif changed == "type":
            record.action = "EXPENSE" if fin_type == "INCOME" else "INCOME"
            record.amount = abs(int(old_value))
            record.save()
            return f"🔄 Turi o‘zgartirildi: {fin_type} ➡️ {record.action}"

        return "⚠️ Hech narsa o‘zgartirilmadi."

    async def list_finance(self, data):
        ic(data)

        date_str = data.get("date", "")
        action_type = data.get("type", "").upper()
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
            return "❌ Noto‘g‘ri sana formati. Misol: 10/05/2025 yoki 01/04/2025-10/04/2025"

        # --- Parse times ---
        try:
            if time_range and "-" in time_range:
                start_time_str, end_time_str = time_range.split("-")
                start_time = datetime.strptime(start_time_str.strip(), "%H:%M").time()
                end_time = datetime.strptime(end_time_str.strip(), "%H:%M").time()
            else:
                start_time = dtime.min
                end_time = dtime.max
        except ValueError:
            return "❌ Noto‘g‘ri vaqt formati. Misol: 09:00-18:00"

        # --- Construct datetime boundaries ---
        start_datetime = datetime.combine(date_start, start_time)
        end_datetime = datetime.combine(date_end, end_time)

        # --- Filter ---
        queryset = FinanceAction.objects.filter(
            user__chat_id=self.user_id,
            date__range=(date_start, date_end),
        ).filter(
            # Combine both for precise filtering
            time__range=(start_datetime, end_datetime)
        )

        if action_type != "ALL":
            queryset = queryset.filter(action=action_type)

        ic(queryset)

        if not queryset.exists():
            return "⚠️ Ko‘rsatilgan mezonlar bo‘yicha hech qanday ma’lumot topilmadi."

        # --- Response formatting ---
        response_lines = ["📊 Moliyaviy yozuvlaringiz:\n"]
        for i, record in enumerate(queryset.order_by("date", "time"), start=1):
            time_str = record.time.strftime("%H:%M") if record.time else "--:--"
            date_str = record.date.strftime("%d/%m/%Y")
            response_lines.append(
                f"{i}. {record.amount} {record.currency} | {date_str} {time_str}\n"
                f"Turi: {"Kirim" if record.action == "INCOME" else "Chiqim"}\n"
                f"Sabab: {record.reason}\n"
            )

        return "\n".join(response_lines)

    async def excel_data(self, data):
        ic("-----------------")

        date_str = data.get("date", "")
        time_range = data.get("time", "").strip()
        action_type = data.get("type", "").upper()

        # Parse date or date range
        try:
            if "-" in date_str:
                start_str, end_str = date_str.split("-")
                date_start = datetime.strptime(start_str.strip(), "%d/%m/%Y").date()
                date_end = datetime.strptime(end_str.strip(), "%d/%m/%Y").date()
            else:
                date_start = datetime.strptime(date_str.strip(), "%d/%m/%Y").date()
                date_end = date_start
        except ValueError:
            return "❌ Noto‘g‘ri sana formati. Misol: 10/05/2025 yoki 01/04/2025-10/04/2025"

        # Parse time range
        try:
            if time_range and "-" in time_range:
                start_time_str, end_time_str = time_range.split("-")
                start_time = datetime.strptime(start_time_str.strip(), "%H:%M").time()
                end_time = datetime.strptime(end_time_str.strip(), "%H:%M").time()
            else:
                start_time = dtime.min
                end_time = dtime.max
        except ValueError:
            return "❌ Noto‘g‘ri vaqt formati. Misol: 09:00-18:00"

        start_dt = datetime.combine(date_start, start_time)
        end_dt = datetime.combine(date_end, end_time)

        # Annotate datetime and filter
        queryset = FinanceAction.objects.filter(
            user__chat_id=self.user_id,
            date__range=(date_start, date_end)
        ).annotate(
            dt=ExpressionWrapper(
                Func(
                    Concat(
                        Cast("date", output_field=CharField()),
                        Value(" "),
                        Cast("time", output_field=CharField())
                    ),
                    function="TO_TIMESTAMP",
                    template="TO_TIMESTAMP(%(expressions)s, 'YYYY-MM-DD HH24:MI:SS')",
                    output_field=DateTimeField()
                ),
                output_field=DateTimeField()
            )
        )

        if action_type != "ALL":
            queryset = queryset.filter(action=action_type)

        if not queryset.exists():
            return "⚠️ Ko‘rsatilgan mezonlar bo‘yicha hech qanday ma’lumot topilmadi."

        # Prepare data
        data_list = []
        for record in queryset:
            data_list.append({
                "Sana": record.date.strftime("%d/%m/%Y"),
                "Vaqt": record.time.strftime("%H:%M") if record.time else "--:--",
                "Turi": "Kirim" if record.action == "INCOME" else "Chiqim",
                "Miqdor": record.amount,
                "Valyuta": record.currency,
                "Sabab": record.reason,
            })

        df = pd.DataFrame(data_list)

        # Add total row
        total_sum = queryset.aggregate(total=Sum("amount"))["total"]
        df.loc[len(df.index)] = ["", "", "Jami", total_sum, "", ""]

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="📊 Moliyaviy xisobot")

        output.seek(0)

        return BufferedInputFile(
            output.read(),
            filename=f"FinanceReport {date_start.strftime('%d-%m-%Y')} to {date_end.strftime('%d-%m-%Y')}.xlsx"
        )

    async def dollar_course(self, data):
        from_currency = data.get("from", "USD").upper()
        to_currency = data.get("to", "UZS").upper()
        amount = float(data.get("amount", 1))

        url = "https://cbu.uz/oz/arkhiv-kursov-valyut/json/"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                rates = response.json()
        except Exception as e:
            ic(e)
            user = CustomUser.objects.get(chat_id=self.user_id)
            return get_text(user.language,"currency_fetch_error")

        rate_dict = {item["Ccy"]: float(item["Rate"].replace(",", "")) for item in rates}

        if from_currency not in rate_dict and from_currency != "UZS":
            return f"❌ {from_currency} valyutasi topilmadi."
        if to_currency not in rate_dict and to_currency != "UZS":
            return f"❌ {to_currency} valyutasi topilmadi."


        if from_currency == "UZS":
            amount_in_uzs = amount
        else:
            amount_in_uzs = amount * rate_dict[from_currency]

        if to_currency == "UZS":
            converted = amount_in_uzs
        else:
            converted = amount_in_uzs / rate_dict[to_currency]

        return f"💱 {amount} {from_currency} ≈ {round(converted, 2)} {to_currency}"

    async def user_session(self, data):
        ic(paste)