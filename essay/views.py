from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db import models
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph as PDFParagraph, Spacer
import json
import re  # Add this import
from django.db.models import Count, Q
from .models import Essay, UserProfile, Language, Comment, Paragraph, ReviewTemplate, Notification  # Add missing imports

# ================== BASIC PAGES ==================
def home(request):
    """Home page view"""
    try:
        essays = Essay.objects.filter(status='published').select_related('author', 'primary_language').order_by('-created_at')[:10]
        return render(request, 'essay/home.html', {'essays': essays})
    except Exception as e:
        return render(request, 'essay/home.html', {'essays': [], 'error': str(e)})

def about(request):
    """About page view"""
    return render(request, 'essay/about.html')

def community(request):
    """Community page view"""
    essays = Essay.objects.filter(status='published').order_by('-created_at')[:20]
    return render(request, 'essay/community.html', {'essays': essays})

def resources(request):
    """Resources page view"""
    return render(request, 'essay/resources.html')

def essay_list(request):
    """Public essay listing"""
    essays = Essay.objects.filter(status='published').order_by('-created_at')
    return render(request, 'essay/essay_list.html', {'essays': essays})

# ================== AUTHENTICATION ==================
def custom_login(request):
    """Custom login view"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            messages.error(request, "Please provide both username and password.")
            return render(request, 'essay/login.html')
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {username}!")
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'essay/login.html')

def custom_logout(request):
    """Custom logout view"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')

def register(request):
    """User registration view"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        role = request.POST.get('role', 'student')
        
        if not all([username, email, password, password2]):
            messages.error(request, "All fields are required.")
        elif password != password2:
            messages.error(request, "Passwords do not match.")
        elif len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
        else:
            try:
                user = User.objects.create_user(username=username, email=email, password=password)
                UserProfile.objects.create(user=user, role=role)
                login(request, user)
                messages.success(request, f"Account created successfully! Welcome, {username}!")
                return redirect('home')
            except Exception as e:
                messages.error(request, f"Error creating account: {str(e)}")
    
    return render(request, 'essay/register.html')

# ================== USER PAGES ==================
@login_required
def profile(request):
    """User profile page"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    essays = Essay.objects.filter(author=request.user).select_related('primary_language').order_by('-created_at')
    return render(request, 'essay/profile.html', {'profile': user_profile, 'essays': essays})

@login_required
def dashboard(request):
    """User dashboard"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    essays = Essay.objects.filter(author=request.user).order_by('-created_at')[:5]
    
    # Get all users with their published essay counts
    all_users = User.objects.annotate(
        published_essays=Count('essays', filter=Q(essays__status='published'))
    ).order_by('-published_essays')
    
    # Find user's rank
    rank = None
    for idx, user in enumerate(all_users, start=1):
        if user == request.user:
            rank = idx
            break
    
    # Calculate user's score based on essays and activity
    published_count = Essay.objects.filter(author=request.user, status='published').count()
    draft_count = Essay.objects.filter(author=request.user, status='draft').count()
    
    return render(request, 'essay/dashboard.html', {
        'profile': profile,
        'essays': essays,
        'rank': rank,
        'published_count': published_count,
        'draft_count': draft_count,
    })

def leaderboard(request):
    """Leaderboard page"""
    # Calculate leaderboard based on published essays count
    profiles = UserProfile.objects.annotate(
        essay_count=Count('user__essays', filter=Q(user__essays__status='published'))
    ).order_by('-essay_count')
    
    return render(request, 'essay/leaderboard.html', {'profiles': profiles})

# ================== ESSAY CRUD ==================
@login_required
def create_essay(request):
    """Create a new essay"""
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        formatted_content = request.POST.get('formatted_content', '').strip()
        language_id = request.POST.get('language')
        
        if not title or not content:
            messages.error(request, "Title and content are required.")
        else:
            language = Language.objects.filter(id=language_id).first()
            
            essay = Essay.objects.create(
                author=request.user,
                title=title,
                content=content,
                formatted_content=formatted_content,
                primary_language=language,
                status='submitted'
            )
            
            messages.success(request, "Essay created successfully!")
            return redirect('essay_detail', essay_id=essay.id)
    
    languages = Language.objects.filter(is_active=True)
    return render(request, 'essay/create_essay.html', {'languages': languages})

@login_required
def my_essays(request):
    """List user's essays"""
    essays = Essay.objects.filter(author=request.user).order_by('-created_at')
    return render(request, 'essay/my_essays.html', {'essays': essays})

