# essay/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from .models import Essay, Submission
from .utils import LeaderboardCalculator

@receiver(post_save, sender=Essay)
def update_leaderboard_on_essay_save(sender, instance, created, **kwargs):
    """Update leaderboard when essay is saved"""
    if instance.status in ['published', 'submitted']:
        transaction.on_commit(
            lambda: LeaderboardCalculator.calculate_user_stats(instance.author)
        )

@receiver(post_save, sender=Submission)
def update_leaderboard_on_submission(sender, instance, **kwargs):
    """Update leaderboard when submission is scored"""
    if instance.score or instance.rank:
        transaction.on_commit(
            lambda: LeaderboardCalculator.calculate_user_stats(instance.submitted_by)
        )

@receiver(post_delete, sender=Essay)
def update_leaderboard_on_essay_delete(sender, instance, **kwargs):
    """Update leaderboard when essay is deleted"""
    transaction.on_commit(
        lambda: LeaderboardCalculator.calculate_user_stats(instance.author)
    )