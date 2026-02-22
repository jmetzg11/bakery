from decimal import Decimal
from django import template

register = template.Library()


@register.filter
def clean_qty(value):
    """Display whole numbers without decimals, fractional numbers with decimals."""
    d = Decimal(str(value))
    if d == d.to_integral_value():
        return str(int(d))
    return str(d.normalize())
