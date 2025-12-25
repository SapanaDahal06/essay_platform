# essay/models.py - CORRECTED VERSION
from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils import timezone
import re


class Language(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
        ('judge', 'Judge'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    student_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    preferred_language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    points = models.IntegerField(default=0)
    
    total_essays = models.IntegerField(default=0)
    total_likes_received = models.IntegerField(default=0)
    avg_essay_score = models.FloatField(default=0.0)
    leaderboard_score = models.FloatField(default=0.0)
    last_score_update = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} ({self.role})"
    
    class Meta:
        ordering = ['user__username']
    
    def update_leaderboard_stats(self):
        from django.db.models import Avg
        
        user_essays = Essay.objects.filter(author=self.user, score__gt=0)
        
        self.total_essays = user_essays.count()
        self.avg_essay_score = user_essays.aggregate(avg=Avg('score'))['avg'] or 0
        
        total_likes = 0
        for essay in user_essays:
            total_likes += essay.likes.count()
        self.total_likes_received = total_likes
        
        quality_score = self.avg_essay_score * 0.6
        activity_score = min(40, (self.total_essays / 10) * 40)
        
        self.leaderboard_score = quality_score + activity_score
        self.last_score_update = timezone.now()
        self.save()


class Essay(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('writing', 'Writing in Progress'),
        ('submitted', 'Submitted'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('education', 'Education'),
        ('technology', 'Technology'),
        ('environment', 'Environment'),
        ('creative', 'Creative Writing'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='essays')
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')
    
    # Language reference
    primary_language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True, related_name='primary_essays')
    
    # Metrics
    word_count = models.IntegerField(default=0)
    views = models.IntegerField(default=0)
    likes = models.ManyToManyField(User, blank=True, related_name='liked_essays')
    
    # PDF related
    pdf_file = models.FileField(upload_to='essays/pdfs/', blank=True, null=True)
    pdf_generated_at = models.DateTimeField(blank=True, null=True)
    
    # Scoring
    grammar_issues = models.PositiveIntegerField(default=0)
    spelling_issues = models.PositiveIntegerField(default=0)
    score = models.FloatField(default=0.0)
    grammar_score = models.FloatField(default=0.0)
    spelling_score = models.FloatField(default=0.0)
    content_score = models.FloatField(default=0.0)
    grade = models.CharField(max_length=5, blank=True, null=True)
    
    # Text analysis
    unique_words = models.IntegerField(default=0)
    sentence_count = models.IntegerField(default=0)
    avg_sentence_length = models.FloatField(default=0.0)
    leaderboard_score = models.FloatField(default=0.0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Essays'
    
    def __str__(self):
        return f"{self.title} by {self.author.username}"
    
    def calculate_metrics(self):
        if not self.content:
            self.word_count = 0
            self.sentence_count = 0
            self.unique_words = 0
            self.avg_sentence_length = 0.0
            return
        
        try:
            words = self.content.split()
            self.word_count = len(words)
            
            sentences = [s.strip() for s in re.split(r'[.!?]+', self.content) if s.strip()]
            self.sentence_count = len(sentences) if sentences else 0
            
            self.unique_words = len(set([w.lower().strip() for w in words if w.strip()]))
            self.avg_sentence_length = round(self.word_count / self.sentence_count, 2) if self.sentence_count > 0 else 0.0
        except Exception as e:
            self.word_count = 0
            self.sentence_count = 0
            self.unique_words = 0
            self.avg_sentence_length = 0.0
    
    def save(self, *args, **kwargs):
        skip_checks = kwargs.pop('skip_checks', False)
        
        if not skip_checks:
            self.calculate_metrics()
            self.leaderboard_score = self.score
        
        super().save(*args, **kwargs)
        
        try:
            if self.author.profile:
                self.author.profile.update_leaderboard_stats()
        except:
            pass
    
    @property
    def has_pdf(self):
        return bool(self.pdf_file)
    
    @property
    def like_count(self):
        return self.likes.count()


class Paragraph(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    essay = models.ForeignKey('Essay', on_delete=models.CASCADE, related_name='paragraphs')
    paragraph_number = models.PositiveIntegerField()
    content = models.TextField(blank=True)
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)
    is_locked = models.BooleanField(default=False)
    word_count = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['essay', 'paragraph_number']
        ordering = ['paragraph_number']
    
    def __str__(self):
        return f"Paragraph {self.paragraph_number} of {self.essay.title}"
    
    def save(self, *args, **kwargs):
        if self.content:
            self.word_count = len(self.content.split())
        else:
            self.word_count = 0
        super().save(*args, **kwargs)
    
    def unlock(self):
        self.is_locked = False
        self.save()


class Comment(models.Model):
    essay = models.ForeignKey('Essay', on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author.username} on '{self.essay.title}'"