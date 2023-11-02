import re


def validate_code(code: str):
    code = code.replace(" ", "-")
    if re.match(r"^[A-Z]{1,4}-[0-9]{1,3}$", code):
        return code
    return None
