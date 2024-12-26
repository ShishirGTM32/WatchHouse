from django import template

register = template.Library()

@register.filter(name='multiply')
def multiply(value, arg):
    """Multiplies the value by the argument"""
    try:
        return value * arg
    except (TypeError, ValueError):
        return 0

@register.filter(name='equals')
def equals(value, arg):
    return value == arg