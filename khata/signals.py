from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone
from django.dispatch import receiver
from .models import Profile




@receiver(user_logged_in)
def on_user_login(sender, request, user, **kwargs):
    profile, created = Profile.objects.get_or_create(user=user)
    profile.is_online = True
    profile.last_seen = timezone.now()
    profile.save()

@receiver(user_logged_out)
def on_user_logout(sender, request, user, **kwargs):
    profile, created = Profile.objects.get_or_create(user=user)
    profile.is_online = False
    profile.last_seen = timezone.now()
    profile.save()
