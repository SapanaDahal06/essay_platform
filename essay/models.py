from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import uuid
from django.utils.text import Truncator
import re
from django.db.models import Count
from django.utils import timezone

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
    """Achievement badges for users"""
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
    
    WRITING_MODES = [
        ('normal', 'Normal Mode'),
        ('paragraph', 'Paragraph Mode'),
        ('timed', 'Timed Writing'),
        ('collaborative', 'Collaborative'),
    ]
    
    DIFFICULTY_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    # Emoji feedback choices
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
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    content = models.TextField()
    formatted_content = models.TextField(blank=True)
    abstract = models.TextField(blank=True, help_text="Brief summary of the essay")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='essays')
    primary_language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    writing_mode = models.CharField(max_length=20, choices=WRITING_MODES, default='paragraph')
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS, default='intermediate')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_public = models.BooleanField(default=True)
    allow_comments = models.BooleanField(default=True)
    allow_sharing = models.BooleanField(default=True)
    
    # Basic counts (for info only)
    word_count = models.IntegerField(default=0)
    character_count = models.IntegerField(default=0)
    sentence_count = models.IntegerField(default=0)
    paragraph_count = models.IntegerField(default=0)
    
    # Emoji feedback (instead of grades)
    emoji_feedback = models.CharField(
        max_length=5,
        choices=EMOJI_FEEDBACK_CHOICES,
        blank=True,
        null=True,
        help_text="Overall feedback emoji"
    )
    
    views = models.IntegerField(default=0)
    unique_views = models.IntegerField(default=0)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_essays', blank=True)
    bookmarks = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='bookmarked_essays', blank=True)
    shares = models.IntegerField(default=0)
    writing_time_minutes = models.IntegerField(default=0)
    average_wpm = models.FloatField(default=0)
    revisions_count = models.IntegerField(default=0)
    pdf_file = models.FileField(upload_to='essays/pdfs/%Y/%m/', null=True, blank=True)
    pdf_generated_at = models.DateTimeField(null=True, blank=True)
    pdf_size_kb = models.IntegerField(default=0)
    meta_description = models.CharField(max_length=300, blank=True)
    meta_keywords = models.CharField(max_length=500, blank=True)
    canonical_url = models.URLField(blank=True)
    
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
    
    # Structure feedback
    structure_comments = models.TextField(blank=True)
    content_feedback = models.TextField(blank=True)
    
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
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Essays'
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['author', 'created_at']),
            models.Index(fields=['category', 'created_at']),
        ]
    
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
    
    def mark_as_reviewed(self, reviewer, feedback_data=None):
        """Mark essay as reviewed by admin"""
        self.is_reviewed = True
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        
        if feedback_data:
            for field, value in feedback_data.items():
                if hasattr(self, field):
                    setattr(self, field, value)
        
        self.save()
    
    def mark_as_verified(self, verifier):
        """Mark essay as verified by admin"""
        self.is_verified = True
        self.verified_by = verifier
        self.verified_at = timezone.now()
        self.status = 'published'
        self.save()
    
    def save(self, *args, **kwargs):
        # Calculate basic counts only
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
    
    @property
    def excerpt(self):
        return Truncator(self.content).chars(200)
    
    @property
    def is_published(self):
        return self.status == 'published'
    
    @property
    def is_draft(self):
        return self.status == 'draft'
    
    @property
    def feedback_display(self):
        """Get the full feedback text for the emoji"""
        if self.emoji_feedback:
            for emoji, text in self.EMOJI_FEEDBACK_CHOICES:
                if emoji == self.emoji_feedback:
                    return text
        return "Not reviewed yet"


