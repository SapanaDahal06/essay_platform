from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db import models
from .models import Essay, UserProfile, Competition, Language, Comment, Submission, Paragraph
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from io import BytesIO
import os 
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
import json

def home(request):
    try:
        essays = Essay.objects.filter(status='published').select_related('author', 'primary_language').order_by('-created_at')[:10]
        competitions = Competition.objects.filter(is_active=True)[:5]
        return render(request, 'essay/home.html', {
            'essays': essays,
            'competitions': competitions
        })
    except Exception as e:
        return render(request, 'essay/home.html', {
            'essays': [],
            'competitions': [],
            'error': str(e)
        })

def about(request):
    return render(request, 'essay/about.html')

@login_required
def profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    essays = Essay.objects.filter(author=request.user).select_related('primary_language').order_by('-created_at')
    return render(request, 'essay/profile.html', {
        'profile': user_profile,
        'essays': essays
    })

@login_required
def dashboard(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    essays = Essay.objects.filter(author=request.user).select_related('primary_language').order_by('-created_at')[:5]
    competitions = Competition.objects.filter(is_active=True)[:3]
    
    ranked_users = UserProfile.objects.filter(leaderboard_score__gt=0).order_by('-leaderboard_score')
    
    rank = None
    for idx, user_profile in enumerate(ranked_users, start=1):
        if user_profile.user == request.user:
            rank = idx
            break
    
    return render(request, 'essay/dashboard.html', {
        'profile': profile,
        'essays': essays,
        'competitions': competitions,
        'rank': rank,
    })

def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            messages.error(request, "Please provide both username and password.")
            return render(request, 'essay/login.html')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {username}!")
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
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
            return render(request, 'essay/register.html')
        
        if password != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'essay/register.html')
        
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, 'essay/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'essay/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'essay/register.html')
        
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            UserProfile.objects.create(user=user, role=role)
            login(request, user)
            messages.success(request, f"Account created successfully! Welcome, {username}!")
            return redirect('home')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return render(request, 'essay/register.html')
    
    return render(request, 'essay/register.html')

