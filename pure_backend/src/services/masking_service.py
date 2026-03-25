def mask_value(value: str, strategy: str) -> str:
    if strategy == "full":
        return "*" * len(value)
    if strategy == "phone" and len(value) >= 7:
        return f"{value[:3]}****{value[-4:]}"
    if strategy == "id" and len(value) >= 6:
        return f"{value[:2]}********{value[-2:]}"
    return value
