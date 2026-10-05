import json
from core.models import Profile
from chat.models import Conversation, Message
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

class DirectChatConsumer(AsyncWebsocketConsumer):

    @database_sync_to_async
    def get_user_profile(self, user):
        try: return Profile.objects.get(user=user)
        except Profile.DoesNotExist: return None

    @database_sync_to_async
    def get_profile(self, pid):
        try: return Profile.objects.get(id=pid)
        except Profile.DoesNotExist: return None

    @database_sync_to_async
    def get_conversation(self, user_profile, other_profile):
        conversation = Conversation.objects.filter(type='direct', profiles=user_profile).filter(profiles=other_profile).first()
        if not conversation:
            conversation = Conversation.objects.create(type='direct')
            conversation.profiles.add(user_profile, other_profile)
        return conversation

    @database_sync_to_async
    def save_message(self, content):
        return Message.objects.create(conversation=self.conversation, sender=self.user_profile, content=content)

    async def chat_message(self, event):
        # Convert user_profile.id to string for reliable comparison
        is_outgoing = (event['sender_id'] == str(self.user_profile.id))
        msg_class = 'outgoing' if is_outgoing else 'incoming'
        html = f'<div id="messages" hx-swap-oob="beforeend"><div class="message-bubble {msg_class}"><div class="bubble-content"><p class="message-text">{event["message"]}</p><span class="message-timestamp">{event["timestamp"]}</span></div></div></div>'
        await self.send(text_data=html)

    async def connect(self):
        user = self.scope.get('user')
        if not user or user.is_anonymous: await self.close(); return
        pid = self.scope['url_route']['kwargs']['pid']
        self.user_profile = await self.get_user_profile(user)
        self.other_profile = await self.get_profile(pid)
        if not self.user_profile or not self.other_profile: await self.close(); return
        self.conversation = await self.get_conversation(self.user_profile, self.other_profile)
        self.group_name = f'conversation_{self.conversation.id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        content = data.get('content')
        if not content or not content.strip(): return
        message = await self.save_message(content)
        # CHANGED: Convert sender_id UUID to string
        await self.channel_layer.group_send(self.group_name, {
            'type': 'chat_message',
            'message': message.content,
            'sender_id': str(self.user_profile.id),
            'timestamp': message.updated_at.strftime('%I:%M %p')
        })

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'): await self.channel_layer.group_discard(self.group_name, self.channel_name)


class ChannelChatConsumer(AsyncWebsocketConsumer):

    @database_sync_to_async
    def get_user_profile(self, user):
        try:
            return Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            return None

    @database_sync_to_async
    def get_channel(self, channel_id):
        try:
            return Conversation.objects.get(id=channel_id, type='channels')
        except Conversation.DoesNotExist:
            return None

    @database_sync_to_async
    def check_channel_member(self, channel, user_profile):
        return channel.profiles.filter(id=user_profile.id).exists()

    @database_sync_to_async
    def save_message(self, content):
        return Message.objects.create(conversation=self.channel, content=content, sender=self.user_profile)

    async def chat_message(self, event):
        message = event['message']
        sender_id = event['sender_id']
        sender_username = event['sender_username']
        created_at = event['created_at']
        
        # Parse ISO string format back to local timezone time
        try:
            dt = timezone.datetime.fromisoformat(created_at)
            formatted_time = timezone.localtime(dt).strftime("%I:%M %p")
        except (ValueError, TypeError):
            formatted_time = str(created_at)

        html = (
                f'<div id="messages" hx-swap-oob="beforeend">'
                f'  <div class="message-card">'
                f'    <div class="message-header">'
                f'      <span class="username">@{sender_username}</span>'
                f'      <span class="timestamp">{formatted_time}</span>'
                f'    </div>'
                f'    <div class="message-body" data-sender-id="{sender_id}">{message}</div>'
                f'  </div>'
                f'</div>'
            )
        await self.send(text_data=html)

    async def connect(self):
        print('Connected')
        self.User = self.scope.get('user')
        self.user_profile = await self.get_user_profile(user=self.User)
        self.channel_id = self.scope['url_route']['kwargs']['channel_id']
        self.channel = await self.get_channel(channel_id=self.channel_id)
        self.is_member = await self.check_channel_member(self.channel, self.user_profile)

        if not self.is_member:
            await self.close()
            return
        
        self.group_name = f'channel_{self.channel_id}'

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        try:
            content = data.get('content').strip()
        except AttributeError:
            return
        message = await self.save_message(content)
 
        # CHANGED: Convert UUID and datetime objects to strings
        await self.channel_layer.group_send(self.group_name, {
            'type': 'chat_message',
            'message': message.content,
            'sender_id': str(self.user_profile.id),
            'sender_username': self.user_profile.username,
            'created_at': message.created_at.isoformat(),
        })

    async def disconnect(self, code):
        print('Disconnected')