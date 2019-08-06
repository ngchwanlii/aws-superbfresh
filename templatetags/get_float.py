from math import ceil

from django import template

register = template.Library()


@register.simple_tag
def get_float(goods_total_price):
    x = float(goods_total_price)
    x = ceil(x * 100.0) / 100.0
    x = float("{0:.2f}".format(x))
    return x
