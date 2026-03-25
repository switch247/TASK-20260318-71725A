import re

PASSWORD_PATTERN = re.compile(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d\W_]{8,}$")


def validate_password_policy(password: str) -> bool:
    return bool(PASSWORD_PATTERN.match(password))
