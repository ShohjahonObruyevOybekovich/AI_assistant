from datetime import datetime


def parse_datetime_or_date(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%d/%m/%Y %H:%M")
    except ValueError:
        try:
            d = datetime.strptime(value, "%d/%m/%Y").date()
            return datetime.combine(d, datetime.now().time())
        except ValueError:
            return None


def parse_date(date_str):
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError("Invalid date format for due_date. Use DD/MM/YYYY or DD/MM/YYYY HH:MM.")