def essay_detail(request, essay_id):
    """View essay details"""
    essay = get_object_or_404(Essay, id=essay_id)
    
    # Check permissions
    if essay.status != 'published' and essay.author != request.user:
        messages.error(request, "You don't have permission to view this essay.")
        return redirect('home')
    
    # Increment view count
    Essay.objects.filter(id=essay_id).update(views=models.F('views') + 1)
    
    # Get comments
    comments = essay.comments.all().order_by('-created_at')
    
    return render(request, 'essay/essay_detail.html', {
        'essay': essay,
        'comments': comments
    })

@login_required
def edit_essay(request, essay_id):
    """Edit existing essay"""
    essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    
    if request.method == 'POST':
        essay.title = request.POST.get('title', '').strip()
        essay.content = request.POST.get('content', '').strip()
        essay.formatted_content = request.POST.get('formatted_content', '').strip()
        essay.save()
        
        messages.success(request, "Essay updated successfully!")
        return redirect('essay_detail', essay_id=essay.id)
    
    return render(request, 'essay/edit_essay.html', {'essay': essay})

@login_required
def delete_essay(request, essay_id):
    """Delete essay"""
    essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    
    if request.method == 'POST':
        essay.delete()
        messages.success(request, "Essay deleted successfully!")
        return redirect('my_essays')
    
    return render(request, 'essay/delete_essay.html', {'essay': essay})

# ================== COMMENTS ==================
@login_required
@require_POST
def add_comment(request, essay_id):
    """Add comment to essay"""
    essay = get_object_or_404(Essay, id=essay_id)
    content = request.POST.get('content', '').strip()
    
    if content:
        Comment.objects.create(
            essay=essay,
            author=request.user,
            content=content
        )
        messages.success(request, "Comment added!")
    else:
        messages.error(request, "Comment cannot be empty.")
    
    return redirect('essay_detail', essay_id=essay_id)

