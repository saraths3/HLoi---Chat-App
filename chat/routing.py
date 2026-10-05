from django.urls import path
from .consumers import DirectChatConsumer, ChannelChatConsumer


websocket_urlpatterns = [
    path('ws/chat/direct/<uuid:pid>/', DirectChatConsumer.as_asgi()),
    path('ws/chat/channels/<int:channel_id>/', ChannelChatConsumer.as_asgi()),
]