from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/coordination/(?P<meeting_id>\w+)/$', consumers.CoordinationConsumer.as_asgi()),
]