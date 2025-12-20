from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils import timezone
import re
from django.db.models import Min

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
    competitions_entered = models.IntegerField(default=0)
    competitions_won = models.IntegerField(default=0)
    best_competition_rank = models.IntegerField(default=0)
    
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
        
        self.competitions_entered = Submission.objects.filter(submitted_by=self.user).count()
        self.competitions_won = Submission.objects.filter(submitted_by=self.user, rank__lte=3).count()
        
        best_rank = Submission.objects.filter(submitted_by=self.user, rank__isnull=False).aggregate(best=Min('rank'))['best']
        self.best_competition_rank = best_rank or 0
        
        quality_score = self.avg_essay_score * 0.5
        activity_score = min(30, (self.total_essays / 10) * 30)
        competition_score = 20 if self.competitions_won > 0 else 10 if self.competitions_entered > 0 else 0
        
        self.leaderboard_score = quality_score + activity_score + competition_score
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
    
    WRITING_MODE_CHOICES = [
        ('normal', 'Normal'),
        ('paragraph', 'Paragraph by Paragraph'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='essays')
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    file_name = models.CharField(max_length=255, default='essay.txt')
    file_size = models.BigIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    word_count = models.IntegerField(default=0)
    views = models.IntegerField(default=0)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')
    pdf_file = models.FileField(upload_to='essays/pdfs/', blank=True, null=True)
    pdf_generated_at = models.DateTimeField(blank=True, null=True)
    writing_mode = models.CharField(max_length=20, choices=WRITING_MODE_CHOICES, default='normal')
    current_paragraph = models.PositiveIntegerField(default=1)
    max_paragraphs = models.PositiveIntegerField(default=5)
    primary_language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True, related_name='primary_essays')
    likes = models.ManyToManyField(User, blank=True, related_name='liked_essays')
    
    grammar_issues = models.PositiveIntegerField(default=0)
    spelling_issues = models.PositiveIntegerField(default=0)
    score = models.FloatField(default=0.0)
    grammar_score = models.FloatField(default=0.0)
    spelling_score = models.FloatField(default=0.0)
    content_score = models.FloatField(default=0.0)
    grade = models.CharField(max_length=5, blank=True, null=True)
    unique_words = models.IntegerField(default=0)
    sentence_count = models.IntegerField(default=0)
    avg_sentence_length = models.FloatField(default=0.0)
    leaderboard_score = models.FloatField(default=0.0)  # FIXED: Added this field
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Essays'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['author', '-created_at']),
        ]
    
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
            print(f"Error calculating metrics: {e}")
            self.word_count = 0
            self.sentence_count = 0
            self.unique_words = 0
            self.avg_sentence_length = 0.0
    
    def check_grammar_and_spelling(self):
        try:
            from .grammar_checker import grammar_checker
            
            if not self.content or len(self.content.strip()) < 10:
                self.grammar_issues = 0
                self.spelling_issues = 0
                self.grammar_score = 100.0
                self.spelling_score = 100.0
                self.score = 100.0
                self.grade = 'A'
                return
            
            if not grammar_checker.is_available():
                self.grammar_score = 75.0
                self.spelling_score = 75.0
                self.score = 75.0
                self.grade = 'C'
                return
            
            result = grammar_checker.check_essay(self.content)
            self.grammar_issues = result.get('grammar_issues', 0)
            self.spelling_issues = result.get('spelling_issues', 0)
            self.grammar_score = result.get('grammar_score', 0)
            self.spelling_score = result.get('spelling_score', 0)
            
            if self.content_score > 0:
                self.score = round((self.grammar_score * 0.4) + (self.spelling_score * 0.3) + (self.content_score * 0.3), 2)
            else:
                self.score = round((self.grammar_score * 0.6) + (self.spelling_score * 0.4), 2)
            
            if self.score >= 90:
                self.grade = 'A'
            elif self.score >= 80:
                self.grade = 'B'
            elif self.score >= 70:
                self.grade = 'C'
            elif self.score >= 60:
                self.grade = 'D'
            else:
                self.grade = 'F'
                
        except ImportError:
            print("Grammar checker module not found.")
            self.grammar_score = 75.0
            self.spelling_score = 75.0
            self.score = 75.0
            self.grade = 'C'
        except Exception as e:
            print(f"Grammar check error: {e}")
            self.grammar_score = 70.0
            self.spelling_score = 70.0
            self.score = 70.0
            self.grade = 'C'
    
    def save(self, *args, **kwargs):
        skip_checks = kwargs.pop('skip_checks', False)
        
        if not skip_checks:
            if self.writing_mode == 'paragraph' and self.pk:
                try:
                    paragraphs = self.paragraphs.all().order_by('paragraph_number')
                    if paragraphs.exists():
                        self.content = '\n\n'.join([p.content for p in paragraphs if p.content])
                except Exception as e:
                    print(f"Error combining paragraphs: {e}")
            
            self.calculate_metrics()
            self.check_grammar_and_spelling()
            self.leaderboard_score = self.score  # FIXED: Set leaderboard_score
        
        super().save(*args, **kwargs)
        
        try:
            if self.author.profile:
                self.author.profile.update_leaderboard_stats()
        except:
            pass
    
    def get_current_paragraph(self):
        if self.writing_mode != 'paragraph':
            return None
        try:
            return self.paragraphs.filter(paragraph_number=self.current_paragraph).first()
        except Exception:
            return None
    
    def move_to_next_paragraph(self):
        if self.current_paragraph < self.max_paragraphs:
            self.current_paragraph += 1
            self.save(skip_checks=True)
            return True
        return False
    
    def get_paragraph_progress(self):
        if self.max_paragraphs == 0:
            return 0
        completed = self.paragraphs.filter(content__isnull=False).exclude(content='').count()
        return round((completed / self.max_paragraphs) * 100, 2)
    
    @property
    def has_pdf(self):
        return bool(self.pdf_file)
    
    @property
    def like_count(self):
        return self.likes.count()
    
    @property
    def is_completed(self):
        return self.status in ['published', 'submitted']