# ================== PDF DOWNLOAD ==================
def download_pdf(request, essay_id):
    """Download essay as PDF"""
    essay = get_object_or_404(Essay, id=essay_id)
    
    # Check permissions
    if essay.status != 'published' and essay.author != request.user:
        messages.error(request, "You don't have permission to download this essay.")
        return redirect('home')
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Add title
    story.append(PDFParagraph(f"<b>{essay.title}</b>", styles['Title']))
    story.append(PDFParagraph(f"By: {essay.author.username}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Clean HTML content before adding to PDF
    def clean_html_for_pdf(text):
        """Remove unsupported HTML tags for PDF generation"""
        if not text:
            return ""
        
        # Remove HTML tags that reportlab doesn't support
        text = re.sub(r'<span[^>]*>.*?</span>', '', text)  # Remove span tags
        text = re.sub(r'<br\s*/?>', '\n', text)  # Replace <br> with newline
        text = re.sub(r'&nbsp;', ' ', text)  # Replace &nbsp; with space
        text = re.sub(r'<[^>]+>', '', text)  # Remove any remaining HTML tags
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Normalize multiple newlines
        return text.strip()
    
    # Get and clean content
    content = essay.formatted_content or essay.content
    clean_content = clean_html_for_pdf(content)
    
    # Split into paragraphs
    paragraphs = [p.strip() for p in clean_content.split('\n\n') if p.strip()]
    
    for para in paragraphs:
        if para:
            # Replace multiple spaces with single space
            para = re.sub(r'\s+', ' ', para)
            story.append(PDFParagraph(para, styles['Normal']))
            story.append(Spacer(1, 6))
    
    # Build PDF
    try:
        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Return PDF as response
        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{essay.title}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f"Error generating PDF: {str(e)}")
        return redirect('essay_detail', essay_id=essay.id)

# ================== GRAMMAR CHECK ==================
@login_required
def grammar_check(request, essay_id):
    """Grammar check for essay"""
    essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    return render(request, 'essay/grammar_check.html', {'essay': essay})

# ================== ADMIN DASHBOARD ==================
@login_required
def admin_dashboard(request):
    """Admin dashboard"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access the admin dashboard.")
        return redirect('home')
    
    context = {
        'total_essays': Essay.objects.count(),
        'total_users': User.objects.count(),
        'total_comments': Comment.objects.count(),
        'essay_status': dict(Essay.objects.values_list('status').annotate(count=Count('id'))),
        'user_roles': dict(UserProfile.objects.values_list('role').annotate(count=Count('id'))),
        'recent_essays': Essay.objects.select_related('author').order_by('-created_at')[:5],
        'recent_users': User.objects.select_related('userprofile').order_by('-date_joined')[:5],
    }
    
    return render(request, 'essay/admin_dashboard.html', context)

# ================== PARAGRAPH WRITING ==================
@login_required
def write_paragraph(request, essay_id):
    """Write paragraph for essay"""
    essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    
    # Handle AJAX request
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            paragraph_content = data.get('content', '')
            paragraph_index = data.get('paragraph_index', 0)
            
            paragraph, created = Paragraph.objects.get_or_create(
                essay=essay,
                paragraph_number=paragraph_index + 1,
                defaults={'content': paragraph_content}
            )
            
            if not created:
                paragraph.content = paragraph_content
                paragraph.save()
            
            return JsonResponse({
                'success': True,
                'paragraph_id': str(paragraph.id)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # GET request - render template
    paragraphs = essay.paragraphs.all().order_by('paragraph_number')
    return render(request, 'essay/write_paragraph.html', {
        'essay': essay,
        'paragraphs': paragraphs
    })

@login_required
@require_POST
def save_paragraph(request, essay_id):
    """Save paragraph"""
    essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    content = request.POST.get('content', '').strip()
    paragraph_num = int(request.POST.get('paragraph_num', 1))
    
    paragraph, created = Paragraph.objects.get_or_create(
        essay=essay,
        paragraph_number=paragraph_num,
        defaults={'content': content}
    )
    
    if not created:
        paragraph.content = content
        paragraph.save()
    
    messages.success(request, f"Paragraph {paragraph_num} saved!")
    return redirect('write_paragraph', essay_id=essay.id)

@login_required
def unlock_paragraph(request, essay_id, paragraph_num):
    """Unlock paragraph for editing"""
    essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    paragraph = Paragraph.objects.filter(essay=essay, paragraph_number=paragraph_num).first()
    
    if paragraph:
        paragraph.is_locked = False
        paragraph.save()
        messages.success(request, f"Paragraph {paragraph_num} unlocked!")
    else:
        messages.warning(request, f"Paragraph {paragraph_num} not found.")
    
    return redirect('write_paragraph', essay_id=essay.id)

# ================== ENHANCED WRITING ==================
@login_required
def write_paragraph_enhanced(request):
    """Enhanced writing page"""
    return render(request, 'essay/write_paragraph_enhanced.html')

@login_required
def save_secure_paragraph(request):
    """Save secure paragraph"""
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        
        if content:
            # Create essay from secure paragraph
            essay = Essay.objects.create(
                author=request.user,
                title=f"Secure Essay {timezone.now().strftime('%Y-%m-%d %H:%M')}",
                content=content,
                status='submitted',
                writing_mode='enhanced'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Paragraph saved successfully!',
                'essay_id': str(essay.id),
                'content': content[:100] + '...' if len(content) > 100 else content
            })
        
        return JsonResponse({
            'success': False,
            'message': 'No content provided'
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

# ================== LIKE ESSAY ==================
@login_required
def like_essay(request, pk):
    """Like/unlike essay"""
    essay = get_object_or_404(Essay, pk=pk)
    
    if request.user in essay.likes.all():
        # Unlike
        essay.likes.remove(request.user)
        liked = False
        message = 'You unliked this essay.'
    else:
        # Like
        essay.likes.add(request.user)
        liked = True
        message = 'You liked this essay!'
    
    # Check if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'likes_count': essay.likes.count(),
            'message': message
        })
    
    messages.success(request, message)
    return redirect('essay_detail', essay_id=essay.id)

# ================== ESSAY REVIEW ==================
@login_required
def review_essays(request):
    """List essays for review (admin only)"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to review essays.")
        return redirect('home')
    
    # Get essays pending review
    pending_essays = Essay.objects.filter(
        status='submitted',
        is_reviewed=False
    ).order_by('created_at')
    
    # Get recently reviewed essays
    reviewed_essays = Essay.objects.filter(
        is_reviewed=True
    ).order_by('-reviewed_at')[:10]
    
    return render(request, 'essay/review_essays.html', {
        'pending_essays': pending_essays,
        'reviewed_essays': reviewed_essays,
    })

