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
import json
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from io import BytesIO
import os 
from django.conf import settings

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
    
    # Calculate user's rank
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
            # Create essay
            essay = Essay.objects.create(
                author=request.user,
                title=title,
                content=content,
                category=category,
                primary_language=language,
                status='submitted'  # Make sure it's submitted, not draft
            )
            
            # FORCE CALCULATE SCORE
            essay.calculate_metrics()
            essay.check_grammar_and_spelling()
            
            # Set a minimum score if none calculated
            if essay.score == 0:
                # Simple scoring based on content length
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
            
            # UPDATE USER PROFILE IMMEDIATELY
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
    
    try:
        from .grammar_checker import grammar_checker
        result = grammar_checker.check_essay(essay.content)
        
        if hasattr(essay, 'grammar_issues'):
            essay.grammar_issues = result.get('grammar_issues', 0)
        if hasattr(essay, 'spelling_issues'):
            essay.spelling_issues = result.get('spelling_issues', 0)
        if hasattr(essay, 'grammar_score'):
            essay.grammar_score = result.get('grammar_score', 0)
        if hasattr(essay, 'spelling_score'):
            essay.spelling_score = result.get('spelling_score', 0)
        if hasattr(essay, 'score'):
            essay.score = result.get('score', 0)
        
        essay.save()
        messages.success(request, "Grammar check completed!")
    except ImportError:
        messages.error(request, "Grammar checker module is not available. Please install required dependencies.")
    except Exception as e:
        messages.error(request, f"Error checking grammar: {str(e)}")
    
    return redirect('essay_detail', essay_id=essay.id)

@login_required
def write_paragraph(request, essay_id):
    essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    
    if not hasattr(essay, 'writing_mode') or essay.writing_mode != 'paragraph':
        messages.warning(request, "This essay is not in paragraph writing mode.")
        return redirect('essay_detail', essay_id=essay.id)
    
    current_paragraph = None
    if hasattr(essay, 'get_current_paragraph'):
        current_paragraph = essay.get_current_paragraph()
    
    paragraphs = essay.paragraphs.all().order_by('paragraph_number')
    
    return render(request, 'essay/write_paragraph.html', {
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
            paragraph.is_locked = False
            paragraph.locked_by = None
            paragraph.locked_at = None
            paragraph.save()
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
    
    # Get ALL user profiles (not just users)
    profiles = UserProfile.objects.all()
    stats_list = []
    
    for profile in profiles:
        # Skip users with no essays
        if profile.total_essays > 0 and profile.leaderboard_score > 0:
            stats_list.append({
                'user': profile.user,
                'total_essays': profile.total_essays,
                'avg_essay_score': round(profile.avg_essay_score, 1),
                'leaderboard_score': round(profile.leaderboard_score, 1),
            })
    
    # Sort by leaderboard score
    stats_list.sort(key=lambda x: x['leaderboard_score'], reverse=True)
    
    # Calculate overall stats
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
        'stats_list': stats_list[:50],  # Top 50
        'total_writers': total_writers,
        'total_essays': total_essays_count,
        'avg_score': round(avg_score, 1),
        'top_score': round(top_score, 1),
        'filter_type': filter_type,
    }
    
    return render(request, 'essay/leaderboard.html', context)

@login_required
def update_all_scores(request):
    """Update scores for all essays (admin function)"""
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

def check_grammar_api(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        content = request.POST.get('content', '')
        
        if not content:
            return JsonResponse({'error': 'No content provided'}, status=400)
        
        try:
            from .grammar_checker import grammar_checker
            result = grammar_checker.check_essay(content)
            return JsonResponse(result)
        except ImportError:
            return JsonResponse({
                'error': 'Grammar checker module not available'
            }, status=503)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

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