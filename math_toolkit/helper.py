"""Helper utilities used by math_toolkit's entry point."""


def format_result(label, value):
    """Return a human-readable label for a computed value."""
    return f"{label} = {value}"


def parse_number(text):
    """Convert user input text into an int or float."""
    text = text.strip()
    return int(text) if text.lstrip("-").isdigit() else float(text)