@login_required
def review_essay_detail(request, essay_id):
    """Detailed review of an essay"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to review essays.")
        return redirect('home')
    
    essay = get_object_or_404(Essay, id=essay_id)
    
    # Get review templates for suggestions
    review_templates = ReviewTemplate.objects.filter(is_active=True)
    
    # Analyze essay content for common errors
    content = essay.content
    word_count = len(content.split())
    
    # Simple analysis
    sentences = re.split(r'[.!?]+', content)
    avg_sentence_length = word_count / max(len(sentences), 1)
    
    # Common grammar patterns to check
    grammar_patterns = {
        'run_on_sentences': r'[.!?]\s*[a-z]',  # Sentences starting with lowercase
        'comma_splices': r',\s+[a-z]',  # Comma followed by lowercase (potential splice)
        'fragments': r'^[a-z].*[^.!?]$',  # Starts lowercase, doesn't end with punctuation
    }
    
    grammar_issues = {}
    for issue, pattern in grammar_patterns.items():
        matches = re.findall(pattern, content, re.MULTILINE)
        grammar_issues[issue] = len(matches)
    
    # Simple spelling check (basic)
    common_misspellings = {
        'seperate': 'separate',
        'definately': 'definitely',
        'occured': 'occurred',
        'recieve': 'receive',
        'wierd': 'weird',
        'accomodate': 'accommodate',
        'embarass': 'embarrass',
        'mispell': 'misspell'
    }
    
    spelling_issues = {}
    words = content.lower().split()
    for word in words:
        clean_word = re.sub(r'[^\w\s]', '', word)
        if clean_word in common_misspellings:
            spelling_issues[clean_word] = common_misspellings[clean_word]
    
    if request.method == 'POST':
        # Save review feedback
        essay.grammar_errors = request.POST.get('grammar_errors', '')
        essay.spelling_errors = request.POST.get('spelling_errors', '')
        essay.punctuation_errors = request.POST.get('punctuation_errors', '')
        essay.style_suggestions = request.POST.get('style_suggestions', '')
        essay.vocabulary_suggestions = request.POST.get('vocabulary_suggestions', '')
        essay.structure_comments = request.POST.get('structure_comments', '')
        essay.content_feedback = request.POST.get('content_feedback', '')
        
        # Calculate scores based on feedback
        essay.grammar_score = max(0, 100 - (len(essay.grammar_errors.split(',')) * 5))
        essay.spelling_score = max(0, 100 - (len(essay.spelling_errors.split(',')) * 10))
        
        # Update overall score
        essay.overall_score = (essay.grammar_score * 0.3 + 
                              essay.spelling_score * 0.3 + 
                              essay.content_score * 0.4)
        
        # Mark as reviewed
        essay.is_reviewed = True
        essay.reviewed_by = request.user
        essay.reviewed_at = timezone.now()
        essay.save()
        
        # Send notification to author
        Notification.objects.create(
            user=essay.author,
            notification_type='system',
            title='Your Essay Has Been Reviewed! 📝',
            message=f'Your essay "{essay.title}" has been reviewed by an admin.',
            is_important=True
        )
        
        messages.success(request, "Essay review submitted successfully!")
        return redirect('review_essays')
    
    return render(request, 'essay/review_essay_detail.html', {
        'essay': essay,
        'review_templates': review_templates,
        'word_count': word_count,
        'avg_sentence_length': round(avg_sentence_length, 1),
        'grammar_issues': grammar_issues,
        'spelling_issues': spelling_issues,
    })

@login_required
def verify_essay(request, essay_id):
    """Mark essay as verified"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to verify essays.")
        return redirect('home')
    
    essay = get_object_or_404(Essay, id=essay_id)
    
    if request.method == 'POST':
        essay.is_verified = True
        essay.verified_by = request.user
        essay.verified_at = timezone.now()
        essay.status = 'published'
        essay.save()
        
        # Send notification
        Notification.objects.create(
            user=essay.author,
            notification_type='achievement',
            title='Essay Verified! ✅',
            message=f'Congratulations! Your essay "{essay.title}" has been verified and published.',
            is_important=True
        )
        
        messages.success(request, "Essay verified and published!")
        return redirect('review_essays')
    
    return render(request, 'essay/verify_essay.html', {'essay': essay})

