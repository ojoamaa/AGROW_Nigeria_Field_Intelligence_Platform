import re


def valid_phone(phone: str) -> bool:
    return phone.isdigit() and len(phone) == 11


def valid_nin(nin: str) -> bool:
    return nin.isdigit() and len(nin) == 11


def valid_email(email: str) -> bool:
    pattern = r"[^@]+@[^@]+\.[^@]+"
    return re.match(pattern, email) is not None
