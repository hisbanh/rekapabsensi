from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a key"""
    return dictionary.get(key)

@register.filter
def get_attr(obj, attr):
    """Get an attribute from an object using a string key.
    Supports nested attributes using dot notation (e.g., 'student.name')
    """
    try:
        for part in attr.split('.'):
            obj = getattr(obj, part, None)
            if obj is None:
                return ''
        return obj
    except (AttributeError, TypeError):
        return ''

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """Calculate percentage"""
    try:
        if int(total) == 0:
            return 0
        return round((int(value) / int(total)) * 100, 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0