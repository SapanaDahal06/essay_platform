# essay/signals.py
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from .models import (
    UserProfile, Essay, Comment, Notification, 
    Competition, CompetitionSubmission, Follow, Bookmark, Badge
)


# ================== UTILITY FUNCTIONS ==================
class LeaderboardCalculator:
    @staticmethod
    def calculate_user_stats(user):
        """Calculate and update user statistics for leaderboard"""
        if not hasattr(user, 'profile'):
            return
        
        profile = user.profile
        # Check if update_stats method exists
        if hasattr(profile, 'update_stats'):
            profile.update_stats()


# ================== USER SIGNALS ==================
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create UserProfile when User is created"""
    if created:
        UserProfile.objects.create(user=instance)
        
        # Send welcome notification
        Notification.objects.create(
            user=instance,
            notification_type='system',
            title='Welcome to WriteVerse! 🎉',
            message='Welcome to our writing community! Start by exploring competitions or writing your first essay.',
            is_important=True
        )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Ensure UserProfile is saved when User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


# ================== ESSAY SIGNALS ==================
@receiver(post_save, sender=Essay)
def update_leaderboard_on_essay_save(sender, instance, created, **kwargs):
    """Update leaderboard when essay is saved"""
    if instance.status in ['published', 'submitted']:
        transaction.on_commit(
            lambda: LeaderboardCalculator.calculate_user_stats(instance.author)
        )


@receiver(post_save, sender=Essay)
def essay_created_notification(sender, instance, created, **kwargs):
    """Send notification when essay is created"""
    if created:
        # Notify essay author
        Notification.objects.create(
            user=instance.author,
            notification_type='essay_published' if instance.status == 'published' else 'system',
            title='Essay Created Successfully! 📝',
            message=f'Your essay "{instance.title[:50]}" has been created.'
        )
        
        # Update user stats
        if instance.author.profile and hasattr(instance.author.profile, 'update_stats'):
            instance.author.profile.update_stats()


@receiver(post_save, sender=Essay)
def essay_published_notification(sender, instance, **kwargs):
    """Send notification when essay status changes to published"""
    if instance.status == 'published':
        # Check if it was just published (published_at is now but wasn't before)
        from django.db.models import F
        Essay.objects.filter(id=instance.id, published_at__isnull=True).update(
            published_at=timezone.now()
        )
        
        # Notify author
        Notification.objects.create(
            user=instance.author,
            notification_type='essay_published',
            title='Essay Published! 🎉',
            message=f'Your essay "{instance.title[:50]}" is now live and visible to the community!',
            is_important=True
        )
        
        # Update user experience - check if methods exist
        if instance.author.profile:
            if hasattr(instance.author.profile, 'add_experience'):
                instance.author.profile.add_experience(100, "Essay published")
            if hasattr(instance.author.profile, 'update_streak'):
                instance.author.profile.update_streak()


@receiver(post_delete, sender=Essay)
def update_leaderboard_on_essay_delete(sender, instance, **kwargs):
    """Update leaderboard when essay is deleted"""
    transaction.on_commit(
        lambda: LeaderboardCalculator.calculate_user_stats(instance.author)
    )


# ================== COMMENT SIGNALS ==================
@receiver(post_save, sender=Comment)
def comment_created_notification(sender, instance, created, **kwargs):
    """Send notification when comment is created"""
    if created and instance.author != instance.essay.author:
        # Notify essay author about new comment
        Notification.objects.create(
            user=instance.essay.author,
            notification_type='comment',
            title='New Comment on Your Essay 💬',
            message=f'{instance.author.username} commented on your essay "{instance.essay.title[:50]}..."'
        )
        
        # Give experience to commenter - check if method exists
        if instance.author.profile and hasattr(instance.author.profile, 'add_experience'):
            instance.author.profile.add_experience(10, "Comment posted")


@receiver(post_save, sender=Comment)
def reply_created_notification(sender, instance, created, **kwargs):
    """Send notification when reply is created"""
    if created and instance.parent and instance.author != instance.parent.author:
        # Notify parent comment author about reply
        Notification.objects.create(
            user=instance.parent.author,
            notification_type='reply',
            title='Reply to Your Comment ↩️',
            message=f'{instance.author.username} replied to your comment'
        )


# ================== LIKE SIGNALS ==================
@receiver(m2m_changed, sender=Essay.likes.through)
def essay_like_notification(sender, instance, action, pk_set, **kwargs):
    """Send notification when essay is liked"""
    if action == 'post_add' and pk_set:
        # Get the user who liked
        from django.contrib.auth.models import User
        liker = User.objects.get(pk=list(pk_set)[0])
        
        # Don't notify if user liked their own essay
        if liker != instance.author:
            Notification.objects.create(
                user=instance.author,
                notification_type='like',
                title='New Like on Your Essay ❤️',
                message=f'{liker.username} liked your essay "{instance.title[:50]}..."'
            )
            
            # Give experience to essay author - check if method exists
            if instance.author.profile and hasattr(instance.author.profile, 'add_experience'):
                instance.author.profile.add_experience(5, "Essay liked")


# ================== COMPETITION SIGNALS ==================
@receiver(post_save, sender=Competition)
def competition_status_changed(sender, instance, **kwargs):
    """Handle competition status changes"""
    if instance.status == 'active' and instance.is_active:
        # Notify all followers of competitions
        from django.db.models import Q
        users = User.objects.filter(
            Q(profile__email_competition_updates=True) |
            Q(profile__email_notifications=True)
        ).distinct()
        
        for user in users:
            Notification.objects.create(
                user=user,
                notification_type='competition_start',
                title='New Competition Started! 🏆',
                message=f'"{instance.title}" competition has started. Submit your entry now!'
            )


@receiver(post_save, sender=CompetitionSubmission)
def update_leaderboard_on_submission(sender, instance, **kwargs):
    """Update leaderboard when submission is scored"""
    if instance.score or instance.rank:
        transaction.on_commit(
            lambda: LeaderboardCalculator.calculate_user_stats(instance.participant)
        )


@receiver(post_save, sender=CompetitionSubmission)
def submission_created_notification(sender, instance, created, **kwargs):
    """Send notification when submission is created"""
    if created:
        # Notify participant
        Notification.objects.create(
            user=instance.participant,
            notification_type='system',
            title='Submission Received 📤',
            message=f'Your submission for "{instance.competition.title}" has been received.'
        )
        
        # Notify competition organizer
        if instance.competition.organizer != instance.participant:
            Notification.objects.create(
                user=instance.competition.organizer,
                notification_type='system',
                title='New Competition Submission',
                message=f'{instance.participant.username} submitted an entry to "{instance.competition.title}".'
            )


@receiver(post_save, sender=CompetitionSubmission)
def submission_judged_notification(sender, instance, **kwargs):
    """Send notification when submission is judged"""
    if instance.score is not None and instance.rank is not None:
        if instance.rank <= 3:  # Top 3 winners
            Notification.objects.create(
                user=instance.participant,
                notification_type='competition_result',
                title=f'🏅 You Won #{instance.rank} Place!',
                message=f'Congratulations! You ranked #{instance.rank} in "{instance.competition.title}"!',
                is_important=True
            )
            # Give bonus experience for winning - check if method exists
            bonus_xp = {1: 500, 2: 300, 3: 200}.get(instance.rank, 0)
            if instance.participant.profile and hasattr(instance.participant.profile, 'add_experience'):
                instance.participant.profile.add_experience(bonus_xp, f"Competition rank #{instance.rank}")
        else:
            Notification.objects.create(
                user=instance.participant,
                notification_type='competition_result',
                title='Competition Results Are In! 📊',
                message=f'Results for "{instance.competition.title}" are available. You ranked #{instance.rank}.'
            )
        
        # Give experience for participation - check if method exists
        if instance.participant.profile and hasattr(instance.participant.profile, 'add_experience'):
            instance.participant.profile.add_experience(50, "Competition participation")


# ================== FOLLOW SIGNALS ==================
@receiver(post_save, sender=Follow)
def follow_created_notification(sender, instance, created, **kwargs):
    """Send notification when user is followed"""
    if created:
        Notification.objects.create(
            user=instance.following,
            notification_type='follow',
            title='New Follower 👤',
            message=f'{instance.follower.username} started following you.',
            is_actionable=True
        )
        
        # Give experience to follower - check if method exists
        if instance.follower.profile and hasattr(instance.follower.profile, 'add_experience'):
            instance.follower.profile.add_experience(5, "Started following someone")


# ================== BOOKMARK SIGNALS ==================
@receiver(post_save, sender=Bookmark)
def bookmark_created_signal(sender, instance, created, **kwargs):
    """Update essay bookmark count"""
    if created:
        instance.essay.bookmarks.add(instance.user)


@receiver(post_delete, sender=Bookmark)
def bookmark_deleted_signal(sender, instance, **kwargs):
    """Update essay bookmark count when removed"""
    instance.essay.bookmarks.remove(instance.user)


# ================== UPDATE STATS SIGNALS ==================
@receiver(post_save, sender=Essay)
def update_user_stats_on_essay(sender, instance, **kwargs):
    """Update user stats when essay is saved"""
    if instance.author and hasattr(instance.author, 'profile') and hasattr(instance.author.profile, 'update_stats'):
        instance.author.profile.update_stats()


@receiver(post_delete, sender=Essay)
def update_user_stats_on_essay_delete(sender, instance, **kwargs):
    """Update user stats when essay is deleted"""
    if instance.author and hasattr(instance.author, 'profile') and hasattr(instance.author.profile, 'update_stats'):
        instance.author.profile.update_stats()


# ================== BADGE AWARDING SIGNALS ==================
@receiver(post_save, sender=UserProfile)
def check_badge_achievements(sender, instance, **kwargs):
    """Check and award badges based on user achievements"""
    
    # FIX: Get essays_published count dynamically instead of from UserProfile field
    from django.db.models import Count, Q
    essays_published_count = Essay.objects.filter(
        author=instance.user, 
        status='published'
    ).count()
    
    # FIX: Safely check for badges field
    has_badges_field = hasattr(instance, 'badges')
    
    # Essay count badges
    if essays_published_count >= 10:
        badge, created = Badge.objects.get_or_create(
            name='Prolific Writer',
            badge_type='essays',
            requirement_value=10,
            defaults={
                'description': 'Published 10 essays',
                'icon': 'fas fa-pen-fancy',
                'color': '#4CAF50',
                'level': 1
            }
        )
        if created or (has_badges_field and badge not in instance.badges.all()):
            if has_badges_field:
                instance.badges.add(badge)
            
            Notification.objects.create(
                user=instance.user,
                notification_type='achievement',
                title='🏆 Badge Earned: Prolific Writer',
                message='Congratulations! You published 10 essays and earned the Prolific Writer badge!',
                is_important=True
            )
    
    # FIX: Safely check for streak_days field
    streak_days = getattr(instance, 'streak_days', 0)
    if streak_days >= 7:
        badge, created = Badge.objects.get_or_create(
            name='Weekly Warrior',
            badge_type='streak',
            requirement_value=7,
            defaults={
                'description': '7-day writing streak',
                'icon': 'fas fa-fire',
                'color': '#FF9800',
                'level': 1
            }
        )
        if created or (has_badges_field and badge not in instance.badges.all()):
            if has_badges_field:
                instance.badges.add(badge)
    
    # FIX: Safely check for level field
    user_level = getattr(instance, 'level', 0)
    if user_level >= 5:
        badge, created = Badge.objects.get_or_create(
            name='Seasoned Writer',
            badge_type='score',
            requirement_value=5,
            defaults={
                'description': 'Reached Level 5',
                'icon': 'fas fa-star',
                'color': '#FFD700',
                'level': 2
            }
        )
        if created or (has_badges_field and badge not in instance.badges.all()):
            if has_badges_field:
                instance.badges.add(badge)
    
    # Competition badges (check if user has won any competitions)
    competition_wins = CompetitionSubmission.objects.filter(
        participant=instance.user,
        rank=1,
        won_prize=True
    ).count()
    
    if competition_wins >= 1:
        badge, created = Badge.objects.get_or_create(
            name='Champion',
            badge_type='competition',
            requirement_value=1,
            defaults={
                'description': 'Won a competition',
                'icon': 'fas fa-trophy',
                'color': '#FF6B6B',
                'level': 3
            }
        )
        if created or (has_badges_field and badge not in instance.badges.all()):
            if has_badges_field:
                instance.badges.add(badge)


# ================== BADGE UNLOCK SIGNALS ==================
@receiver(post_save, sender=Badge)
def notify_badge_unlock(sender, instance, created, **kwargs):
    """Notify users when a new badge is created that they might have earned"""
    if created:
        # Find all users who meet the requirement
        if instance.badge_type == 'essays':
            # Get users with published essays count >= requirement
            users = []
            for profile in UserProfile.objects.all():
                essays_count = Essay.objects.filter(
                    author=profile.user, 
                    status='published'
                ).count()
                if essays_count >= instance.requirement_value:
                    users.append(profile)
            
        elif instance.badge_type == 'streak':
            # Safely check for streak_days field
            users = []
            if hasattr(UserProfile, 'streak_days'):
                users = UserProfile.objects.filter(
                    streak_days__gte=instance.requirement_value
                )
            
        elif instance.badge_type == 'score':
            # Safely check for level field
            users = []
            if hasattr(UserProfile, 'level'):
                users = UserProfile.objects.filter(level__gte=instance.requirement_value)
                
        elif instance.badge_type == 'competition':
            # More complex query for competition wins
            users = UserProfile.objects.none()  # Will be handled by competition signals
        else:
            users = UserProfile.objects.none()
        
        for profile in users:
            # Safely check if badges field exists
            has_badges = hasattr(profile, 'badges')
            badge_already_has = False
            
            if has_badges:
                badge_already_has = instance in profile.badges.all()
            
            if not badge_already_has:
                if has_badges:
                    profile.badges.add(instance)
                
                Notification.objects.create(
                    user=profile.user,
                    notification_type='achievement',
                    title=f'🏆 Badge Unlocked: {instance.name}',
                    message=f'You have earned the "{instance.name}" badge!',
                    is_important=True
                )


# ================== PREVENT DUPLICATE SIGNALS ==================
@receiver(post_save, sender=Notification)
def prevent_duplicate_notifications(sender, instance, created, **kwargs):
    """Prevent duplicate notifications within short time frame"""
    if created:
        from django.utils import timezone
        from datetime import timedelta
        
        # Check for similar recent notifications
        recent_notifications = Notification.objects.filter(
            user=instance.user,
            notification_type=instance.notification_type,
            created_at__gte=timezone.now() - timedelta(minutes=5)
        )
        
        # If similar notification exists within 5 minutes, delete this one
        if recent_notifications.count() > 1:
            # Keep the first one, delete others
            recent_notifications.exclude(id=recent_notifications.first().id).delete()