# ================== PARAGRAPH MODEL ==================
class Paragraph(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    essay = models.ForeignKey('Essay', on_delete=models.CASCADE, related_name='paragraphs')
    paragraph_number = models.IntegerField()
    content = models.TextField()
    formatted_content = models.TextField(blank=True)
    word_count = models.IntegerField(default=0)
    character_count = models.IntegerField(default=0)
    sentence_count = models.IntegerField(default=0)
    time_spent_seconds = models.IntegerField(default=0)
    writing_mode = models.CharField(max_length=20, choices=Essay.WRITING_MODES, default='paragraph')
    revisions = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    completion_time = models.DateTimeField(null=True, blank=True)
    grammar_notes = models.TextField(blank=True)
    improvement_suggestions = models.TextField(blank=True)
    version = models.IntegerField(default=1)
    previous_version = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['paragraph_number']
        unique_together = ['essay', 'paragraph_number']
        verbose_name_plural = 'Paragraphs'
    
    def __str__(self):
        return f"Paragraph {self.paragraph_number} of '{self.essay.title[:20]}...'"
    
    def save(self, *args, **kwargs):
        self.word_count = len(self.content.split()) if self.content else 0
        self.character_count = len(self.content) if self.content else 0
        if self.content:
            sentences = re.split(r'[.!?]+', self.content)
            self.sentence_count = len([s for s in sentences if s.strip()])
        if self.content.strip() and not self.is_completed:
            self.is_completed = True
            self.completion_time = timezone.now()
        super().save(*args, **kwargs)
    
    @property
    def is_empty(self):
        return not bool(self.content and self.content.strip())
    
    @property
    def reading_time_seconds(self):
        return max(1, self.word_count // 3)


# ================== COMMENT MODEL ==================
class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    essay = models.ForeignKey(Essay, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    is_edited = models.BooleanField(default=False)
    edit_count = models.IntegerField(default=0)
    last_edited_at = models.DateTimeField(null=True, blank=True)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_comments', blank=True)
    is_pinned = models.BooleanField(default=False)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    is_approved = models.BooleanField(default=True)
    reported = models.BooleanField(default=False)
    report_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['essay', 'created_at']),
            models.Index(fields=['author', 'created_at']),
        ]
    
    def __str__(self):
        return f"Comment by {self.author.username} on '{self.essay.title[:20]}...'"
    
    @property
    def likes_count(self):
        return self.likes.count()
    
    @property
    def replies_count(self):
        return self.replies.count()
    
    @property
    def is_reply(self):
        return self.parent is not None


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
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    description = models.TextField()
    rules = models.TextField(blank=True)
    theme = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=Essay.CATEGORY_CHOICES, default='general')
    difficulty_level = models.CharField(max_length=20, choices=Essay.DIFFICULTY_LEVELS, default='intermediate')
    word_limit_min = models.IntegerField(default=300)
    word_limit_max = models.IntegerField(default=1500)
    time_limit_minutes = models.IntegerField(default=60)
    allowed_languages = models.ManyToManyField(Language, blank=True)
    prize_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    prize_description = models.TextField(blank=True)
    has_entry_fee = models.BooleanField(default=False)
    entry_fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    registration_start = models.DateTimeField()
    registration_end = models.DateTimeField()
    submission_start = models.DateTimeField()
    submission_end = models.DateTimeField()
    results_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    is_featured = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    max_participants = models.IntegerField(default=0)
    current_participants = models.IntegerField(default=0)
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='organized_competitions')
    organizer_name = models.CharField(max_length=200, blank=True)
    organizer_logo = models.ImageField(upload_to='competition_logos/', null=True, blank=True)
    banner_image = models.ImageField(upload_to='competition_banners/', null=True, blank=True)
    thumbnail_image = models.ImageField(upload_to='competition_thumbnails/', null=True, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    meta_keywords = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Competitions'
        indexes = [
            models.Index(fields=['status', 'submission_end']),
            models.Index(fields=['is_featured', 'created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


# ================== COMPETITION SUBMISSION MODEL ==================
class CompetitionSubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='submissions')
    participant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='competition_submissions')
    essay = models.ForeignKey(Essay, on_delete=models.CASCADE, related_name='competition_submissions')
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    score = models.FloatField(null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    won_prize = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['competition', 'participant']
        verbose_name_plural = 'Competition Submissions'
    
    def __str__(self):
        return f"Submission by {self.participant.username} for {self.competition.title}"


# ================== NOTIFICATION MODEL ==================
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('comment', 'New Comment'),
        ('like', 'New Like'),
        ('reply', 'Reply to Comment'),
        ('system', 'System Notification'),
        ('achievement', 'Achievement Unlocked'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    class Meta:
        ordering = ['-created_at']


# ================== REVIEW TEMPLATE MODEL ==================
class ReviewTemplate(models.Model):
    """Template for essay reviews with predefined feedback"""
    CATEGORY_CHOICES = [
        ('grammar', 'Grammar'),
        ('spelling', 'Spelling'),
        ('structure', 'Structure'),
        ('content', 'Content'),
        ('style', 'Writing Style'),
        ('vocabulary', 'Vocabulary'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    example = models.TextField(blank=True)
    correction = models.TextField(blank=True)
    severity = models.CharField(
        max_length=10,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        default='medium'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category', 'severity']
    
    def __str__(self):
        return f"{self.category}: {self.title}"


# ================== USER PROFILE MODEL ==================
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('judge', 'Judge'),
        ('admin', 'Administrator'),
        ('content_creator', 'Content Creator'),
        ('sponsor', 'Sponsor'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    display_name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/%Y/%m/', null=True, blank=True, default='profile_pictures/default.png')
    cover_photo = models.ImageField(upload_to='cover_photos/%Y/%m/', null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    is_verified_writer = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def verification_status(self):
        """Readable verification status"""
        if self.is_verified_writer:
            return "Verified Writer"
        elif self.email_verified:
            return "Email Verified"
        else:
            return "Pending"

    def save(self, *args, **kwargs):
        if not self.display_name:
            self.display_name = self.user.username
        # Optional: auto verify new users
        if not self.pk and not self.is_verified_writer:
            self.email_verified = True
            self.is_verified_writer = True
        super().save(*args, **kwargs)


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
    
    
    # Add these imports at the top of your models.py
from django.utils import timezone
from datetime import timedelta
import uuid

# Add these models to your essay/models.py file

class TimedChallenge(models.Model):
    """Timed writing challenges with different durations"""
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
    min_words = models.IntegerField(default=300, help_text="Minimum word count")
    max_words = models.IntegerField(default=1000, help_text="Maximum word count")
    points_reward = models.IntegerField(default=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_timed_challenges')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Timed Challenge'
        verbose_name_plural = 'Timed Challenges'
    
    def __str__(self):
        return f"{self.title} ({self.duration_minutes} min)"
    
    def get_difficulty_color(self):
        colors = {'easy': 'success', 'medium': 'warning', 'hard': 'danger'}
        return colors.get(self.difficulty, 'info')


class TimedChallengeSubmission(models.Model):
    """User submissions for timed challenges"""
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
        verbose_name = 'Timed Challenge Submission'
        verbose_name_plural = 'Timed Challenge Submissions'
    
    def __str__(self):
        return f"{self.user.username} - {self.challenge.title}"
    
    def calculate_points(self):
        """Calculate points based on completion and word count"""
        if self.status != 'completed':
            return 0
        
        base_points = self.challenge.points_reward
        
        # Bonus for meeting word count requirements
        if self.challenge.min_words <= self.word_count <= self.challenge.max_words:
            base_points += 50
        
        # Time bonus (completed before time limit)
        time_limit = self.challenge.duration_minutes * 60
        if self.time_spent_seconds < time_limit:
            time_bonus = int((time_limit - self.time_spent_seconds) / 60) * 5
            base_points += min(time_bonus, 100)  # Max 100 bonus points
        
        self.points_earned = base_points
        return base_points
    
    def save(self, *args, **kwargs):
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
            self.calculate_points()
        super().save(*args, **kwargs)


class CharacterChallenge(models.Model):
    """Character-limited writing challenges"""
    LIMIT_CHOICES = [
        (100, '100 Characters - Micro'),
        (280, '280 Characters - Tweet'),
        (500, '500 Characters - Flash'),
        (1000, '1000 Characters - Short'),
        (2000, '2000 Characters - Medium'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    prompt = models.TextField(help_text="The writing prompt for this challenge")
    character_limit = models.IntegerField(choices=LIMIT_CHOICES, default=280)
    allow_over_limit = models.BooleanField(default=False, help_text="Allow submissions exceeding limit")
    points_reward = models.IntegerField(default=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_character_challenges')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Character Challenge'
        verbose_name_plural = 'Character Challenges'
    
    def __str__(self):
        return f"{self.title} ({self.character_limit} chars)"
    
    def get_difficulty_badge(self):
        if self.character_limit <= 280:
            return 'Hard'
        elif self.character_limit <= 1000:
            return 'Medium'
        else:
            return 'Easy'


class CharacterChallengeSubmission(models.Model):
    """User submissions for character challenges"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    challenge = models.ForeignKey(CharacterChallenge, on_delete=models.CASCADE, related_name='submissions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='character_submissions')
    content = models.TextField()
    character_count = models.IntegerField(default=0)
    word_count = models.IntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)
    points_earned = models.IntegerField(default=0)
    is_valid = models.BooleanField(default=True, help_text="Within character limit")
    
    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['challenge', 'user']
        verbose_name = 'Character Challenge Submission'
        verbose_name_plural = 'Character Challenge Submissions'
    
    def __str__(self):
        return f"{self.user.username} - {self.challenge.title}"
    
    def validate_submission(self):
        """Check if submission meets requirements"""
        self.character_count = len(self.content)
        self.word_count = len(self.content.split())
        
        if self.character_count <= self.challenge.character_limit:
            self.is_valid = True
            self.points_earned = self.challenge.points_reward
            
            # Bonus for using exactly the limit
            if abs(self.character_count - self.challenge.character_limit) <= 10:
                self.points_earned += 25
        else:
            self.is_valid = self.challenge.allow_over_limit
            self.points_earned = 0 if not self.is_valid else self.challenge.points_reward // 2
    
    def save(self, *args, **kwargs):
        self.validate_submission()
        super().save(*args, **kwargs)


class AIWritingSession(models.Model):
    """Track AI Writing Assistant usage"""
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
    essay = models.ForeignKey('Essay', on_delete=models.CASCADE, null=True, blank=True, related_name='ai_sessions')
    suggestion_type = models.CharField(max_length=20, choices=SUGGESTION_TYPES)
    original_text = models.TextField()
    ai_suggestion = models.TextField()
    was_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'AI Writing Session'
        verbose_name_plural = 'AI Writing Sessions'
    
    def __str__(self):
        return f"{self.user.username} - {self.suggestion_type} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class ChallengeLeaderboard(models.Model):
    """Leaderboard for challenge participants"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='challenge_stats')
    total_challenges_completed = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    timed_challenges_completed = models.IntegerField(default=0)
    character_challenges_completed = models.IntegerField(default=0)
    fastest_completion_seconds = models.IntegerField(null=True, blank=True)
    longest_streak = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    last_challenge_date = models.DateField(null=True, blank=True)
    rank = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-total_points', '-total_challenges_completed']
        verbose_name = 'Challenge Leaderboard'
        verbose_name_plural = 'Challenge Leaderboards'
    
    def __str__(self):
        return f"{self.user.username} - {self.total_points} points"
    
    def update_stats(self):
        """Update user statistics"""
        # Calculate totals
        self.timed_challenges_completed = TimedChallengeSubmission.objects.filter(
            user=self.user, status='completed'
        ).count()
        
        self.character_challenges_completed = CharacterChallengeSubmission.objects.filter(
            user=self.user, is_valid=True
        ).count()
        
        self.total_challenges_completed = self.timed_challenges_completed + self.character_challenges_completed
        
        # Calculate total points
        timed_points = TimedChallengeSubmission.objects.filter(
            user=self.user, status='completed'
        ).aggregate(total=models.Sum('points_earned'))['total'] or 0
        
        character_points = CharacterChallengeSubmission.objects.filter(
            user=self.user
        ).aggregate(total=models.Sum('points_earned'))['total'] or 0
        
        self.total_points = timed_points + character_points
        
        # Update streak
        today = timezone.now().date()
        if self.last_challenge_date:
            days_diff = (today - self.last_challenge_date).days
            if days_diff == 1:
                self.current_streak += 1
                self.longest_streak = max(self.longest_streak, self.current_streak)
            elif days_diff > 1:
                self.current_streak = 1
        else:
            self.current_streak = 1
        
        self.last_challenge_date = today
        self.save()
    
    @classmethod
    def update_all_ranks(cls):
        """Update ranks for all users"""
        leaderboard = cls.objects.all().order_by('-total_points', '-total_challenges_completed')
        for rank, entry in enumerate(leaderboard, start=1):
            entry.rank = rank
            entry.save(update_fields=['rank'])