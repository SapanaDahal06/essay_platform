from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import uuid


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


# ================== ESSAY MODEL ==================
class Essay(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('published', 'Published'),
        ('rejected', 'Rejected'),
    ]
    
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('education', 'Education'),
        ('technology', 'Technology'),
        ('environment', 'Environment'),
        ('creative', 'Creative Writing'),
    ]
    
    WRITING_MODES = [
        ('normal', 'Normal Mode'),
        ('paragraph', 'Paragraph Mode'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    
    # Content fields
    content = models.TextField()  # Plain text version
    formatted_content = models.TextField(blank=True)  # HTML version - ADDED
    
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='essays')
    
    # Language and category
    primary_language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')
    
    # Writing mode
    writing_mode = models.CharField(max_length=20, choices=WRITING_MODES, default='paragraph')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Statistics
    word_count = models.IntegerField(default=0)
    grammar_score = models.FloatField(default=0)
    spelling_score = models.FloatField(default=0)
    content_score = models.FloatField(default=0)
    score = models.FloatField(default=0)
    grade = models.CharField(max_length=2, blank=True)
    views = models.IntegerField(default=0)
    
    # PDF related
    pdf_file = models.FileField(upload_to='essays/pdfs/', null=True, blank=True)
    pdf_generated_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Likes
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_essays', blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Essays'
    
    def __str__(self):
        return self.title
    
    def calculate_metrics(self):
        # Calculate word count from content
        words = len(self.content.split())
        self.word_count = words
        
        # Simple scoring (you can customize this)
        self.grammar_score = min(100, words * 0.1)
        self.spelling_score = min(100, words * 0.08)
        self.content_score = min(100, words * 0.12)
        self.score = (self.grammar_score + self.spelling_score + self.content_score) / 3
        
        # Determine grade
        if self.score >= 90:
            self.grade = 'A+'
        elif self.score >= 80:
            self.grade = 'A'
        elif self.score >= 70:
            self.grade = 'B'
        elif self.score >= 60:
            self.grade = 'C'
        elif self.score >= 50:
            self.grade = 'D'
        else:
            self.grade = 'F'
    
    def save(self, *args, **kwargs):
        self.calculate_metrics()
        super().save(*args, **kwargs)


# ================== PARAGRAPH MODEL ==================
class Paragraph(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # ForeignKey to Essay
    essay = models.ForeignKey(Essay, on_delete=models.CASCADE, related_name='paragraphs')
    
    paragraph_number = models.IntegerField()
    
    # Content fields
    content = models.TextField()  # Plain text
    formatted_content = models.TextField(blank=True)  # HTML with formatting - ADDED
    
    word_count = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['paragraph_number']
        unique_together = ['essay', 'paragraph_number']
    
    def __str__(self):
        return f"Paragraph {self.paragraph_number} of '{self.essay.title[:20]}...'"
    
    def save(self, *args, **kwargs):
        # Calculate word count
        self.word_count = len(self.content.split())
        super().save(*args, **kwargs)


# ================== COMMENT MODEL ==================
class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # ForeignKey to Essay
    essay = models.ForeignKey(Essay, on_delete=models.CASCADE, related_name='comments')
    
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.author} on '{self.essay.title[:20]}...'"


# ================== USER PROFILE MODEL ==================
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Administrator'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    
    # Profile info
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    student_id = models.CharField(max_length=50, blank=True)
    bio = models.TextField(blank=True)
    
    # Preferences
    preferred_language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    
    # Stats
    points = models.IntegerField(default=0)
    leaderboard_score = models.IntegerField(default=0)
    essays_written = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-leaderboard_score']
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def update_stats(self):
        self.essays_written = Essay.objects.filter(author=self.user).count()
        self.leaderboard_score = (self.essays_written * 10) + self.points
        self.save()