@login_required
def create_essay(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        category = request.POST.get('category', 'general')
        language_id = request.POST.get('language')
        
        if not title or not content:
            messages.error(request, "Title and content are required.")
            languages = Language.objects.filter(is_active=True)
            return render(request, 'essay/create_essay.html', {'languages': languages})
        
        language = None
        if language_id:
            try:
                language = Language.objects.get(id=language_id, is_active=True)
            except Language.DoesNotExist:
                messages.warning(request, "Selected language not found. Essay created without language.")
        
        try:
            essay = Essay.objects.create(
                author=request.user,
                title=title,
                content=content,
                category=category,
                primary_language=language,
                status='submitted'
            )
            
            essay.calculate_metrics()
            essay.check_grammar_and_spelling()
            
            if essay.score == 0:
                word_count = len(content.split())
                if word_count > 500:
                    essay.score = 85
                elif word_count > 300:
                    essay.score = 75
                elif word_count > 100:
                    essay.score = 65
                else:
                    essay.score = 50
                essay.grammar_score = essay.score
                essay.spelling_score = essay.score
            
            essay.save()
            
            try:
                profile = UserProfile.objects.get(user=request.user)
                profile.update_leaderboard_stats()
            except:
                pass
            
            messages.success(request, "Essay created and submitted successfully!")
            return redirect('essay_detail', essay_id=essay.id)
        except Exception as e:
            messages.error(request, f"Error creating essay: {str(e)}")
    
    languages = Language.objects.filter(is_active=True)
    return render(request, 'essay/create_essay.html', {'languages': languages})

@login_required
def my_essays(request):
    essays = Essay.objects.filter(author=request.user).select_related('primary_language').order_by('-created_at')
    return render(request, 'essay/my_essays.html', {'essays': essays})

def essay_detail(request, essay_id):
    essay = get_object_or_404(Essay.objects.select_related('author', 'primary_language'), id=essay_id)
    
    if essay.status != 'published' and essay.author != request.user:
        messages.error(request, "You don't have permission to view this essay.")
        return redirect('home')
    
    Essay.objects.filter(id=essay_id).update(views=models.F('views') + 1)
    essay.refresh_from_db()
    
    comments = essay.comments.select_related('author').order_by('-created_at')
    return render(request, 'essay/essay_detail.html', {'essay': essay, 'comments': comments})

@login_required
def edit_essay(request, essay_id):
    essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        category = request.POST.get('category', 'general')
        
        if not title or not content:
            messages.error(request, "Title and content are required.")
            languages = Language.objects.filter(is_active=True)
            return render(request, 'essay/edit_essay.html', {'essay': essay, 'languages': languages})
        
        essay.title = title
        essay.content = content
        essay.category = category
        
        language_id = request.POST.get('language')
        if language_id:
            try:
                essay.primary_language = Language.objects.get(id=language_id, is_active=True)
            except Language.DoesNotExist:
                messages.warning(request, "Selected language not found.")
        
        try:
            essay.save()
            messages.success(request, "Essay updated successfully!")
            return redirect('essay_detail', essay_id=essay.id)
        except Exception as e:
            messages.error(request, f"Error updating essay: {str(e)}")
    
    languages = Language.objects.filter(is_active=True)
    return render(request, 'essay/edit_essay.html', {'essay': essay, 'languages': languages})

@login_required
def delete_essay(request, essay_id):
    essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    if request.method == 'POST':
        try:
            essay.delete()
            messages.success(request, "Essay deleted successfully!")
            return redirect('my_essays')
        except Exception as e:
            messages.error(request, f"Error deleting essay: {str(e)}")
            return redirect('essay_detail', essay_id=essay.id)
    return render(request, 'essay/delete_essay.html', {'essay': essay})

def essay_results(request, essay_id):
    essay = get_object_or_404(Essay, id=essay_id)
    
    if essay.status != 'published' and essay.author != request.user:
        messages.error(request, "You don't have permission to view this essay.")
        return redirect('home')
    
    return render(request, 'essay/essay_results.html', {'essay': essay})

def essay_list(request):
    try:
        essays = Essay.objects.filter(status='published').select_related('author', 'primary_language').order_by('-created_at')
        languages = Language.objects.filter(is_active=True)
        
        language_id = request.GET.get('language')
        if language_id:
            essays = essays.filter(primary_language_id=language_id)
        
        category = request.GET.get('category')
        if category:
            essays = essays.filter(category=category)
        
        search_query = request.GET.get('search', '').strip()
        if search_query:
            essays = essays.filter(title__icontains=search_query)
        
        return render(request, 'essay/essay_list.html', {
            'essays': essays,
            'languages': languages,
            'selected_language': language_id,
            'selected_category': category,
            'search_query': search_query
        })
    except Exception as e:
        return HttpResponse(f"Database error: {str(e)}. Please check your database configuration and run migrations.")

@login_required
@require_POST
def like_essay(request, essay_id):
    essay = get_object_or_404(Essay, id=essay_id)
    if essay.likes.filter(id=request.user.id).exists():
        essay.likes.remove(request.user)
        liked = False
    else:
        essay.likes.add(request.user)
        liked = True
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'liked': liked, 'like_count': essay.likes.count()})
    return redirect('essay_detail', essay_id=essay_id)

@login_required
@require_POST
def add_comment(request, essay_id):
    essay = get_object_or_404(Essay, id=essay_id)
    content = request.POST.get('content', '').strip()
    if not content:
        messages.error(request, "Comment cannot be empty.")
        return redirect('essay_detail', essay_id=essay_id)
    Comment.objects.create(essay=essay, author=request.user, content=content)
    messages.success(request, "Comment added successfully!")
    return redirect('essay_detail', essay_id=essay_id)

