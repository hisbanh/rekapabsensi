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

@register.filter
def make_list(value):
    """Convert a number to a range list for iteration in templates.
    Usage: {% for i in 6|make_list %}
    """
    try:
        return range(1, int(value) + 1)
    except (ValueError, TypeError):
        return []

@register.filter
def subtract(value, arg):
    """Subtract arg from value"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def avatar_initials(name):
    """Generate 2-letter initials from name"""
    if not name or not isinstance(name, str):
        return "??"
    
    # Clean the name and split into words
    name = name.strip()
    if not name:
        return "??"
    
    words = name.split()
    
    if len(words) >= 2:
        # Take first letter of first two words
        return (words[0][0] + words[1][0]).upper()
    elif len(words) == 1:
        # Take first two letters of single word
        word = words[0]
        if len(word) >= 2:
            return word[:2].upper()
        else:
            return (word[0] + word[0]).upper()
    else:
        return "??"

@register.filter
def avatar_color(name):
    """Generate consistent color based on name hash"""
    if not name or not isinstance(name, str):
        return '#6366F1'  # Default primary color
    
    # Predefined color palette matching the design system
    colors = [
        '#6366F1',  # Primary indigo
        '#8B5CF6',  # Purple
        '#EC4899',  # Pink
        '#EF4444',  # Red
        '#F97316',  # Orange
        '#EAB308',  # Yellow
        '#22C55E',  # Green
        '#14B8A6',  # Teal
        '#06B6D4',  # Cyan
        '#3B82F6'   # Blue
    ]
    
    # Generate hash from name
    name = name.strip().lower()
    hash_val = sum(ord(c) for c in name)
    
    # Return consistent color based on hash
    return colors[hash_val % len(colors)]