import json
import pytest
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.conf.urls import url
from ..consumers import SubmissionsConsumer


@pytest.mark.asyncio
async def test_submissions_consumer():
    application = URLRouter([
        url(r'^image/ws/submissions/(?P<submission_key>[^/]+)/$',
            SubmissionsConsumer),
    ])
    communicator = WebsocketCommunicator(application,
                                         "/image/ws/submissions/test/")
    connected, subprotocol = await communicator.connect()
    assert connected
    test_message = {
        'message': 'hello',
        'notification_message': 'notification'
    }
    await communicator.send_to(text_data=json.dumps(test_message))
    response = await communicator.receive_from()
    assert response == '{"message": "hello", ' \
                       '"notification_message": "notification", ' \
                       '"validation_message": ""}'
    await communicator.disconnect()