@login_required
def grammar_check(request, essay_id):
    essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    
    # This is a placeholder - implement grammar checking logic
    messages.info(request, "Grammar check would run here. Implement grammar checking logic.")
    return redirect('essay_detail', essay_id=essay.id)

@login_required
def write_paragraph(request, essay_id):
    essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX request for paragraph writing
        try:
            data = json.loads(request.body)
            paragraph_content = data.get('content', '')
            paragraph_index = data.get('paragraph_index', 0)
            
            # Check grammar (fallback function)
            try:
                from .grammer_checker import check_grammar
                grammar_issues = check_grammar(paragraph_content)
            except:
                grammar_issues = []
            
            # Create or update paragraph
            paragraph, created = Paragraph.objects.get_or_create(
                essay=essay,
                paragraph_number=paragraph_index + 1,
                defaults={'content': paragraph_content}
            )
            
            if not created:
                paragraph.content = paragraph_content
                paragraph.save()
            
            # Lock previous paragraphs if moving to next
            if paragraph_index > 0:
                previous_paragraph = Paragraph.objects.filter(
                    essay=essay, 
                    paragraph_number=paragraph_index
                ).first()
                if previous_paragraph:
                    previous_paragraph.lock(request.user)
            
            return JsonResponse({
                'success': True,
                'grammar_issues': grammar_issues,
                'paragraph_id': str(paragraph.id)
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    # GET request - load existing paragraphs
    if not hasattr(essay, 'writing_mode') or essay.writing_mode != 'paragraph':
        messages.warning(request, "This essay is not in paragraph writing mode.")
        return redirect('essay_detail', essay_id=essay.id)
    
    current_paragraph = essay.get_current_paragraph() if hasattr(essay, 'get_current_paragraph') else None
    paragraphs = essay.paragraphs.all().order_by('paragraph_number')
    
    return render(request, 'essay/write_paragraph_enhanced.html', {
        'essay': essay,
        'current_paragraph': current_paragraph,
        'paragraphs': paragraphs
    })

@login_required
@require_POST
def save_paragraph(request, essay_id):
    essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    content = request.POST.get('content', '').strip()
    
    if hasattr(essay, 'current_paragraph'):
        paragraph_num = int(request.POST.get('paragraph_num', essay.current_paragraph))
    else:
        paragraph_num = int(request.POST.get('paragraph_num', 1))
    
    try:
        paragraph, created = Paragraph.objects.get_or_create(
            essay=essay,
            paragraph_number=paragraph_num,
            defaults={'content': content}
        )
        
        if not created:
            paragraph.content = content
            paragraph.save()
        
        essay.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'paragraph_num': paragraph_num,
                'message': 'Paragraph saved successfully'
            })
        else:
            messages.success(request, f"Paragraph {paragraph_num} saved!")
            return redirect('write_paragraph', essay_id=essay.id)
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
        else:
            messages.error(request, f"Error saving paragraph: {str(e)}")
            return redirect('write_paragraph', essay_id=essay.id)

@login_required
def unlock_paragraph(request, essay_id, paragraph_num):
    essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    
    try:
        paragraph = Paragraph.objects.filter(
            essay=essay,
            paragraph_number=paragraph_num
        ).first()
        
        if paragraph:
            paragraph.unlock()
            messages.success(request, f"Paragraph {paragraph_num} unlocked!")
        else:
            messages.warning(request, f"Paragraph {paragraph_num} not found.")
    except Exception as e:
        messages.error(request, f"Error unlocking paragraph: {str(e)}")
    
    return redirect('write_paragraph', essay_id=essay.id)

def competition_list(request):
    competitions = Competition.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'essay/competition_list.html', {'competitions': competitions})

def competition_detail(request, competition_id):
    competition = get_object_or_404(Competition, id=competition_id)
    submissions = competition.submissions.select_related('essay', 'submitted_by').order_by('-score')
    
    user_submission = None
    if request.user.is_authenticated:
        user_submission = Submission.objects.filter(
            competition=competition,
            submitted_by=request.user
        ).first()
    
    return render(request, 'essay/competition_detail.html', {
        'competition': competition,
        'submissions': submissions,
        'user_submission': user_submission
    })

