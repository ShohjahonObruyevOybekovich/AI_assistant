import json
import re
from datetime import datetime
import os

from decouple import config
from openai import AsyncOpenAI
from django.utils import timezone
from icecream import ic


class GptFunctions:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=config("AI_TOKEN"))

    async def prompt_to_json(self, user_id, text: str):
        INSTRUCTION = """Convert voice commands in Uzbek into JSON commands with the specified structure.

    - Extract key information such as action type, name, time, and other relevant details from the voice command.
    - Ensure the output JSON is consistent with the required fields and format.

    # Steps

    1. **Identify the Action**: Determine the primary action from the prompt, translating from Uzbek if necessary. use check_free_time for checking for free time and check_free_date for checking time for date 
    2. **Our existing actions**: 'create_meeting*', 'list_meetings*', 'send_document*', 'remind_something', 'check_free_time','check_free_date','create_income', 'create_expense', 'list_finance', 'excel_data', 'currency_price', 'powered_by' . Prioritize actions with * at the end
    3. **Extract Details**: Parse the Uzbek voice command to extract details such as name, time, and other relevant information.
    4. **Format Date and Time**: Convert and format the date and time from the command to the "dd/mm/yyyy hh:mm" format.
    5. **Construct JSON**: Assemble the extracted information into the JSON command with the following structure.
    6. **Accuracy**: If Accuracy is low just return empty string in action field
    7. **Actions**: User can ask for several thing. Create meeting, list meetings, Ask some documents.

    # Output Format

    The output should be a JSON object with the following fields:
    - **action**: The primary action in lowercase with underscores.
    - **name**: The name of the person involved.
    - **time**: The date and time of meeting, document, reminder in "dd/mm/yyyy hh:mm" format or empty.If in contex there is no time exactly
    mentioned just return time_empty field.Example "08/05/2025 ", time_empty = True
    - **phone_number**: Include the phone number if provided, or an empty string otherwise.
    - **amount**: Income or Expanse amount or 0
    - **reason**: Reason of Income, Expanse, Meeting, place of meeting or empty string
    - **currency**: Currency of finance (USD | UZS)
    - **remind_text**: Text for reminding something. You have to add some meaningful text without grammar mistakes. in uzbek language
    - **document_id**: list of Id of document which provided to you.

    # Finance actions

    When the action is related to **create_income** or **create_expense** or **list_finance** respond with a nested object like this:
    
    # Additional Clarifications

    - `time_empty` must be included as true if the user only says a date or vague time (e.g., “ertalab”, “kechasi”, “bugun” without specific hours).
    - `type` for list_finance must always be one of: "INCOME", "EXPENSE", or "ALL". Do not return other words.
    - The `date` field for `list_finance` must be present in `"dd/mm/yyyy"` format, even if only a vague reference like "bugun" or "kecha" was made.

    # Examples
    **Input:** "Ikki kun avvalgi mening kirimlarim excel ro'yxatini tashlab ber."
    **Output:**
    {{
        "action": "excel_data",
        "date": "08/05/2025",
        "type": "INCOME",
        "time": "",
    }}
    
    **Input:** "Bir oylik xisobotlarim excel ro'yxatini tashlab ber."
    **Output:**
    {{
        "action": "excel_data",
        "date": "10/04/2025-10/05/2025",
        "type": "ALL",
        "time": "",
    }}
    
    
    **Output:**
    {{
        "action": "list_finance",
        "date": "08/05/2025",
        "type": "INCOME",
        "time": "",
    }}
    
    **Input:** "Ikki kun avvalgi mening kirimlarim ro'yxatini tashlab ber."
    
    **Output:**
    {{
        "action": "list_finance",
        "date": "08/05/2025",
        "type": "INCOME",
        "time": "",
    }}
    
    **Input:** "Bugungi kun uchun Bekjonga bergan chiqimlarimni tashlab ber."
    
    **Output:**
    {{
        "action": "list_finance",
        "date": "10/05/2025",
        "type": "EXPANSE",
        "time": "",
    }}
    
    **Input:** "Bugungi kun uchun xisobotlarimni yubor."
    
    **Output:**
    {{
        "action": "list_finance",
        "date": "10/05/2025",
        "type": "ALL",
        "time": "",
    }}
    # Examples 

    **Input:** "Bugun men abetgi 2 da 100000 sum oylik oldim."

    **Output:**
    {{
        "action": "create_income",
        "amount": "100000",
        "currency": "UZS",
        "reason": "Ish haqi",
        "time": "08/05/2025 14:00"
        "time_empty": false,
    }}

    **Input:** "Kecha ukamga 500000 ming sum qarz bergan edim."

    **Output:**
    {{
        "action": "create_expense",
        "amount": "500000",
        "currency": "UZS",
        "reason": "Qarz berish",
        "time": "07/05/2025 14:00"
    }}

    # Examples

    **Input:** "ikkiming yigirma to'rtinchi yil 22 Oktabr da  o'n to'rtu no'l no'lga Shukurulloh bilan uchrashuv belgila"

    **Output:**
    {{
        "action": "create_meeting",
        "name": "Shukurulloh",
        "time": "22/10/2024 14:00",
        "phone_number": ""
    }}

    **Input:** "Manga yigirma ikkiyu no'l no'lga uxlashimni eslat."

    **Output:**
    {{
        "action": "remind_something",
        "name": "Remind Sleep",
        "time": "{today} 22:00",
        "remind_text": "Soat 22:00 da uhlashingiz kerak."
    }}

    **Input:** "Bu botni kim yaratgan."

    **Output:**
    {{
        "action": "powered_by"
    }}

    # Notes

    - Pay attention to varying phrasings in Uzbek voice commands and ensure accurate extraction.
    - Handle different potential formats for dates and times, converting them to the required format.
    - Response must be only json. no other texts around json brace (before and after)
    - Today is {today}

    Documents list:
        {documents}
    """.format(
                today=timezone.now().strftime("%d/%m/%Y"),
                documents="N/A"
            )
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": INSTRUCTION},
                {"role": "user", "content": text},
            ],
            temperature=0.2,
        )

        raw_content = response.choices[0].message.content.strip()
        ic("RAW GPT OUTPUT:", raw_content)

        # Make sure GPT response is valid JSON and parse it
        if raw_content.startswith("```"):
            raw_content = re.sub(r"^```(?:json)?\n?", "", raw_content)  # remove ```json or ```
            raw_content = re.sub(r"\n?```$", "", raw_content)  # remove ending ```

        try:
            result = json.loads(raw_content)
            return result
        except json.JSONDecodeError as e:
            ic("❌ JSON decoding failed:", e)
            return {"action": ""}