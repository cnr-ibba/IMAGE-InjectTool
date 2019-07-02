import ast
from django import template

register = template.Library()


@register.filter
def get_dict_from_str(value):
    to_return = list()
    for item in value:
        to_return.append(ast.literal_eval(item))
    return to_return


@register.filter
def get_str_from_list(value):
    return ','.join(str(item) for item in value)
