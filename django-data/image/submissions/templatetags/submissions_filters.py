import ast
from django import template

from common.constants import ACCURACIES

register = template.Library()


@register.filter
def get_dict_from_str(value):
    to_return = list()
    for item in value:
        to_return.append(ast.literal_eval(item))
    return to_return


@register.filter
def getattribute(value, arg):
    if arg == 'birth_location_accuracy':
        return ACCURACIES.get_value_display(getattr(value, arg))
    return getattr(value, arg)


@register.filter
def create_unique_id(value, arg):
    return "{}{}".format(arg, value)


@register.filter
def convert_to_human_readable(value):
    name = dict()
    name['birth_location_latitude'] = 'Birth location latitude'
    name['birth_location_longitude'] = 'Birth location longitude'
    name['birth_location_accuracy'] = 'Birth location accuracy'
    name['birth_location'] = 'Birth location'
    return name[value]