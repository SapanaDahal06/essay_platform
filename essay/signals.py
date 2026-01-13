# essay/signals.py
from django.db.models.signals import m2m_changed, post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Essay, Notification, UserProfile, User

# Only connect signals if the Essay model has the 'likes' field
@receiver(m2m_changed, sender=Essay.likes.through)
def notify_on_like(sender, instance, action, **kwargs):
    """Send notification when someone likes an essay"""
    if action == "post_add":
        # Get the user who liked (last user in the added list)
        if kwargs.get('pk_set'):
            user_id = list(kwargs['pk_set'])[-1]
            user = User.objects.get(id=user_id)
            
            # Don't notify if user liked their own essay
            if user != instance.author:
                Notification.objects.create(
                    user=instance.author,
                    notification_type='like',
                    title='New Like',
                    message=f"{user.username} liked your essay '{instance.title}'",
                    is_actionable=True
                )

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when a new User is created"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=Essay)
def update_user_streak(sender, instance, created, **kwargs):
    """Update user's streak when they create/update an essay"""
    if created and instance.author:
        try:
            profile = instance.author.profile
            profile.update_streak()
        except UserProfile.DoesNotExist:
            # Create profile if it doesn't exist
            UserProfile.objects.create(user=instance.author)
            instance.author.profile.update_streak() 