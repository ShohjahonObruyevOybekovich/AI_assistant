# from bot.models import Payment, Installment
import datetime
from time import localtime

from dateutil.relativedelta import relativedelta

# from bot.models import Certification, Kpi, Amount


def format_phone_number(phone_number: str) -> str:

    phone_number = ''.join(c for c in phone_number if c.isdigit())

    # Prepend +998 if missing
    if phone_number.startswith('998'):
        phone_number = '+' + phone_number
    elif not phone_number.startswith('+998'):
        phone_number = '+998' + phone_number

    # Check final phone number length
    if len(phone_number) == 13:
        return phone_number
    else:
        raise ValueError("Invalid phone number length")


import re

def extract_payment_amount(text):
    """
    Extracts the first numeric value from a given string and returns it as a number.
    Handles cases where numbers are embedded within words or surrounded by text.

    Args:
        text (str): The input string.

    Returns:
        float: The extracted number or None if no number is found.
    """
    # Find the first match for a number in the string
    match = re.search(r'\d+(\.\d+)?', text)  # Matches integers or decimals
    if match:
        return float(match.group())  # Convert the matched string to a float
    return None  # Return None if no numbers are found

