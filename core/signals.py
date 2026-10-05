import re
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Profile

User = settings.AUTH_USER_MODEL


def get_user_profile(user):
    try:
        return user.profile
    except (Profile.DoesNotExist, AttributeError):
        email = getattr(user, 'email', '') or ''
        base_username = email.split('@')[0] if email else 'user'
        base_username = re.sub(r'[^a-zA-Z0-9_]', '', base_username) or 'user'
        base_username = base_username.lower()[:30]

        username = base_username
        counter = 1
        while Profile.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        name = base_username.replace('_', ' ').title()
        profile, _ = Profile.objects.get_or_create(
            user=user,
            defaults={'username': username, 'name': name}
        )
        return profile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        get_user_profile(instance)