@login_required
def submit_essay(request, competition_id):
    competition = get_object_or_404(Competition, id=competition_id)
    
    if not hasattr(competition, 'is_open') or not competition.is_open:
        messages.error(request, "This competition is not currently open for submissions.")
        return redirect('competition_detail', competition_id=competition_id)
    
    if request.method == 'POST':
        essay_id = request.POST.get('essay_id')
        
        if not essay_id:
            messages.error(request, "Please select an essay to submit.")
            essays = Essay.objects.filter(author=request.user, status='published')
            return render(request, 'essay/submit_essay.html', {
                'competition': competition,
                'essays': essays
            })
        
        essay = get_object_or_404(Essay, id=essay_id, author=request.user)
        
        existing_submission = Submission.objects.filter(
            competition=competition,
            submitted_by=request.user
        ).first()
        
        if existing_submission:
            messages.warning(request, "You have already submitted to this competition.")
        else:
            try:
                Submission.objects.create(
                    competition=competition,
                    essay=essay,
                    submitted_by=request.user
                )
                messages.success(request, "Essay submitted successfully!")
            except Exception as e:
                messages.error(request, f"Error submitting essay: {str(e)}")
        
        return redirect('competition_detail', competition_id=competition_id)
    
    essays = Essay.objects.filter(author=request.user, status='published')
    return render(request, 'essay/submit_essay.html', {
        'competition': competition,
        'essays': essays
    })

@login_required
def my_submissions(request):
    submissions = Submission.objects.filter(
        submitted_by=request.user
    ).select_related('competition', 'essay').order_by('-submitted_at')
    return render(request, 'essay/my_submissions.html', {'submissions': submissions})

def winners(request):
    winning_submissions = Submission.objects.filter(
        rank__lte=3,
        rank__isnull=False
    ).select_related('competition', 'essay', 'submitted_by').order_by('competition', 'rank')
    return render(request, 'essay/winners.html', {'winners': winning_submissions})

def community(request):
    essays = Essay.objects.filter(
        status='published'
    ).select_related('author', 'primary_language').order_by('-created_at')[:20]
    return render(request, 'essay/community.html', {'essays': essays})

def resources(request):
    return render(request, 'essay/resources.html')

def leaderboard(request):
    filter_type = request.GET.get('filter', 'all')
    
    profiles = UserProfile.objects.all()
    stats_list = []
    
    for profile in profiles:
        if profile.total_essays > 0 and profile.leaderboard_score > 0:
            stats_list.append({
                'user': profile.user,
                'total_essays': profile.total_essays,
                'avg_essay_score': round(profile.avg_essay_score, 1),
                'leaderboard_score': round(profile.leaderboard_score, 1),
            })
    
    stats_list.sort(key=lambda x: x['leaderboard_score'], reverse=True)
    
    all_essays = Essay.objects.all()
    total_writers = len(stats_list)
    total_essays_count = all_essays.count()
    
    if all_essays.exists():
        scores = [essay.score for essay in all_essays if essay.score > 0]
        avg_score = sum(scores) / len(scores) if scores else 0
        top_score = max(scores) if scores else 0
    else:
        avg_score = 0
        top_score = 0
    
    context = {
        'stats_list': stats_list[:50],
        'total_writers': total_writers,
        'total_essays': total_essays_count,
        'avg_score': round(avg_score, 1),
        'top_score': round(top_score, 1),
        'filter_type': filter_type,
    }
    
    return render(request, 'essay/leaderboard.html', context)

