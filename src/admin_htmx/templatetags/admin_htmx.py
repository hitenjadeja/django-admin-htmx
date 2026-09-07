from django import template
from django.utils.html import format_html

register = template.Library()


@register.simple_tag(takes_context=True)
def admin_htmx_nonce(context):
    """Accept Django's CSP context convention without requiring Django 6."""
    nonce = context.get("csp_nonce")
    return format_html('nonce="{}"', nonce) if nonce is not None else ""
