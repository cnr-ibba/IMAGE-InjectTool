import ast
from django import template

from common.constants import ACCURACIES
from image_app.models import Animal, Sample

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
        return value.get_birth_location_accuracy_display()
    elif arg == 'collection_place_accuracy':
        return value.get_collection_place_accuracy_display()
    else:
        return getattr(value, arg)


@register.filter
def create_unique_id(value, arg):
    return "{}{}".format(arg, value)


@register.filter
def convert_to_human_readable(value, record_type):
    if record_type == 'animal':
        return  Animal._meta.get_field(value).verbose_name.title()
    elif record_type == 'sample':
        return  Sample._meta.get_field(value).verbose_name.title()
