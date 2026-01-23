"""
Custom template tags and filters for schedule management
"""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Get item from dictionary by key
    Usage: {{ my_dict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key, [])


@register.filter
def get_schedule_at_jp(schedules, jp):
    """
    Check if there's a schedule at specific JP
    Usage: {{ schedules|get_schedule_at_jp:jp }}
    """
    if not schedules:
        return None
    
    for schedule in schedules:
        if schedule.jp_start <= jp <= schedule.jp_end:
            return schedule
    return None


@register.filter
def has_schedule_at_jp(schedules, jp):
    """
    Check if there's any schedule at specific JP
    Usage: {{ schedules|has_schedule_at_jp:jp }}
    """
    if not schedules:
        return False
    
    for schedule in schedules:
        if schedule.jp_start <= jp <= schedule.jp_end:
            return True
    return False
