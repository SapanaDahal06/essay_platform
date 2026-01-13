# essay/models.py - CLEAN VERSION
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import uuid
from django.utils.text import Truncator
import re
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta

# ================== LANGUAGE MODEL ==================
class Language(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


# ================== BADGE MODEL ==================
class Badge(models.Model):
    BADGE_TYPES = [
        ('essays', 'Essay Writing'),
        ('likes', 'Popularity'),
        ('score', 'Quality'),
        ('competition', 'Competitions'),
        ('streak', 'Consistency'),
        ('community', 'Community'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, help_text="FontAwesome icon class")
    color = models.CharField(max_length=20, default='#FFD700')
    badge_type = models.CharField(max_length=50, choices=BADGE_TYPES)
    requirement_value = models.IntegerField(help_text="Value needed to earn this badge")
    level = models.IntegerField(default=1, help_text="Badge level (1-5)")
    
    class Meta:
        ordering = ['level', 'badge_type']
    
    def __str__(self):
        return f"{self.name} (Level {self.level})"


# ================== ESSAY MODEL ==================
class Essay(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted for Review'),
        ('published', 'Published'),
        ('rejected', 'Rejected'),
        ('archived', 'Archived'),
    ]
    
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('education', 'Education'),
        ('technology', 'Technology'),
        ('environment', 'Environment'),
        ('science', 'Science'),
        ('literature', 'Literature'),
        ('creative', 'Creative Writing'),
        ('argumentative', 'Argumentative'),
        ('narrative', 'Narrative'),
        ('descriptive', 'Descriptive'),
    ]
    
    EMOJI_FEEDBACK_CHOICES = [
        ('🌟', '🌟 Excellent - Outstanding work!'),
        ('👍', '👍 Good - Well done!'),
        ('✅', '✅ Satisfactory - Meets expectations'),
        ('📝', '📝 Needs Improvement - Some areas to work on'),
        ('💡', '💡 Creative - Great ideas!'),
        ('🚀', '🚀 Impressive - Above and beyond'),
        ('🎯', '🎯 On Target - Meets all requirements'),
        ('🔥', '🔥 Amazing work!'),
        ('💫', '💫 Exceptional effort'),
        ('✨', '✨ Well crafted'),
    ]
    
    GRAMMAR_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('checked', 'Checked'),
        ('needs_review', 'Needs Review'),
        ('auto_approved', 'Auto Approved'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    content = models.TextField()
    formatted_content = models.TextField(blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='essays')
    primary_language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Basic counts
    word_count = models.IntegerField(default=0)
    character_count = models.IntegerField(default=0)
    sentence_count = models.IntegerField(default=0)
    paragraph_count = models.IntegerField(default=0)
    
    # Emoji feedback
    emoji_feedback = models.CharField(
        max_length=5,
        choices=EMOJI_FEEDBACK_CHOICES,
        blank=True,
        null=True,
        help_text="Overall feedback emoji"
    )
    
    views = models.IntegerField(default=0)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_essays', blank=True)
    bookmarks = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='bookmarked_essays', blank=True)
    
    # Admin review fields
    is_reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_essays'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Grammar and spelling feedback
    grammar_errors = models.TextField(blank=True)
    spelling_errors = models.TextField(blank=True)
    vocabulary_suggestions = models.TextField(blank=True)
    
    # Verification status
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_essays'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # NEW GRAMMAR CHECKING FIELDS
    grammar_status = models.CharField(
        max_length=20,
        choices=GRAMMAR_STATUS_CHOICES,
        default='pending'
    )
    
    grammar_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Grammar score from 0-100"
    )
    
    grammar_checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checked_essays'
    )
    
    grammar_checked_at = models.DateTimeField(null=True, blank=True)
    
    grammar_notes = models.TextField(blank=True, help_text="Admin notes on grammar issues")
    
    requires_grammar_check = models.BooleanField(
        default=False,
        help_text="User requested grammar check"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Essays'
    
    def __str__(self):
        return self.title
    
    def calculate_basic_counts(self):
        """Calculate word, character, sentence, and paragraph counts"""
        words = [word for word in self.content.split() if word.strip()]
        self.word_count = len(words)
        self.character_count = len(self.content)
        sentences = re.split(r'[.!?]+', self.content)
        self.sentence_count = len([s for s in sentences if s.strip()])
        paragraphs = [p for p in self.content.split('\n\n') if p.strip()]
        self.paragraph_count = len(paragraphs)
        return {
            'words': self.word_count,
            'characters': self.character_count,
            'sentences': self.sentence_count,
            'paragraphs': self.paragraph_count
        }
    
    def save(self, *args, **kwargs):
        if self.content:
            self.calculate_basic_counts()
        
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def likes_count(self):
        return self.likes.count()
    
    @property
    def bookmarks_count(self):
        return self.bookmarks.count()
    
    @property
    def reading_time_minutes(self):
        return max(1, self.word_count // 200)
    
    def get_grammar_status_color(self):
        colors = {
            'pending': 'warning',
            'checked': 'success',
            'needs_review': 'danger',
            'auto_approved': 'info'
        }
        return colors.get(self.grammar_status, 'secondary')


# ================== GRAMMAR CHECK MODEL ==================
class GrammarCheck(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    essay = models.ForeignKey(
        Essay, 
        on_delete=models.CASCADE,
        related_name='grammar_checks'
    )
    
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    
    checked_at = models.DateTimeField(auto_now_add=True)
    
    score = models.DecimalField(max_digits=5, decimal_places=2)
    
    issues_found = models.IntegerField(default=0)
    
    # Store detailed issues as JSON
    issues_data = models.JSONField(default=dict, blank=True)
    
    # Store suggestions/comments
    suggestions = models.TextField(blank=True)
    
    automated_check = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-checked_at']
    
    def __str__(self):
        return f"Grammar check for {self.essay.title} - Score: {self.score}"


# ================== COMMENT MODEL ==================
class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    essay = models.ForeignKey(Essay, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.author.username}"


# ================== USER PROFILE MODEL ==================
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Administrator'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/%Y/%m/', null=True, blank=True, default='profile_pictures/default.png')
    
    # Experience and level
    experience_points = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    
    # Streak
    streak_days = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    
    # Badges
    badges = models.ManyToManyField('Badge', related_name='users', blank=True)
    
    # Email preferences
    email_notifications = models.BooleanField(default=True)
    email_competition_updates = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def add_experience(self, points, reason=""):
        """Add experience points to user"""
        self.experience_points += points
        
        # Calculate level based on experience (1000 points per level)
        new_level = self.experience_points // 1000 + 1
        if new_level > self.level:
            self.level = new_level
        
        self.save()
    
    def update_streak(self):
        """Update user's writing streak"""
        today = timezone.now().date()
        
        if self.last_activity_date:
            days_diff = (today - self.last_activity_date).days
            
            if days_diff == 1:
                # Consecutive day
                self.streak_days += 1
            elif days_diff > 1:
                # Broken streak
                self.streak_days = 1
        else:
            # First activity
            self.streak_days = 1
        
        self.last_activity_date = today
        self.save()


# ================== REVIEW TEMPLATE MODEL ==================
class ReviewTemplate(models.Model):
    CATEGORY_CHOICES = [
        ('grammar', 'Grammar'),
        ('spelling', 'Spelling'),
        ('structure', 'Structure'),
        ('content', 'Content'),
        ('vocabulary', 'Vocabulary'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    example = models.TextField(blank=True)
    correction = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category']
    
    def __str__(self):
        return f"{self.category}: {self.title}"


# ================== NOTIFICATION MODEL ==================
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('comment', 'New Comment'),
        ('like', 'New Like'),
        ('system', 'System Notification'),
        ('achievement', 'Achievement Unloaded'),
        ('essay_published', 'Essay Published'),
        ('reply', 'Reply to Comment'),
        ('competition_start', 'Competition Started'),
        ('competition_result', 'Competition Result'),
        ('follow', 'New Follower'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    is_important = models.BooleanField(default=False)
    is_actionable = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    class Meta:
        ordering = ['-created_at']


# ================== PARAGRAPH MODEL ==================
class Paragraph(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    essay = models.ForeignKey(Essay, on_delete=models.CASCADE, related_name='paragraphs')
    paragraph_number = models.IntegerField()
    content = models.TextField()
    word_count = models.IntegerField(default=0)
    character_count = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['paragraph_number']
        unique_together = ['essay', 'paragraph_number']
    
    def __str__(self):
        return f"Paragraph {self.paragraph_number} of '{self.essay.title[:20]}...'"


# ================== COMPETITION MODEL ==================
class Competition(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('active', 'Active'),
        ('judging', 'Judging'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    theme = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=Essay.CATEGORY_CHOICES, default='general')
    word_limit_min = models.IntegerField(default=300)
    word_limit_max = models.IntegerField(default=1500)
    time_limit_minutes = models.IntegerField(default=60)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    is_active = models.BooleanField(default=True)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_competitions')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class CompetitionSubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='submissions')
    participant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='competition_submissions')
    essay = models.ForeignKey(Essay, on_delete=models.CASCADE, related_name='competition_submissions')
    score = models.FloatField(null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    won_prize = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"Submission by {self.participant.username}"


# ================== FOLLOW MODEL ==================
class Follow(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following_set')
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='followers_set')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['follower', 'following']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


# ================== BOOKMARK MODEL ==================
class Bookmark(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookmark_set')
    essay = models.ForeignKey(Essay, on_delete=models.CASCADE, related_name='bookmark_set')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['user', 'essay']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} bookmarked {self.essay.title}"


# ================== CHALLENGE MODELS ==================
class TimedChallenge(models.Model):
    DURATION_CHOICES = [
        (15, '15 Minutes - Sprint'),
        (30, '30 Minutes - Quick Write'),
        (60, '60 Minutes - Standard'),
        (120, '2 Hours - Extended'),
        (180, '3 Hours - Marathon'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    prompt = models.TextField(help_text="The writing prompt for this challenge")
    duration_minutes = models.IntegerField(choices=DURATION_CHOICES, default=30)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='medium')
    min_words = models.IntegerField(default=300)
    max_words = models.IntegerField(default=1000)
    points_reward = models.IntegerField(default=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_timed_challenges')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.duration_minutes} min)"


class TimedChallengeSubmission(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    challenge = models.ForeignKey(TimedChallenge, on_delete=models.CASCADE, related_name='submissions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='timed_submissions')
    content = models.TextField(blank=True)
    word_count = models.IntegerField(default=0)
    time_spent_seconds = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    points_earned = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-started_at']
        unique_together = ['challenge', 'user', 'started_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.challenge.title}"


class CharacterChallenge(models.Model):
    LIMIT_CHOICES = [
        (100, '100 Characters - Micro'),
        (280, '280 Characters - Tweet'),
        (500, '500 Characters - Flash'),
        (1000, '1000 Characters - Short'),
        (2000, '2000 Characters - Medium'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    prompt = models.TextField()
    character_limit = models.IntegerField(choices=LIMIT_CHOICES, default=280)
    allow_over_limit = models.BooleanField(default=False)
    points_reward = models.IntegerField(default=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_character_challenges')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.character_limit} chars)"


class CharacterChallengeSubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    challenge = models.ForeignKey(CharacterChallenge, on_delete=models.CASCADE, related_name='submissions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='character_submissions')
    content = models.TextField()
    character_count = models.IntegerField(default=0)
    word_count = models.IntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)
    points_earned = models.IntegerField(default=0)
    is_valid = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['challenge', 'user']
    
    def __str__(self):
        return f"{self.user.username} - {self.challenge.title}"


class AIWritingSession(models.Model):
    SUGGESTION_TYPES = [
        ('improve', 'Improve Text'),
        ('expand', 'Expand Content'),
        ('summarize', 'Summarize'),
        ('rephrase', 'Rephrase'),
        ('grammar', 'Grammar Check'),
        ('tone', 'Adjust Tone'),
        ('creative', 'Creative Suggestions'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_sessions')
    essay = models.ForeignKey(Essay, on_delete=models.CASCADE, null=True, blank=True, related_name='ai_sessions')
    suggestion_type = models.CharField(max_length=20, choices=SUGGESTION_TYPES)
    original_text = models.TextField()
    ai_suggestion = models.TextField()
    was_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.suggestion_type}"


class ChallengeLeaderboard(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='challenge_stats')
    total_challenges_completed = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    timed_challenges_completed = models.IntegerField(default=0)
    character_challenges_completed = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    last_challenge_date = models.DateField(null=True, blank=True)
    rank = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-total_points', '-total_challenges_completed']
    
    def __str__(self):
        return f"{self.user.username} - {self.total_points} points"