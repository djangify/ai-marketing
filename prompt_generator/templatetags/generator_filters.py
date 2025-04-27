# prompt_generator/templatetags/generator_filters.py
from django import template

register = template.Library()

@register.filter(name='trim')
def trim(value):
    """Strips leading/trailing whitespace."""
    if value is None:
        return ''
    return str(value).strip()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Gets an item from a dictionary using the key."""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter(name='split_comma')
def split_comma(value):
    """Splits a string by commas."""
    if value is None:
        return []
    return [item for item in value.split(',') if item.strip()]