"""Python names for CSDL identifiers."""

import keyword
import re


def snake(name):
    """Turn a CSDL name into a snake_case Python name."""
    text = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
    text = text.replace("-", "_").replace(".", "_").lower()
    if keyword.iskeyword(text):
        text = text + "_value"
    return text


def ident(name):
    if name.isidentifier() and not keyword.iskeyword(name):
        return name
    cleaned = re.sub(r"\W", "_", name)
    if not cleaned or cleaned[0].isdigit():
        cleaned = "member_" + cleaned
    if keyword.iskeyword(cleaned):
        cleaned = cleaned + "_value"
    return cleaned
