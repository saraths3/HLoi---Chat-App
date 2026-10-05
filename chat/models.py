from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL
class Conversation(models.Model):
    name = models.CharField(max_length=100, blank=True, default='')
    profiles = models.ManyToManyField('core.Profile', related_name='conversations')
    admin = models.ForeignKey('core.Profile', on_delete=models.CASCADE, related_name='admin_channels', null=True)
    TYPE = [
        ('direct', 'direct'),
        ('channels', 'channels')
    ]
    type = models.CharField(max_length=200, choices=TYPE, default='direct')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        profile_names = ', '.join(
            profile.name or profile.username for profile in self.profiles.all()
        )
        return profile_names if profile_names else f'Conversation {self.pk} '

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey('core.Profile', on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        sender_name = self.sender.name or self.sender.username
        return f'{sender_name}: {self.content[:30]}'