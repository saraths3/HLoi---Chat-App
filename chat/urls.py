from django.urls import path
from . import views

urlpatterns = [
    path('direct/<uuid:pid>', views.direct_chat_view, name = 'direct_chat_page'),
    path('channels', views.channels_view, name = 'channels_page'),
    path('create/channels', views.channel_creation_view, name='channel_creation_page'),
    path('delete/channel/<int:channel_id>', views.channel_deletion_view,  name='channel_deletion'),
    path('chat/channels/<int:channel_id>', views.channel_chat_view, name='channel_chat_page')
] 
