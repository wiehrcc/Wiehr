from django import template
from django.templatetags.static import static
from django.conf import settings

register = template.Library()

@register.simple_tag
def static_version(path):
    static_url = static(path)
    version = getattr(settings, 'STATIC_VERSION', '1')
    return f"{static_url}?v={version}"

@register.filter
def add_version(value):
    version = getattr(settings, 'STATIC_VERSION', '1')
    return f"{value}?v={version}"
