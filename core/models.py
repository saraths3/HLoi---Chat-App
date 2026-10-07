import os
from uuid import uuid4
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from cloudinary_storage.storage import MediaCloudinaryStorage

User = settings.AUTH_USER_MODEL


class Profile(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(storage = MediaCloudinaryStorage() ,upload_to='Profile/', blank=True, null=True)
    username = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        email = getattr(self.user, 'email', None)
        if email:
            return f'{email}: {self.username}'
        else:
            return self.username

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'
        ordering = ['username']


class Friendship(models.Model):
    sender_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='sent_friendships')
    reciever_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='recieved_friendships')
    STATUS = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ]
    status = models.CharField(max_length=100, choices=STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
             models.UniqueConstraint(
                 fields=['sender_profile', 'reciever_profile'],
                 name='unique_friendship_request',
             )
        ]
        ordering = ['-created_at']

    @property
    def sender(self):
        return self.sender_profile

    @property
    def receiver(self):
        return self.reciever_profile

    @property
    def receiver_profile(self):
        return self.reciever_profile

    def clean(self):
        if self.reciever_profile_id == self.sender_profile_id:
            raise ValidationError('You cannot send a friend request to yourself.')
        
        reverse_exists = Friendship.objects.filter(
            sender_profile_id=self.reciever_profile_id,
            reciever_profile_id=self.sender_profile_id
        ).exclude(pk=self.pk).exists()

        if reverse_exists:
            raise ValidationError('A friendship request between these profiles already exists.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.sender_profile}: {self.reciever_profile}'
    