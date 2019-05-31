from django.conf.urls import url

from . import consumers

websocket_urlpatterns = [
    url(r'^image/ws/submissions/(?P<submission_key>[^/]+)/$',
        consumers.SubmissionsConsumer),
]