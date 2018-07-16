"""

Downloaded from:

https://gist.github.com/czue/90e287c9818ae726f73f5850c1b00f7f

Usage:

{% import json_tags %}

var = myJsObject = {{ template_var|to_json }};

Features:

- Built in support for dates, datetimes, lazy translations.
- Safe escaping of script tags.
- Support for including QuryDict objects.
- Support for custom serialization methods on objects via defining a `to_json()` method.
"""

import datetime
import json
from decimal import Decimal
from django import template
from django.http import QueryDict
from django.utils.encoding import force_str
from django.utils.functional import Promise
from django.utils.safestring import mark_safe

register = template.Library()

ISO_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


def json_handler(obj):
    if callable(getattr(obj, 'to_json', None)):
        return obj.to_json()
    elif isinstance(obj, datetime.datetime):
        return obj.strftime(ISO_DATETIME_FORMAT)
    elif isinstance(obj, datetime.date):
        return obj.isoformat()
    elif isinstance(obj, datetime.time):
        return obj.strftime('%H:%M:%S')
    elif isinstance(obj, Decimal):
        return float(obj)  # warning, potential loss of precision
    elif isinstance(obj, Promise):
        return force_str(obj)  # to support ugettext_lazy
    else:
        return json.JSONEncoder().default(obj)


@register.filter
def to_json(obj):
    def escape_script_tags(unsafe_str):
        # seriously: http://stackoverflow.com/a/1068548/8207
        return unsafe_str.replace('</script>', '<" + "/script>')

    # json.dumps does not properly convert QueryDict array parameter to json
    if isinstance(obj, QueryDict):
        obj = dict(obj)
    return mark_safe(escape_script_tags(json.dumps(obj, default=json_handler)))
