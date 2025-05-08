from icecream import ic
from openai import OpenAI
from decouple import config
from datetime import datetime
import json
from finance.models import FinanceAction
from account.models import CustomUser
from django.db.models import Sum

client = OpenAI(api_key=config("AI_TOKEN"))

def extract_intent_and_handle(prompt_text: str, user_telegram_id: str) -> dict:
    intent_prompt = f"""
    You are a finance assistant that understands Uzbek.
    Determine the user's intent from this sentence: "{prompt_text}"

    Respond with only one word in lowercase:
    - "create" if they are trying to save or register a financial action (e.g., "berdim", "olganman", "qarz berdim")
    - "query" if they are asking for financial status or logs (e.g., "yubor", "ko‘rsat", "hisobot", "tahlil qil")
    If unsure, respond with "unknown".
    """
    try:
        intent_resp = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": intent_prompt}],
            temperature=0,
        )
        intent = intent_resp.choices[0].message.content.strip().lower()

        if intent == "create":
            return handle_create_action(prompt_text, user_telegram_id)
        elif intent == "query":
            return handle_query_logs(prompt_text, user_telegram_id)
        else:
            return {"error": "Unknown intent", "raw_response": intent}

    except Exception as e:
        return {"error": str(e)}

def handle_create_action(prompt_text: str, user_telegram_id: str) -> dict:
    prompt = f"""
    You are a smart Uzbek finance assistant.
    Extract the following structured fields from this sentence:
    Sentence: "{prompt_text}"

    Return as pure JSON with no explanation:
    {{
      "action_type": "give", 
      "amount": 100000,
      "currency": "UZS",
      "target_person": "my brother",
      "note": "optional",
      "date": "2025-05-08"
    }}
    Respond ONLY with JSON that starts with '{{' and is valid.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = response.choices[0].message.content.strip()

        ic(content)

        if not content.startswith("{"):
            return {"error": "Invalid JSON format from LLM", "raw_response": content}

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            return {"error": "JSON parsing failed", "exception": str(e), "raw_response": content}

        if data.get("date"):
            try:
                datetime.strptime(data["date"], "%Y-%m-%d")
            except ValueError:
                data["date"] = None

        data.setdefault("currency", "UZS")

        user = CustomUser.objects.get(chat_id=str(user_telegram_id))
        FinanceAction.objects.create(
            user=user,
            action_type=data["action_type"],
            amount=data["amount"],
            currency=data["currency"],
            target_person=data.get("target_person"),
            note=data.get("note"),
            date=data.get("date")
        )
        data["action_type"] = "create"
        return data

    except Exception as e:
        return {"error": str(e)}

def handle_query_logs(prompt_text: str, user_telegram_id: str) -> dict:
    month_prompt = f"""
    You are an assistant that extracts a month from a sentence in Uzbek.

    Example 1: "menga may oyi xarajatlarini yubor" → "2025-05"
    Example 2: "bugungi xarajatlarimni yubor" → "{datetime.today().strftime('%Y-%m')}"
    Example 3: "mart oyidagi daromadlarimni ko'rsat" → "2025-03"

    Extract only in YYYY-MM format:
    "{prompt_text}"
    """
    try:
        month_resp = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": month_prompt}],
            temperature=0,
        )
        parsed_date = month_resp.choices[0].message.content.strip()

        try:
            year, month = map(int, parsed_date.split("-"))
        except Exception:
            today = datetime.today()
            year, month = today.year, today.month

        user = CustomUser.objects.get(chat_id=str(user_telegram_id))
        logs = FinanceAction.objects.filter(user=user, date__year=year, date__month=month)

        total = logs.aggregate(total=Sum("amount"))["total"] or 0
        count = logs.count()
        items = [f"{a.action_type}: {a.amount} {a.currency} ({a.note or ''})" for a in logs]

        return {
            "action_type": "query",
            "year": year,
            "month": month,
            "entries": count,
            "total_amount": float(total),
            "logs": items or ["No records found"]
        }

    except Exception as e:
        return {"error": str(e)}
