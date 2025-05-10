import io
from datetime import datetime

import pandas as pd
from aiogram.types import BufferedInputFile
from django.db.models import Q
from icecream import ic

from account.models import CustomUser
from finance.models import FinanceAction


class FinanceHandler:
    def __init__(self, user_id: int):
        self.user_id = user_id  # Telegram user ID

    async def route(self, data: dict):
        action = data.get("action")

        if action == "create_income":
            return await self.create_income(data)
        elif action == "create_expense":
            return await self.create_expense(data)
        elif action == "list_finance":
            return await self.list_finance(data)
        elif action == "excel_data":
            return await self.excel_data(data)
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
            date=date_obj or None,
            time=time_obj or None,
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

            # Parse date
            date_obj = datetime.strptime(date_part, "%d/%m/%Y").date()

            # Safely parse time if it's not empty and not marked as missing
            if time_part.strip() and not data.get("time_empty", False):
                time_obj = datetime.strptime(time_part, "%H:%M").time()

        user = CustomUser.objects.filter(chat_id=self.user_id).first()

        finance = FinanceAction.objects.create(
            user=user,
            amount=amount,
            currency=currency,
            reason=reason,
            action="EXPENSE",
            date=date_obj,
            time=time_obj,
        )

        if finance:
            formatted_time = f"{date_obj} {time_obj.strftime('%H:%M')}" if time_obj else f"{date_obj}"
            return f"📉 {amount} {currency} xarajat sifatida saqlandi.\nSabab: {reason} | Sana: {formatted_time}"

    async def list_finance(self, data):

        ic(data)

        date_str = data.get("date", "")
        action_type = data.get("type", "").upper()

        try:
            date_obj = datetime.strptime(date_str, "%d/%m/%Y").date()
        except ValueError:
            return "❌ Noto‘g‘ri sana formati. Misol: 10/05/2025"

        if action_type != "ALL":
            queryset = FinanceAction.objects.filter(
                user__chat_id=self.user_id,
                action=action_type,
                date=date_obj
            )
        queryset = FinanceAction.objects.filter(
            user__chat_id=self.user_id,
            date=date_obj
        )

        if not queryset.exists():
            return "⚠️ Ko‘rsatilgan mezonlar bo‘yicha hech qanday ma’lumot topilmadi."

        # Format results
        response_lines = ["📊 Moliyaviy yozuvlaringiz:"]
        for i, record in enumerate(queryset, start=1):

            time_str = record.time.strftime("%H:%M") if record.time else "--:--"

            response_lines.append(
                f"{i}. {record.amount} {record.currency}\nSabab: {record.reason} | Vaqt: {time_str}\n"
            )

        return "\n".join(response_lines)

    async def excel_data(self, data):
        ic("-----------------")

        date_str = data.get("date", "")
        action_type = data.get("type", "").upper()

        # Parse date or range
        if "-" in date_str:
            start_str, end_str = date_str.split("-")
            date_start = datetime.strptime(start_str.strip(), "%d/%m/%Y").date()
            date_end = datetime.strptime(end_str.strip(), "%d/%m/%Y").date()
        else:
            date_start = datetime.strptime(date_str.strip(), "%d/%m/%Y").date()
            date_end = date_start

        # Filter queryset
        queryset = FinanceAction.objects.filter(
            user__chat_id=self.user_id,
            date__range=(date_start, date_end)
        )
        if action_type != "ALL":
            queryset = queryset.filter(action=action_type)

        if not queryset.exists():
            return "⚠️ Ko‘rsatilgan mezonlar bo‘yicha hech qanday ma’lumot topilmadi."

        # Prepare data for DataFrame
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

        # Create in-memory Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="📊 Moliyaviy excel xisobotingiz:")
            writer.close()

        output.seek(0)

        # Return as a Telegram-ready file
        file = BufferedInputFile(
            output.read(),
            filename=f"FinanceReport_{date_start.strftime('%d-%m-%Y')}_to_{date_end.strftime('%d-%m-%Y')}.xlsx"
        )
        return file

