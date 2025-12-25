from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db import models
from django.views.decorators.csrf import csrf_exempt
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph as PDFParagraph, Spacer
import json
from django.db.models import Count 
from .models import Essay, UserProfile, Language, Comment, Paragraph

# ================== BASIC PAGES ==================
def home(request):
    try:
        essays = Essay.objects.filter(status='published').select_related('author', 'primary_language').order_by('-created_at')[:10]
        return render(request, 'essay/home.html', {'essays': essays})
    except Exception as e:
        return render(request, 'essay/home.html', {'essays': [], 'error': str(e)})

def about(request):
    return render(request, 'essay/about.html')

def community(request):
    essays = Essay.objects.filter(status='published').order_by('-created_at')[:20]
    return render(request, 'essay/community.html', {'essays': essays})

def essay_list(request):
    """Public essay listing"""
    essays = Essay.objects.filter(status='published').order_by('-created_at')
    return render(request, 'essay/essay_list.html', {'essays': essays})

# ================== AUTHENTICATION ==================
def custom_login(request):
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

@login_required
def custom_logout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')

def register(request):
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
            user = User.objects.create_user(username=username, email=email, password=password)
            UserProfile.objects.create(user=user, role=role)
            login(request, user)
            messages.success(request, f"Account created successfully! Welcome, {username}!")
            return redirect('home')
    
    return render(request, 'essay/register.html')

# ================== USER PAGES ==================
@login_required
def profile(request):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    essays = Essay.objects.filter(author=request.user).select_related('primary_language').order_by('-created_at')
    return render(request, 'essay/profile.html', {'profile': user_profile, 'essays': essays})