# ================== GRAMMAR & SPELLING TOOLS ==================
@login_required
def grammar_check_tool(request, essay_id):
    """Advanced grammar check tool"""
    essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    
    # You can integrate with external APIs here
    # For example: LanguageTool, Grammarly API, etc.
    
    return render(request, 'essay/grammar_check_tool.html', {
        'essay': essay,
    })





@login_required
def spell_check_tool(request, essay_id):
    """Spell check tool"""
    essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    
    try:
        # Try to import nltk and download data
        import nltk
        from nltk.corpus import words
        
        # Download words corpus if not available
        try:
            nltk.data.find('corpora/words')
        except LookupError:
            # Download the words corpus
            nltk.download('words', quiet=True)
        
        word_list = set(words.words())
        content_words = essay.content.lower().split()
        
        # Find potentially misspelled words
        misspelled = []
        for word in content_words:
            clean_word = re.sub(r'[^\w\s]', '', word)
            if clean_word and clean_word not in word_list and len(clean_word) > 2:
                # Check if it's not a proper noun (capitalized)
                if not clean_word[0].isupper():
                    misspelled.append(clean_word)
        
        misspelled_words = list(set(misspelled))
        
    except Exception as e:
        # If NLTK fails, use a basic dictionary approach
        print(f"NLTK error: {e}")  # Debug print
        
        # Use a basic built-in English word list as fallback
        basic_words = {
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
            'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
            'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
            'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their',
            'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which',
            'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just',
            'him', 'know', 'take', 'people', 'into', 'year', 'your', 'good',
            'some', 'could', 'them', 'see', 'other', 'than', 'then', 'now',
            'look', 'only', 'come', 'its', 'over', 'think', 'also', 'back',
            'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well',
            'way', 'even', 'new', 'want', 'because', 'any', 'these', 'give',
            'day', 'most', 'us', 'is', 'was', 'are', 'were', 'has', 'had',
            'been', 'have', 'did', 'does', 'doing', 'done', 'said', 'says',
            'saying', 'went', 'going', 'gone', 'came', 'coming', 'come',
            'took', 'taking', 'taken', 'gave', 'giving', 'given', 'made',
            'making', 'found', 'finding', 'looked', 'looking', 'wanted',
            'wants', 'needs', 'needed', 'help', 'helps', 'helped', 'calls',
            'called', 'uses', 'used', 'tries', 'tried', 'shows', 'showed',
            'seems', 'seemed', 'means', 'meant', 'comes', 'comes', 'gets',
            'got', 'knows', 'knew', 'known', 'thinks', 'thought', 'feels',
            'felt', 'finds', 'found', 'puts', 'put', 'says', 'said', 'asks',
            'asked', 'sees', 'saw', 'seen', 'tells', 'told', 'writes',
            'wrote', 'written', 'reads', 'read', 'likes', 'liked', 'loves',
            'loved', 'hates', 'hated', 'works', 'worked', 'plays', 'played',
            'runs', 'ran', 'walks', 'walked', 'stands', 'stood', 'sits',
            'sat', 'lies', 'lay', 'lays', 'laid', 'eats', 'ate', 'eaten',
            'drinks', 'drank', 'drunk', 'sleeps', 'slept', 'wakes', 'woke',
            'woken', 'talks', 'talked', 'speaks', 'spoke', 'spoken'
        }
        
        content_words = essay.content.lower().split()
        misspelled = []
        
        for word in content_words:
            clean_word = re.sub(r'[^\w\s]', '', word)
            # Check if word is at least 3 characters and not in basic dictionary
            if (clean_word and len(clean_word) > 2 and 
                clean_word not in basic_words and 
                not clean_word[0].isupper() and
                not clean_word.isdigit()):
                misspelled.append(clean_word)
        
        misspelled_words = list(set(misspelled))
    
    return render(request, 'essay/spell_check_tool.html', {
        'essay': essay,
        'misspelled_words': misspelled_words,
    })

