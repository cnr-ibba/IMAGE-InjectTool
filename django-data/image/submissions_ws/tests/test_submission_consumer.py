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
    await communicator.send_to(text_data="hello")
    response = await communicator.receive_from()
    assert response == '{"message": "hello"}'
    await communicator.disconnect()