@login_required
def dashboard(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    essays = Essay.objects.filter(author=request.user).order_by('-created_at')[:5]
    
    ranked_users = UserProfile.objects.filter(leaderboard_score__gt=0).order_by('-leaderboard_score')
    rank = None
    for idx, user_profile in enumerate(ranked_users, start=1):
        if user_profile.user == request.user:
            rank = idx
            break
    
    return render(request, 'essay/dashboard.html', {'profile': profile, 'essays': essays, 'rank': rank})

# ================== ESSAY CRUD ==================
@login_required
def create_essay(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        language_id = request.POST.get('language')
        
        if not title or not content:
            messages.error(request, "Title and content are required.")
        else:
            language = Language.objects.filter(id=language_id).first()
            essay = Essay.objects.create(
                author=request.user,
                title=title,
                content=content,
                primary_language=language,
                status='submitted'
            )
            essay.calculate_metrics()
            essay.save()
            messages.success(request, "Essay created successfully!")
            return redirect('essay_detail', essay_id=essay.id)
    
    languages = Language.objects.filter(is_active=True)
    return render(request, 'essay/create_essay.html', {'languages': languages})

@login_required
def my_essays(request):
    essays = Essay.objects.filter(author=request.user).order_by('-created_at')
    return render(request, 'essay/my_essays.html', {'essays': essays})

def essay_detail(request, essay_id):
    essay = get_object_or_404(Essay, id=essay_id)
    if essay.status != 'published' and essay.author != request.user:
        messages.error(request, "You don't have permission to view this essay.")
        return redirect('home')
    Essay.objects.filter(id=essay_id).update(views=models.F('views') + 1)
    comments = essay.comments.all().order_by('-created_at')
    return render(request, 'essay/essay_detail.html', {'essay': essay, 'comments': comments})

@login_required
def edit_essay(request, essay_id):
    essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    if request.method == 'POST':
        essay.title = request.POST.get('title', '').strip()
        essay.content = request.POST.get('content', '').strip()
        essay.save()
        messages.success(request, "Essay updated successfully!")
        return redirect('essay_detail', essay_id=essay.id)
    return render(request, 'essay/edit_essay.html', {'essay': essay})

@login_required
def delete_essay(request, essay_id):
    essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    if request.method == 'POST':
        essay.delete()
        messages.success(request, "Essay deleted successfully!")
        return redirect('my_essays')
    return render(request, 'essay/delete_essay.html', {'essay': essay})

# ================== COMMENTS & GRAMMAR ==================
@login_required
@require_POST
def add_comment(request, essay_id):
    essay = get_object_or_404(Essay, id=essay_id)
    content = request.POST.get('content', '').strip()
    if content:
        Comment.objects.create(essay=essay, author=request.user, content=content)
        messages.success(request, "Comment added!")
    else:
        messages.error(request, "Comment cannot be empty.")
    return redirect('essay_detail', essay_id=essay_id)

@login_required
def grammar_check(request, essay_id):
    essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    return render(request, 'essay/essay_detail.html', {'essay': essay})

# ================== PDF DOWNLOAD ==================
def download_pdf(request, essay_id):
    essay = get_object_or_404(Essay, id=essay_id)
    if essay.status != 'published' and essay.author != request.user:
        messages.error(request, "You don't have permission to download this essay.")
        return redirect('home')
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    story.append(PDFParagraph(f"<b>{essay.title}</b>", styles['Title']))
    story.append(PDFParagraph(f"By: {essay.author.username}", styles['Normal']))
    story.append(Spacer(1, 12))
    for para in essay.content.split('\n'):
        story.append(PDFParagraph(para, styles['Normal']))
        story.append(Spacer(1, 6))
    
    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf_data, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{essay.title}.pdf"'
    return response

# ================== LEADERBOARD ==================
def leaderboard(request):
    profiles = UserProfile.objects.filter(leaderboard_score__gt=0).order_by('-leaderboard_score')
    return render(request, 'essay/leaderboard.html', {'profiles': profiles})

# ================== ADMIN DASHBOARD ==================
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('home')
    
    context = {
        'total_essays': Essay.objects.count(),
        'total_users': User.objects.count(),
        'total_comments': Comment.objects.count(),
        'essay_status': dict(Essay.objects.values_list('status').annotate(count=Count('id'))),
        'user_roles': {},  # Update this based on your user model
        'recent_essays': Essay.objects.order_by('-created_at')[:5],
        'recent_users': User.objects.order_by('-date_joined')[:5],
    }
    
    return render(request, 'essay/admin_dashboard.html', context)

# ================== PARAGRAPH WRITING SYSTEM ==================
@login_required
def write_paragraph(request, essay_id):
    essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    
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
            
            return JsonResponse({'success': True, 'paragraph_id': str(paragraph.id)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    paragraphs = essay.paragraphs.all().order_by('paragraph_number')
    return render(request, 'essay/write_paragraph.html', {'essay': essay, 'paragraphs': paragraphs})

@login_required
@require_POST
def save_paragraph(request, essay_id):
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
    essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    paragraph = Paragraph.objects.filter(essay=essay, paragraph_number=paragraph_num).first()
    if paragraph:
        paragraph.unlock()
        messages.success(request, f"Paragraph {paragraph_num} unlocked!")
    else:
        messages.warning(request, f"Paragraph {paragraph_num} not found.")
    return redirect('write_paragraph', essay_id=essay.id)

# ================== ADD THESE FUNCTIONS ==================
def resources(request):
    return render(request, 'essay/resources.html')

@login_required
def write_paragraph_enhanced(request):
    """Render the secure writing page"""
    return render(request, 'essay/write_paragraph_enhanced.html')

@login_required
def save_secure_paragraph(request):
    """Save the securely typed paragraph"""
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        
        if content:
            # Here you can save to your Essay model
            # For example:
            # essay = Essay.objects.create(
            #     user=request.user,
            #     content=content,
            #     title=f"Secure Essay {timezone.now().strftime('%Y-%m-%d %H:%M')}"
            # )
            
            # For now, just return success
            return JsonResponse({
                'success': True,
                'message': 'Paragraph saved successfully!',
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

# ================== LIKE ESSAY FUNCTION ==================
@login_required
def like_essay(request, pk):
    """Toggle like/unlike for an essay"""
    essay = get_object_or_404(Essay, pk=pk)
    
    if request.user in essay.likes.all():
        # User already liked it, so unlike
        essay.likes.remove(request.user)
        messages.success(request, 'You unliked this essay.')
    else:
        # User hasn't liked it yet, so like
        essay.likes.add(request.user)
        messages.success(request, 'You liked this essay!')
    
    return redirect('essay_detail', essay_id=essay.id)