# ================== AUTO CHECK FEATURES ==================
@login_required
def auto_check_essay(request, essay_id):
    """Run automatic checks on essay"""
    essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    
    # Simple automated checks
    checks = {
        'word_count': len(essay.content.split()),
        'sentence_count': len(re.split(r'[.!?]+', essay.content)),
        'paragraph_count': len([p for p in essay.content.split('\n\n') if p.strip()]),
        'avg_word_length': sum(len(word) for word in essay.content.split()) / max(len(essay.content.split()), 1),
    }
    
    # Check for common issues
    issues = []
    
    # Check minimum word count
    if checks['word_count'] < 300:
        issues.append(f"Essay is short ({checks['word_count']} words). Consider expanding to at least 300 words.")
    
    # Check sentence variety
    if checks['sentence_count'] > 0:
        avg_words_per_sentence = checks['word_count'] / checks['sentence_count']
        if avg_words_per_sentence > 25:
            issues.append("Sentences may be too long. Consider breaking them up.")
        elif avg_words_per_sentence < 10:
            issues.append("Sentences may be too short. Consider combining some.")
    
    # Check paragraph structure
    if checks['paragraph_count'] < 3:
        issues.append("Consider adding more paragraphs for better structure.")
    
    return JsonResponse({
        'checks': checks,
        'issues': issues,
        'suggestions': [
            "Use transition words between paragraphs",
            "Include topic sentences in each paragraph",
            "Proofread for spelling and grammar",
            "Ensure proper citation if using sources"
        ]
    })
    
    # essay/views.py
from .utils import check_grammar_issues, check_spelling, analyze_vocabulary

@login_required
def create_essay(request):
    """Create and submit a new essay - SIMPLE"""
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        category = request.POST.get('category', 'general')
        
        if not title or not content:
            messages.error(request, "Title and content are required.")
        else:
            # Simple creation - NO auto-analysis
            essay = Essay.objects.create(
                author=request.user,
                title=title,
                content=content,
                category=category,
                status='submitted'
            )
            
            messages.success(request, "Essay submitted for review!")
            return redirect('essay_detail', essay_id=essay.id)
    
    categories = Essay.CATEGORY_CHOICES
    return render(request, 'essay/create_essay.html', {'categories': categories})

@login_required
def review_essay_detail(request, essay_id):
    """Review essay - Focus on Grammar, Spelling, Vocabulary ONLY"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission.")
        return redirect('home')
    
    essay = get_object_or_404(Essay, id=essay_id)
    
    # Run checks ONLY when admin visits (optional helpers)
    grammar_issues = check_grammar_issues(essay.content)
    spelling_errors = check_spelling(essay.content)
    vocabulary_analysis = analyze_vocabulary(essay.content)
    
    if request.method == 'POST':
        # Admin fills ONLY the 3 feedback fields
        essay.grammar_errors = request.POST.get('grammar_errors', '').strip()
        essay.spelling_errors = request.POST.get('spelling_errors', '').strip()
        essay.vocabulary_feedback = request.POST.get('vocabulary_feedback', '').strip()
        
        # Optional emoji
        if request.POST.get('emoji_feedback'):
            essay.emoji_feedback = request.POST.get('emoji_feedback')
        
        # Mark as reviewed
        essay.is_reviewed = True
        essay.reviewed_by = request.user
        essay.reviewed_at = timezone.now()
        essay.save()
        
        messages.success(request, "Review submitted successfully!")
        return redirect('review_essays')
    
    return render(request, 'essay/review_essay_detail.html', {
        'essay': essay,
        'grammar_issues': grammar_issues,      # Helper for admin
        'spelling_errors': spelling_errors,    # Helper for admin
        'vocabulary_analysis': vocabulary_analysis,  # Helper for admin
    })