@login_required
def update_all_scores(request):
    if not request.user.is_superuser:
        messages.error(request, "Only administrators can update scores.")
        return redirect('home')
    
    try:
        essays = Essay.objects.all()
        updated_count = 0
        
        for essay in essays:
            essay.calculate_metrics()
            essay.check_grammar_and_spelling()
            essay.save(skip_checks=True)
            updated_count += 1
        
        messages.success(request, f"Successfully updated scores for {updated_count} essays!")
        return redirect('leaderboard')
    
    except Exception as e:
        messages.error(request, f"Error updating scores: {str(e)}")
        return redirect('leaderboard')

def get_languages(request):
    try:
        languages = Language.objects.filter(is_active=True).values('id', 'code', 'name')
        return JsonResponse(list(languages), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def check_auth(request):
    return JsonResponse({
        'authenticated': request.user.is_authenticated,
        'username': request.user.username if request.user.is_authenticated else None
    })

def get_paragraphs(request, essay_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        essay = get_object_or_404(Essay, id=essay_id)
        
        if essay.author != request.user and essay.status != 'published':
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        paragraphs = essay.paragraphs.all().order_by('paragraph_number').values(
            'id', 'paragraph_number', 'content', 'is_locked', 'word_count'
        )
        
        return JsonResponse(list(paragraphs), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def admin_essay_list(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    essays = Essay.objects.all().select_related('author', 'primary_language').order_by('-created_at')
    return render(request, 'essay/admin_essay_list.html', {'essays': essays})

def download_pdf(request, essay_id):
    essay = get_object_or_404(Essay, id=essay_id)
    
    if essay.status != 'published' and essay.author != request.user:
        messages.error(request, "You don't have permission to download this PDF.")
        return redirect('essay_detail', essay_id=essay.id)
    
    try:
        buffer = BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72, leftMargin=72,
            topMargin=72, bottomMargin=18
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1
        )
        story.append(Paragraph(essay.title, title_style))
        
        author_style = ParagraphStyle(
            'AuthorStyle',
            parent=styles['Normal'],
            fontSize=14,
            textColor='#666666',
            alignment=1
        )
        story.append(Paragraph(f"By: {essay.author.username}", author_style))
        
        date_str = essay.created_at.strftime("%B %d, %Y")
        story.append(Paragraph(f"Submitted on: {date_str}", author_style))
        story.append(Spacer(1, 30))
        
        content_style = ParagraphStyle(
            'ContentStyle',
            parent=styles['Normal'],
            fontSize=12,
            leading=18,
            spaceBefore=12,
            spaceAfter=12
        )
        
        paragraphs = essay.content.split('\n')
        for para in paragraphs:
            if para.strip():
                story.append(Paragraph(para.strip(), content_style))
                story.append(Spacer(1, 12))
        
        story.append(Spacer(1, 50))
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor='#888888',
            alignment=1
        )
        story.append(Paragraph(f"Generated from WriteVerse", footer_style))
        
        doc.build(story)
        
        pdf_data = buffer.getvalue()
        buffer.close()
        
        media_dir = os.path.join(settings.MEDIA_ROOT, 'essays', 'pdfs')
        os.makedirs(media_dir, exist_ok=True)
        
        safe_title = "".join(c for c in essay.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"essay_{essay.id}_{essay.author.username}_{safe_title}.pdf"
        filepath = os.path.join(media_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(pdf_data)
        
        print(f"✅ PDF saved to: {filepath}")
        print(f"✅ File size: {len(pdf_data)} bytes")
        
        essay.pdf_file.name = f'essays/pdfs/{filename}'
        essay.save()
        
        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{essay.author.username}_{essay.title}.pdf"'
        return response
        
    except Exception as e:
        messages.error(request, f"Error generating PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return redirect('essay_detail', essay_id=essay.id)

# ================== API VIEWS ==================

@csrf_exempt
@login_required
def save_paragraph_api(request):
    """Save a single paragraph via API"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            essay_id = data.get('essay_id')
            content = data.get('content')
            paragraph_index = data.get('paragraph_index', 0)
            
            essay = Essay.objects.get(id=essay_id, author=request.user)
            
            paragraph, created = Paragraph.objects.get_or_create(
                essay=essay,
                paragraph_number=paragraph_index + 1,
                defaults={'content': content}
            )
            
            if not created:
                paragraph.content = content
                paragraph.save()
            
            return JsonResponse({'success': True, 'paragraph_id': str(paragraph.id)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

@csrf_exempt
def check_grammar_api(request):
    """Check grammar for text via API"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            text = data.get('text', '')
            
            # Try to use grammar checker
            try:
                from .grammer_checker import check_grammar
                issues = check_grammar(text)
            except ImportError:
                issues = []
            
            return JsonResponse({'issues': issues})
        except Exception as e:
            return JsonResponse({'issues': [], 'error': str(e)})
    return JsonResponse({'issues': []})

@csrf_exempt
@login_required
def final_submit_api(request):
    """Final submit an essay via API"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            essay_id = data.get('essay_id')
            
            essay = Essay.objects.get(id=essay_id, author=request.user)
            essay.status = 'submitted'
            essay.save()
            
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('essay_detail', args=[essay.id])
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

@csrf_exempt
@login_required
def update_status_api(request):
    """Update essay status via API"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            essay_id = data.get('essay_id')
            status = data.get('status')
            
            essay = Essay.objects.get(id=essay_id, author=request.user)
            essay.status = status
            essay.save()
            
            return JsonResponse({'success': True, 'status': status})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

@login_required
def grammar_check(request, essay_id):
    essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    
    # Check if grammar_checker module exists
    try:
        # Try to import and use your grammar checker
        from .grammer_checker import check_grammar
        
        if essay.content:
            issues = check_grammar(essay.content)
            
            # Update essay with grammar issues count
            if hasattr(essay, 'grammar_issues'):
                essay.grammar_issues = len(issues)
                essay.save()
            
            messages.success(request, f"Found {len(issues)} grammar issues!")
            
            # Return to essay detail page with issues
            return render(request, 'essay/essay_detail.html', {
                'essay': essay,
                'grammar_issues': issues
            })
        else:
            messages.warning(request, "No content to check!")
            
    except ImportError:
        # If grammar checker doesn't exist, use a simple one
        if essay.content:
            # Simple grammar check logic
            import re
            
            issues = []
            content = essay.content
            
            # Check for lowercase 'i'
            if re.search(r'\bi\s+', content):
                issues.append("Use capital 'I' when referring to yourself")
            
            # Check for double spaces
            if '  ' in content:
                issues.append("Avoid double spaces")
            
            # Check sentence capitalization
            sentences = re.split(r'[.!?]', content)
            for i, sentence in enumerate(sentences):
                sentence = sentence.strip()
                if sentence and not sentence[0].isupper():
                    issues.append(f"Sentence {i+1} should start with capital letter")
            
            messages.success(request, f"Basic check found {len(issues)} issues!")
            
            return render(request, 'essay/essay_detail.html', {
                'essay': essay,
                'grammar_issues': issues
            })
        else:
            messages.warning(request, "No content to check!")
    
    return redirect('essay_detail', essay_id=essay.id)



# ========== PARAGRAPH WRITING SYSTEM ==========

@login_required
def paragraph_writer(request, essay_id):
    """Main paragraph writing interface"""
    essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    
    # Ensure essay is in paragraph mode
    if essay.writing_mode != 'paragraph':
        essay.writing_mode = 'paragraph'
        essay.max_paragraphs = 5
        essay.save()
    
    # Get or create paragraphs
    paragraphs = []
    for i in range(1, essay.max_paragraphs + 1):
        paragraph, created = Paragraph.objects.get_or_create(
            essay=essay,
            paragraph_number=i,
            defaults={'content': ''}
        )
        paragraphs.append(paragraph)
    
    return render(request, 'essay/paragraph_writer.html', {
        'essay': essay,
        'paragraphs': paragraphs,
        'max_paragraphs': range(1, essay.max_paragraphs + 1)
    })

@csrf_exempt
@login_required
def api_save_paragraph(request):
    """API: Save paragraph"""
    from .paragraph_writer import ParagraphWriter
    return ParagraphWriter.save_paragraph(request)

@csrf_exempt
@login_required
def api_check_grammar(request):
    """API: Check grammar"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            text = data.get('text', '')
            language = data.get('language', 'en-US')
            
            from .paragraph_writer import ParagraphWriter
            issues = ParagraphWriter.check_grammar(text, language)
            
            return JsonResponse({'issues': issues})
        except Exception as e:
            return JsonResponse({'issues': [], 'error': str(e)})
    
    return JsonResponse({'issues': []})

@csrf_exempt
@login_required
def api_submit_essay(request):
    """API: Submit complete essay"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            essay_id = data.get('essay_id')
            
            essay = Essay.objects.get(id=essay_id, author=request.user)
            
            # Combine all paragraphs into essay content
            paragraphs = essay.paragraphs.all().order_by('paragraph_number')
            full_content = '\n\n'.join([p.content for p in paragraphs if p.content.strip()])
            
            essay.content = full_content
            essay.status = 'submitted'
            essay.save()
            
            # Generate PDF
            try:
                # Call your PDF generation function
                from .views import download_pdf
                response = download_pdf(request, essay_id)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Essay submitted and PDF generated!',
                    'redirect_url': reverse('essay_detail', args=[essay.id])
                })
            except:
                return JsonResponse({
                    'success': True,
                    'message': 'Essay submitted!',
                    'redirect_url': reverse('essay_detail', args=[essay.id])
                })
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)




# ========== ADMIN DASHBOARD ==========

@login_required
def admin_dashboard(request):
    """Main admin dashboard - only accessible by admin users"""
    # Check if user is admin
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Access denied. Admin only.")
        return redirect('home')
    
    # Get statistics
    total_essays = Essay.objects.count()
    total_users = User.objects.count()
    total_competitions = Competition.objects.count()
    total_submissions = Submission.objects.count()
    
    # Get recent activities
    recent_essays = Essay.objects.all().order_by('-created_at')[:10]
    recent_users = User.objects.all().order_by('-date_joined')[:10]
    recent_submissions = Submission.objects.all().select_related('essay', 'competition', 'submitted_by').order_by('-submitted_at')[:10]
    
    # Get essay statistics by status
    essay_status = {
        'draft': Essay.objects.filter(status='draft').count(),
        'writing': Essay.objects.filter(status='writing').count(),
        'submitted': Essay.objects.filter(status='submitted').count(),
        'published': Essay.objects.filter(status='published').count(),
    }
    
    # Get user statistics by role
    user_roles = {}
    for profile in UserProfile.objects.all():
        role = profile.role
        user_roles[role] = user_roles.get(role, 0) + 1
    
    context = {
        'total_essays': total_essays,
        'total_users': total_users,
        'total_competitions': total_competitions,
        'total_submissions': total_submissions,
        'recent_essays': recent_essays,
        'recent_users': recent_users,
        'recent_submissions': recent_submissions,
        'essay_status': essay_status,
        'user_roles': user_roles,
    }
    
    return render(request, 'essay/admin_dashboard.html', context)

@login_required
def admin_essay_management(request):
    """Admin essay management page"""
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Access denied. Admin only.")
        return redirect('home')
    
    essays = Essay.objects.all().select_related('author', 'primary_language').order_by('-created_at')
    
    # Filtering
    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')
    
    if status_filter:
        essays = essays.filter(status=status_filter)
    if category_filter:
        essays = essays.filter(category=category_filter)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        essays = essays.filter(
            models.Q(title__icontains=search_query) |
            models.Q(content__icontains=search_query) |
            models.Q(author__username__icontains=search_query)
        )
    
    context = {
        'essays': essays,
        'status_choices': Essay.STATUS_CHOICES,
        'category_choices': Essay.CATEGORY_CHOICES,
    }
    
    return render(request, 'essay/admin_essay_management.html', context)

@login_required
def admin_user_management(request):
    """Admin user management page"""
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Access denied. Admin only.")
        return redirect('home')
    
    users = User.objects.all().order_by('-date_joined')
    user_profiles = UserProfile.objects.all().select_related('user')
    
    # Filtering
    role_filter = request.GET.get('role', '')
    if role_filter:
        user_profiles = user_profiles.filter(role=role_filter)
        user_ids = user_profiles.values_list('user_id', flat=True)
        users = users.filter(id__in=user_ids)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            models.Q(username__icontains=search_query) |
            models.Q(email__icontains=search_query) |
            models.Q(first_name__icontains=search_query) |
            models.Q(last_name__icontains=search_query)
        )
    
    context = {
        'users': users,
        'user_profiles': user_profiles,
        'role_choices': UserProfile.ROLE_CHOICES,
    }
    
    return render(request, 'essay/admin_user_management.html', context)

@login_required
def admin_competition_management(request):
    """Admin competition management page"""
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Access denied. Admin only.")
        return redirect('home')
    
    competitions = Competition.objects.all().order_by('-created_at')
    
    # Filtering
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        competitions = competitions.filter(is_active=True)
    elif status_filter == 'inactive':
        competitions = competitions.filter(is_active=False)
    
    context = {
        'competitions': competitions,
    }
    
    return render(request, 'essay/admin_competition_management.html', context)

@login_required
def admin_analytics(request):
    """Admin analytics page with charts and graphs"""
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Access denied. Admin only.")
        return redirect('home')
    
    # Get data for charts
    from django.db.models import Count, Avg, Q
    import datetime
    
    # Essay growth (last 30 days)
    thirty_days_ago = timezone.now() - datetime.timedelta(days=30)
    daily_essays = Essay.objects.filter(
        created_at__gte=thirty_days_ago
    ).extra({
        'date': "DATE(created_at)"
    }).values('date').annotate(count=Count('id')).order_by('date')
    
    # User growth
    daily_users = User.objects.filter(
        date_joined__gte=thirty_days_ago
    ).extra({
        'date': "DATE(date_joined)"
    }).values('date').annotate(count=Count('id')).order_by('date')
    
    # Top writers
    top_writers = User.objects.annotate(
        essay_count=Count('essays')
    ).filter(essay_count__gt=0).order_by('-essay_count')[:10]
    
    # Top essays by score
    top_essays = Essay.objects.filter(score__gt=0).order_by('-score')[:10]
    
    # Essay quality distribution
    quality_distribution = {
        'excellent': Essay.objects.filter(score__gte=90).count(),
        'good': Essay.objects.filter(score__gte=80, score__lt=90).count(),
        'average': Essay.objects.filter(score__gte=70, score__lt=80).count(),
        'poor': Essay.objects.filter(score__lt=70).count(),
    }
    
    context = {
        'daily_essays': list(daily_essays),
        'daily_users': list(daily_users),
        'top_writers': top_writers,
        'top_essays': top_essays,
        'quality_distribution': quality_distribution,
    }
    
    return render(request, 'essay/admin_analytics.html', context)

@login_required
def admin_system_settings(request):
    """Admin system settings page"""
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Access denied. Admin only.")
        return redirect('home')
    
    if request.method == 'POST':
        # Handle settings update
        messages.success(request, "Settings updated successfully!")
        return redirect('admin_system_settings')
    
    # Get current settings (you can store these in database)
    settings = {
        'site_name': 'Essay Platform',
        'site_description': 'Essay writing and competition platform',
        'registration_open': True,
        'competition_mode': True,
        'max_essay_length': 5000,
        'min_essay_length': 100,
        'grammar_check_enabled': True,
        'auto_grade_essays': True,
    }
    
    return render(request, 'essay/admin_system_settings.html', {'settings': settings})