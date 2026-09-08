"""
Common — Reusable Validators
==============================
Shared field-level validators used across multiple apps.
"""
import re
from datetime import date

from django.core.exceptions import ValidationError


def validate_egyptian_phone(value: str) -> str:
    """
    Validate that the phone number matches Egyptian mobile format.
    Accepts: 01012345678  or  +201012345678
    Pattern: starts with 010, 011, 012, or 015 followed by 8 digits.
    """
    # Strip leading/trailing whitespace
    value = value.strip()

    # Normalize to local format (replace country code with 0)
    if value.startswith("+20"):
        value = "0" + value[3:]
    elif value.startswith("20") and len(value) == 12:
        value = "0" + value[2:]

    # Now check local format
    pattern = r"^01[0125]\d{8}$"
    if not re.match(pattern, value):
        raise ValidationError(
            "رقم الهاتف غير صالح. يجب أن يكون رقم هاتف مصري صحيح (مثال: 01012345678)."
        )

    return value


def validate_birthday(value: date) -> date:
    """
    Validate that the birthday is a valid past date.
    Enforces a minimum age of 18 years.
    """
    today = date.today()

    if value >= today:
        raise ValidationError("تاريخ الميلاد يجب أن يكون في الماضي.")

    # Calculate age
    age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))

    if age < 18:
        raise ValidationError("يجب أن يكون عمرك 18 عامًا على الأقل.")

    if age > 120:
        raise ValidationError("تاريخ الميلاد غير صالح.")

    return value
