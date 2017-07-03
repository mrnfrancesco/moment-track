from urlparse import urljoin

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from moment_track import settings

register = template.Library()


@register.filter(name='flag', needs_autoescape=True)
@stringfilter
def flag(value, autoescape=True):
    """Return the HTML img tag for the flag icon of the specified language if any"""
    if autoescape:
        escape = conditional_escape
    else:
        escape = lambda x: x

    img = '<img src="{uri}"/>'.format(
        uri=escape(
            urljoin(
                settings.STATIC_URL,
                'dashboard/img/flags/{language}.gif'.format(
                    language=value.lower()
                )
            )
        )
    )
    return mark_safe(img)