class Paragraph(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    essay = models.ForeignKey(Essay, on_delete=models.CASCADE, related_name='paragraphs')
    paragraph_number = models.PositiveIntegerField()
    content = models.TextField(blank=True)
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)
    is_locked = models.BooleanField(default=False)
    word_count = models.IntegerField(default=0)
    grammar_issues = models.PositiveIntegerField(default=0)
    spelling_issues = models.PositiveIntegerField(default=0)
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='locked_paragraphs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['essay', 'paragraph_number']
        ordering = ['paragraph_number']
        indexes = [
            models.Index(fields=['essay', 'paragraph_number']),
        ]
    
    def __str__(self):
        return f"Paragraph {self.paragraph_number} of {self.essay.title}"
    
    def save(self, *args, **kwargs):
        if self.content:
            self.word_count = len(self.content.split())
        else:
            self.word_count = 0
        super().save(*args, **kwargs)
    
    def lock(self, user):
        self.is_locked = True
        self.locked_at = timezone.now()
        self.locked_by = user
        self.save()
    
    def unlock(self):
        self.is_locked = False
        self.locked_by = None
        self.locked_at = None
        self.save()
    
    def is_editable(self, user):
        if not self.is_locked:
            return True
        return self.locked_by == user
    
    @property
    def is_empty(self):
        return not self.content or not self.content.strip()

class Competition(models.Model):
    WRITING_MODE_CHOICES = [
        ('normal', 'Normal'),
        ('paragraph', 'Paragraph by Paragraph'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    topic = models.CharField(max_length=200, blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    prize = models.CharField(max_length=100, blank=True, null=True)
    word_limit = models.CharField(max_length=50, default="1500-2500")
    is_active = models.BooleanField(default=True)
    allowed_languages = models.ManyToManyField(Language, blank=True)
    writing_mode = models.CharField(max_length=20, choices=WRITING_MODE_CHOICES, default='normal')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['is_active', '-created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def is_open(self):
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date
    
    @property
    def is_upcoming(self):
        return self.is_active and timezone.now() < self.start_date
    
    @property
    def is_ended(self):
        return timezone.now() > self.end_date
    
    @property
    def submission_count(self):
        return self.submissions.count()

class Comment(models.Model):
    essay = models.ForeignKey(Essay, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['essay', '-created_at']),
        ]
    
    def __str__(self):
        return f"Comment by {self.author.username} on '{self.essay.title}'"
    
    @property
    def is_recent(self):
        return (timezone.now() - self.created_at).days == 0

class Submission(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='submissions')
    essay = models.ForeignKey(Essay, on_delete=models.CASCADE)
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    score = models.FloatField(null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['competition', 'submitted_by']
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['competition', '-score']),
            models.Index(fields=['submitted_by', '-submitted_at']),
        ]
    
    def __str__(self):
        return f"Submission by {self.submitted_by.username} for '{self.competition.title}'"
    
    @property
    def is_winner(self):
        return self.rank is not None and self.rank <= 3
    
    @property
    def is_active(self):
        return self.competition.is_open if self.competition else False
    
    @property
    def medal(self):
        if self.rank == 1:
            return "🥇"
        elif self.rank == 2:
            return "🥈"
        elif self.rank == 3:
            return "🥉"
        return None