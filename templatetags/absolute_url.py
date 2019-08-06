from django import template
from django.conf import settings
from django.urls import reverse

register = template.Library()


@register.simple_tag
def absolute_url(view_name, *args, **kwargs):
    return settings.BASE_URL + reverse(view_name, args=args, kwargs=kwargs)
