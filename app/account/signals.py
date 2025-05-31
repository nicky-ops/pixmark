from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

# Optional: A signal to save the profile when the user is saved,
# though not strictly necessary if Profile is simple or has no save() logic tied to user updates.
# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
# instance.profile.save()
