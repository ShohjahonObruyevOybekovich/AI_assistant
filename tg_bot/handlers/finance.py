import io
from datetime import datetime
from datetime import time as dtime

import httpx
import pandas as pd
from aiogram.types import BufferedInputFile
from django.db.models import Sum, ExpressionWrapper, DateTimeField, Func, Value, CharField
from django.db.models.functions import Cast, Concat
from icecream import ic

from account.models import CustomUser
from finance.models import FinanceAction
from tg_bot.utils.exchange import get_exchange_rates
from tg_bot.utils.translator import get_text


class FinanceHandler:
    def __init__(self, user_id: int):
        self.user_id = user_id

    async def route(self, data):
        """
        Accepts:
            - single dict → processes one action
            - list of dicts → processes all actions and returns concatenated result
        """
        if isinstance(data, list):
            responses = []
            for item in data:
                single_result = await self._route_single(item)
                if single_result:
                    responses.append(single_result)
            return "\n\n".join([r for r in responses if isinstance(r, str)])
        else:
            return await self._route_single(data)

    async def _route_single(self, data: dict):
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

        elif action == "user_session":
            return await self.user_session(data)

        elif action == "powered_by":
            return await self.powered_by(data)

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
            time=time_obj if not data.get("time_empty", False) else datetime.now().time(),
        )
        if finance:
            return f"✅ {amount} {currency} daromad sifatida muvaffaqiyatli saqlandi!\n📌 Sabab: {reason}\n📅 Sana: {time}"

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
            return f"📉 {amount} {currency} xarajat sifatida saqlandi!\n📌 Sabab: {reason}\n📅 Sana: {formatted_time}"

    async def edit_finance(self, data: dict):
        fin_type = data.get("type", "")
        old_value = data.get("from", "")
        new_value = data.get("to", "")
        changed = data.get("changed", "")

        if not all([fin_type, old_value, new_value, changed]):
            return  "❌ Iltimos, barcha ma'lumotlarni ulashing."

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
            return "❌ Mos keluvchi yozuv topilmadi."

        # Change logic
        if changed == "amount":
            record.amount = int(new_value)
            record.save()
            return f"✏️ Miqdor muvaffaqiyatli o‘zgartirildi:\n💰 {old_value} ➡️ {new_value}"

        elif changed == "type":
            record.action = "EXPENSE" if fin_type == "INCOME" else "INCOME"
            record.amount = abs(int(old_value))
            record.save()
            return f"🔁 Hisobot turi o‘zgartirildi:\n{fin_type} ➡️ {record.action}"

        return "⚠️ O‘zgartirish amalga oshirilmadi."

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
            return "❌ Sana formati noto‘g‘ri. Namuna: 10/05/2025 yoki 01/04/2025-10/04/2025"

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
            return "❌ Vaqt formati noto‘g‘ri. Namuna: 09:00-18:00"

        # --- Construct datetime boundaries ---
        start_datetime = datetime.combine(date_start, start_time)
        end_datetime = datetime.combine(date_end, end_time)

        # --- Filter queryset ---
        queryset = FinanceAction.objects.filter(
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
        response_lines = ["📊 Moliyaviy yozuvlaringiz:\n"]
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
                f"📌 Turi: {'Kirim' if record.action == 'INCOME' else 'Chiqim'}\n"
                f"📝 Sabab: {record.reason}\n"
            )

        # --- Summary conversion ---
        total_uzs = 0
        summary_lines = ["\n💰 Jami hisob:\n"]
        for currency, amount in total_by_currency.items():
            amount_rounded = round(amount, 2)
            status = "🟢 Foyda" if amount_rounded > 0 else "🔴 Zarar" if amount_rounded < 0 else "⚪️ Neytral"

            summary_lines.append(f"• {currency}: {amount_rounded}   ({status})")

            rate = exchange_rates.get(currency.upper())
            if rate:
                total_uzs += amount * rate

        summary_lines.append(f"\n📌 Umumiy qiymat: {round(total_uzs):,} so‘m")

        return "\n".join(response_lines + summary_lines)

    async def excel_data(self, data):

        date_str = data.get("date", "")
        time_range = data.get("time", "").strip()
        action_type = data.get("type", "").upper()

        # Parse date
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

        try:
            if "-" in time_range:
                start_time_str, end_time_str = time_range.split("-")
                start_time = datetime.strptime(start_time_str.strip(), "%H:%M").time()
                end_time = datetime.strptime(end_time_str.strip(), "%H:%M").time()
            else:
                start_time = dtime.min
                end_time = dtime.max
        except ValueError:
            return "❌ Noto‘g‘ri vaqt formati. Misol: 09:00-18:00"

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
            return "⚠️ Ko‘rsatilgan mezonlarga mos yozuvlar topilmadi."

        exchange_rates, error = await get_exchange_rates()
        if error:
            return f"❌ Valyuta kurslarini olishda xatolik: {error}"
        exchange_rates["UZS"] = 1

        data_list = []
        totals_by_currency = {}
        total_uzs = 0

        for record in queryset:
            amount = float(record.amount)
            sign = 1 if record.action == "INCOME" else -1
            signed_amount = sign * amount
            currency = record.currency.upper()
            totals_by_currency.setdefault(currency, 0)
            totals_by_currency[currency] += signed_amount
            total_uzs += signed_amount * exchange_rates.get(currency, 1)

            data_list.append({
                "Sana": record.date.strftime("%d/%m/%Y"),
                "Vaqt": record.time.strftime("%H:%M") if record.time else "--:--",
                "Turi": "Kirim" if record.action == "INCOME" else "Chiqim",
                "Miqdor": signed_amount,
                "Valyuta": currency,
                "Sabab": record.reason,
            })

        df = pd.DataFrame(data_list)
        df.loc[len(df)] = ["", "", "💱 Valyuta Jami", "", "", ""]
        for currency, val in totals_by_currency.items():
            df.loc[len(df)] = ["", "", "", round(val, 2), currency, ""]
        df.loc[len(df)] = ["", "", "", "", "", ""]
        df.loc[len(df)] = ["", "", "📌 Umumiy qiymat", f"{round(total_uzs):,}", "UZS", ""]

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Moliyaviy Xisobot")
            workbook = writer.book
            worksheet = writer.sheets["Moliyaviy Xisobot"]

            header_fmt = workbook.add_format({"bold": True, "bg_color": "#D9E1F2", "border": 1})
            cell_fmt = workbook.add_format({"border": 1})
            num_fmt = workbook.add_format({"border": 1, "num_format": "#,##0", "align": "right"})
            highlight_fmt = workbook.add_format(
                {"bold": True, "bg_color": "#FCE4D6", "border": 1, "num_format": "#,##0"})

            n_rows, n_cols = df.shape
            for col_num, col in enumerate(df.columns):
                worksheet.write(0, col_num, col, header_fmt)
                max_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(col_num, col_num, max_width)

            for row in range(1, n_rows + 1):
                for col in range(n_cols):
                    value = df.iloc[row - 1, col]
                    col_name = df.columns[col]
                    fmt = num_fmt if col_name == "Miqdor" and isinstance(value, (int, float)) else cell_fmt
                    worksheet.write(row, col, value, fmt)

            for idx in range(n_rows):
                row_value = str(df.iloc[idx].get("Turi", ""))
                if "Jami" in row_value or "Umumiy" in row_value:
                    worksheet.set_row(idx + 1, None, highlight_fmt)

        output.seek(0)
        return BufferedInputFile(output.read(), filename=f"FinanceReport {date_start} to {date_end}.xlsx")

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
            return  f"❌ {from_currency} valyutasi bazada mavjud emas."

        if to_currency not in rate_dict and to_currency != "UZS":
            return f"❌ {to_currency} valyutasi bazada mavjud emas."


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
        ic(data
           )

    async def powered_by(self, data):
        lang = CustomUser.objects.get(chat_id=self.user_id).language
        return get_text(
            lang,"powered_by"
        )