#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 27 11:52:37 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import asyncio
import re

from import_export import resources

from common.constants import STATUSES
from common.helpers import send_message_to_websocket
from uid.models import Animal, Sample


def send_message(submission_obj, validation_message=None):
    """
    Update submission.status and submission message using django
    channels

    Args:
        submission_obj (uid.models.Submission): an UID submission
            object
        validation_message (dict): set validation message
    """

    # define a message to send
    message = {
        'message': STATUSES.get_value_display(submission_obj.status),
        'notification_message': submission_obj.message,
    }

    # if validation message is needed, add to the final message
    if validation_message:
        message['validation_message'] = validation_message

    # now send the message to its submission
    asyncio.get_event_loop().run_until_complete(
        send_message_to_websocket(
            message,
            submission_obj.pk
        )
    )


def is_target_in_message(target, messages):
    """
    This function will return true if target in message

    Args:
        target (str): target to search
    """
    for message in messages:
        if re.search(message, target):
            return True
    return False


# to export data with django-import-export library
class AnimalResource(resources.ModelResource):
    class Meta:
        model = Animal
        fields = (
            'id',
            'name',
            'biosample_id',
            'material',
            'status',
            'last_changed',
            'last_submitted'
        )

        export_order = fields

    def dehydrate_status(self, animal):
        """Convert a numeric status field into the displayed column"""

        return STATUSES.get_value_display(animal.status)


class SampleResource(resources.ModelResource):
    class Meta:
        model = Sample
        fields = (
            'id',
            'name',
            'biosample_id',
            'material',
            'status',
            'last_changed',
            'last_submitted'
        )

        export_order = fields

    def dehydrate_status(self, sample):
        """Convert a numeric status field into the displayed column"""

        return STATUSES.get_value_display(sample.status)
