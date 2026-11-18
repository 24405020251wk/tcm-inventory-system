from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


def _dec(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")


@register.filter
def mul(a, b):
    return _dec(a) * _dec(b)


@register.filter
def sub(a, b):
    return _dec(a) - _dec(b)


@register.filter
def add_num(a, b):
    return _dec(a) + _dec(b)


@register.filter
def abs_num(value):
    return abs(_dec(value))


@register.filter
def money(value, digits=2):
    try:
        return f"{_dec(value):,.{digits}f}"
    except Exception:
        return value


@register.filter
def percent(part, total):
    total = _dec(total)
    if not total:
        return "0%"
    return f"{(_dec(part) / total * 100):.1f}%"


@register.filter
def get_item(mapping, key):
    if hasattr(mapping, "get"):
        return mapping.get(key)
    return None


@register.filter
def status_badge(status):
    mapping = {
        "draft": "secondary",
        "pending": "warning",
        "confirmed": "success",
        "approved": "success",
        "rejected": "danger",
        "cancelled": "dark",
        "active": "success",
        "inactive": "secondary",
        "exhausted": "secondary",
        "expired": "danger",
    }
    return mapping.get(status, "secondary")
