"""Provide centralized masking helpers for sensitive response fields across APIs."""


def mask_value(value: str, strategy: str) -> str:
    if strategy == "full":
        return "*" * len(value)
    if strategy == "phone" and len(value) >= 7:
        return f"{value[:3]}****{value[-4:]}"
    if strategy == "id" and len(value) >= 6:
        return f"{value[:2]}********{value[-2:]}"
    return value


def mask_email(value: str) -> str:
    if "@" not in value:
        return mask_value(value, "full")
    local, domain = value.split("@", 1)
    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = f"{local[0]}***{local[-1]}"
    return f"{masked_local}@{domain}"


def mask_storage_path(value: str, role_name: str) -> str:
    if role_name in {"administrator", "auditor"}:
        return value
    parts = value.replace("\\", "/").split("/")
    return f".../{parts[-1]}" if parts else value
