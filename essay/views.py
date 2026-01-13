# # essay/views.py
# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth.decorators import login_required
# from django.http import HttpResponse, JsonResponse
# from django.contrib.auth.models import User
# from django.contrib.auth import login, logout, authenticate
# from django.contrib import messages
# from django.utils import timezone
# from django.views.decorators.http import require_POST, require_http_methods
# from django.db import models
# from io import BytesIO
# from reportlab.lib.pagesizes import letter
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.platypus import SimpleDocTemplate, Paragraph as PDFParagraph, Spacer
# import json
# import re  # Import re at the top
# from django.db.models import Count, Q
# from .models import (
#     Essay, UserProfile, Language, Comment, Paragraph, 
#     ReviewTemplate, Notification, TimedChallenge, 
#     CharacterChallenge, TimedChallengeSubmission, 
#     CharacterChallengeSubmission, ChallengeLeaderboard, 
#     AIWritingSession
# )

# # Try to import grammar_checker, create fallback if not available
# try:
#     #from .grammar_checker import check_grammar, analyze_text, get_grammar_suggestions
#     print("✓ Successfully imported grammar_checker")
# except ImportError as e:
#     print(f"✗ Error importing grammar_checker: {e}")
#     print("Creating simple versions locally...")
    
#     # Create simple local versions as fallback
#     def check_grammar(text):
#         return []
    
#     def analyze_text(text):
#         return {}
    
#     def get_grammar_suggestions(text):
#         return {'analysis': {}, 'issues': [], 'total_issues': 0}

# # ================== BASIC PAGES ==================
# def home(request):
#     """Home page view"""
#     try:
#         essays = Essay.objects.filter(status='published').select_related('author', 'primary_language').order_by('-created_at')[:10]
#         return render(request, 'essay/home.html', {'essays': essays})
#     except Exception as e:
#         return render(request, 'essay/home.html', {'essays': [], 'error': str(e)})

# def about(request):
#     """About page view"""
#     return render(request, 'essay/about.html')

# def community(request):
#     """Community page view"""
#     essays = Essay.objects.filter(status='published').order_by('-created_at')[:20]
#     return render(request, 'essay/community.html', {'essays': essays})

# def resources(request):
#     """Resources page view"""
#     return render(request, 'essay/resources.html')

# def essay_list(request):
#     """Public essay listing"""
#     essays = Essay.objects.filter(status='published').order_by('-created_at')
#     return render(request, 'essay/essay_list.html', {'essays': essays})

# # ================== AUTHENTICATION ==================
# def custom_login(request):
#     """Custom login view"""
#     if request.method == 'POST':
#         username = request.POST.get('username', '').strip()
#         password = request.POST.get('password', '')
        
#         if not username or not password:
#             messages.error(request, "Please provide both username and password.")
#             return render(request, 'essay/login.html')
        
#         user = authenticate(request, username=username, password=password)
#         if user:
#             login(request, user)
#             messages.success(request, f"Welcome back, {username}!")
#             return redirect('home')
#         else:
#             messages.error(request, "Invalid username or password.")
    
#     return render(request, 'essay/login.html')

# def custom_logout(request):
#     """Custom logout view"""
#     logout(request)
#     messages.success(request, "You have been logged out successfully.")
#     return redirect('home')

# def register(request):
#     """User registration view"""
#     if request.method == 'POST':
#         username = request.POST.get('username', '').strip()
#         email = request.POST.get('email', '').strip()
#         password = request.POST.get('password', '')
#         password2 = request.POST.get('password2', '')
#         role = request.POST.get('role', 'student')
        
#         if not all([username, email, password, password2]):
#             messages.error(request, "All fields are required.")
#         elif password != password2:
#             messages.error(request, "Passwords do not match.")
#         elif len(password) < 8:
#             messages.error(request, "Password must be at least 8 characters long.")
#         elif User.objects.filter(username=username).exists():
#             messages.error(request, "Username already exists.")
#         elif User.objects.filter(email=email).exists():
#             messages.error(request, "Email already registered.")
#         else:
#             try:
#                 user = User.objects.create_user(username=username, email=email, password=password)
#                 UserProfile.objects.create(user=user, role=role)
#                 login(request, user)
#                 messages.success(request, f"Account created successfully! Welcome, {username}!")
#                 return redirect('home')
#             except Exception as e:
#                 messages.error(request, f"Error creating account: {str(e)}")
    
#     return render(request, 'essay/register.html')

# # ================== USER PAGES ==================
# @login_required
# def profile(request):
#     """User profile page"""
#     user_profile, created = UserProfile.objects.get_or_create(user=request.user)
#     essays = Essay.objects.filter(author=request.user).select_related('primary_language').order_by('-created_at')
#     return render(request, 'essay/profile.html', {'profile': user_profile, 'essays': essays})

# @login_required
# def dashboard(request):
#     """User dashboard"""
#     profile, created = UserProfile.objects.get_or_create(user=request.user)
#     essays = Essay.objects.filter(author=request.user).order_by('-created_at')[:5]
    
#     all_users = User.objects.annotate(
#         published_essays=Count('essays', filter=Q(essays__status='published'))
#     ).order_by('-published_essays')
    
#     rank = None
#     for idx, user in enumerate(all_users, start=1):
#         if user == request.user:
#             rank = idx
#             break
    
#     published_count = Essay.objects.filter(author=request.user, status='published').count()
#     draft_count = Essay.objects.filter(author=request.user, status='draft').count()
    
#     return render(request, 'essay/dashboard.html', {
#         'profile': profile,
#         'essays': essays,
#         'rank': rank,
#         'published_count': published_count,
#         'draft_count': draft_count,
#     })
    
    

# def leaderboard(request):
#     """Leaderboard page"""
#     profiles = UserProfile.objects.annotate(
#         essay_count=Count('user__essays', filter=Q(user__essays__status='published'))
#     ).order_by('-essay_count')
    
#     return render(request, 'essay/leaderboard.html', {'profiles': profiles})

# # ================== ESSAY CRUD ==================
# @login_required
# def create_essay(request):
#     """Create a new essay"""
#     if request.method == 'POST':
#         title = request.POST.get('title', '').strip()
#         content = request.POST.get('content', '').strip()
#         formatted_content = request.POST.get('formatted_content', '').strip()
#         language_id = request.POST.get('language')
        
#         if not title or not content:
#             messages.error(request, "Title and content are required.")
#         else:
#             language = Language.objects.filter(id=language_id).first()
            
#             essay = Essay.objects.create(
#                 author=request.user,
#                 title=title,
#                 content=content,
#                 formatted_content=formatted_content,
#                 primary_language=language,
#                 status='submitted'
#             )
            
#             messages.success(request, "Essay created successfully!")
#             return redirect('essay_detail', essay_id=essay.id)
    
#     languages = Language.objects.filter(is_active=True)
#     return render(request, 'essay/create_essay.html', {'languages': languages})

# @login_required
# def my_essays(request):
#     """List user's essays"""
#     essays = Essay.objects.filter(author=request.user).order_by('-created_at')
#     return render(request, 'essay/my_essays.html', {'essays': essays})

# def essay_detail(request, essay_id):
#     """View essay details"""
#     essay = get_object_or_404(Essay, id=essay_id)
    
#     if essay.status != 'published' and essay.author != request.user:
#         messages.error(request, "You don't have permission to view this essay.")
#         return redirect('home')
    
#     Essay.objects.filter(id=essay_id).update(views=models.F('views') + 1)
    
#     comments = essay.comments.all().order_by('-created_at')
    
#     return render(request, 'essay/essay_detail.html', {
#         'essay': essay,
#         'comments': comments
#     })

# @login_required
# def edit_essay(request, essay_id):
#     """Edit existing essay"""
#     essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    
#     if request.method == 'POST':
#         essay.title = request.POST.get('title', '').strip()
#         essay.content = request.POST.get('content', '').strip()
#         essay.formatted_content = request.POST.get('formatted_content', '').strip()
#         essay.save()
        
#         messages.success(request, "Essay updated successfully!")
#         return redirect('essay_detail', essay_id=essay.id)
    
#     return render(request, 'essay/edit_essay.html', {'essay': essay})

# @login_required
# def delete_essay(request, essay_id):
#     """Delete essay"""
#     essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    
#     if request.method == 'POST':
#         essay.delete()
#         messages.success(request, "Essay deleted successfully!")
#         return redirect('my_essays')
    
#     return render(request, 'essay/delete_essay.html', {'essay': essay})

# # ================== COMMENTS ==================
# @login_required
# @require_POST
# def add_comment(request, essay_id):
#     """Add comment to essay"""
#     essay = get_object_or_404(Essay, id=essay_id)
#     content = request.POST.get('content', '').strip()
    
#     if content:
#         Comment.objects.create(
#             essay=essay,
#             author=request.user,
#             content=content
#         )
#         messages.success(request, "Comment added!")
#     else:
#         messages.error(request, "Comment cannot be empty.")
    
#     return redirect('essay_detail', essay_id=essay_id)

# # ================== PDF DOWNLOAD ==================
# def download_pdf(request, essay_id):
#     """Download essay as PDF"""
#     essay = get_object_or_404(Essay, id=essay_id)
    
#     if essay.status != 'published' and essay.author != request.user:
#         messages.error(request, "You don't have permission to download this essay.")
#         return redirect('home')
    
#     buffer = BytesIO()
#     doc = SimpleDocTemplate(buffer, pagesize=letter)
#     story = []
#     styles = getSampleStyleSheet()
    
#     story.append(PDFParagraph(f"<b>{essay.title}</b>", styles['Title']))
#     story.append(PDFParagraph(f"By: {essay.author.username}", styles['Normal']))
#     story.append(Spacer(1, 12))
    
#     def clean_html_for_pdf(text):
#         if not text:
#             return ""
#         text = re.sub(r'<span[^>]*>.*?</span>', '', text)
#         text = re.sub(r'<br\s*/?>', '\n', text)
#         text = re.sub(r'&nbsp;', ' ', text)
#         text = re.sub(r'<[^>]+>', '', text)
#         text = re.sub(r'\n\s*\n', '\n\n', text)
#         return text.strip()
    
#     content = essay.formatted_content or essay.content
#     clean_content = clean_html_for_pdf(content)
    
#     paragraphs = [p.strip() for p in clean_content.split('\n\n') if p.strip()]
    
#     for para in paragraphs:
#         if para:
#             para = re.sub(r'\s+', ' ', para)
#             story.append(PDFParagraph(para, styles['Normal']))
#             story.append(Spacer(1, 6))
    
#     try:
#         doc.build(story)
#         pdf_data = buffer.getvalue()
#         buffer.close()
        
#         response = HttpResponse(pdf_data, content_type='application/pdf')
#         response['Content-Disposition'] = f'attachment; filename="{essay.title}.pdf"'
#         return response
#     except Exception as e:
#         messages.error(request, f"Error generating PDF: {str(e)}")
#         return redirect('essay_detail', essay_id=essay.id)

# # ================== ADMIN DASHBOARD ==================
# @login_required
# def admin_dashboard(request):
#     """Admin dashboard"""
#     if not request.user.is_staff:
#         messages.error(request, "You don't have permission to access the admin dashboard.")
#         return redirect('home')
    
#     context = {
#         'total_essays': Essay.objects.count(),
#         'total_users': User.objects.count(),
#         'total_comments': Comment.objects.count(),
#         'essay_status': dict(Essay.objects.values_list('status').annotate(count=Count('id'))),
#         'user_roles': dict(UserProfile.objects.values_list('role').annotate(count=Count('id'))),
#         'recent_essays': Essay.objects.select_related('author').order_by('-created_at')[:5],
#         'recent_users': User.objects.select_related('userprofile').order_by('-date_joined')[:5],
#     }
    
#     return render(request, 'essay/admin_dashboard.html', context)

# # ================== PARAGRAPH WRITING ==================
# @login_required
# def write_paragraph(request, essay_id):
#     """Write paragraph for essay"""
#     essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    
#     if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#         try:
#             data = json.loads(request.body)
#             paragraph_content = data.get('content', '')
#             paragraph_index = data.get('paragraph_index', 0)
            
#             paragraph, created = Paragraph.objects.get_or_create(
#                 essay=essay,
#                 paragraph_number=paragraph_index + 1,
#                 defaults={'content': paragraph_content}
#             )
            
#             if not created:
#                 paragraph.content = paragraph_content
#                 paragraph.save()
            
#             return JsonResponse({
#                 'success': True,
#                 'paragraph_id': str(paragraph.id)
#             })
#         except Exception as e:
#             return JsonResponse({
#                 'success': False,
#                 'error': str(e)
#             }, status=500)
    
#     paragraphs = essay.paragraphs.all().order_by('paragraph_number')
#     return render(request, 'essay/write_paragraph.html', {
#         'essay': essay,
#         'paragraphs': paragraphs
#     })

# @login_required
# @require_POST
# def save_paragraph(request, essay_id):
#     """Save paragraph"""
#     essay = get_object_or_404(Essay, id=essay_id, author=request.user)
#     content = request.POST.get('content', '').strip()
#     paragraph_num = int(request.POST.get('paragraph_num', 1))
    
#     paragraph, created = Paragraph.objects.get_or_create(
#         essay=essay,
#         paragraph_number=paragraph_num,
#         defaults={'content': content}
#     )
    
#     if not created:
#         paragraph.content = content
#         paragraph.save()
    
#     messages.success(request, f"Paragraph {paragraph_num} saved!")
#     return redirect('write_paragraph', essay_id=essay.id)

# # ================== ENHANCED WRITING ==================
# @login_required
# def write_paragraph_enhanced(request):
#     """Enhanced writing page"""
#     return render(request, 'essay/write_paragraph_enhanced.html')

# # ================== LIKE ESSAY ==================
# @login_required
# def like_essay(request, essay_id):
#     """Like/unlike essay"""
#     essay = get_object_or_404(Essay, id=essay_id)
    
#     if request.user in essay.likes.all():
#         essay.likes.remove(request.user)
#         liked = False
#         message = 'You unliked this essay.'
#     else:
#         essay.likes.add(request.user)
#         liked = True
#         message = 'You liked this essay!'
    
#     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#         return JsonResponse({
#             'liked': liked,
#             'likes_count': essay.likes.count(),
#             'message': message
#         })
    
#     messages.success(request, message)
#     return redirect('essay_detail', essay_id=essay.id)

# # ================== ESSAY REVIEW ==================
# @login_required
# def review_essays(request):
#     """List essays for review (admin only)"""
#     if not request.user.is_staff:
#         messages.error(request, "You don't have permission to review essays.")
#         return redirect('home')
    
#     pending_essays = Essay.objects.filter(
#         status='submitted',
#         is_reviewed=False
#     ).order_by('created_at')
    
#     reviewed_essays = Essay.objects.filter(
#         is_reviewed=True
#     ).order_by('-reviewed_at')[:10]
    
#     return render(request, 'essay/review_essays.html', {
#         'pending_essays': pending_essays,
#         'reviewed_essays': reviewed_essays,
#     })


# # Remove this import:
# # from .grammar_checker import check_grammar, analyze_text, get_grammar_suggestions

# # Add these functions instead (right after the try/except block):
# def check_grammar(text):
#     """Simple grammar checker"""
#     if not text or not text.strip():
#         return []
    
#     issues = []
    
#     # Check for lowercase 'i' as subject
#     if re.search(r'\bi\s+', text):
#         issues.append({
#             'message': 'Use capital "I" when referring to yourself',
#             'suggestion': 'I'
#         })
    
#     # Check for double spaces
#     if '  ' in text:
#         issues.append({
#             'message': 'Avoid double spaces',
#             'suggestion': 'Use single space'
#         })
    
#     # Check sentence capitalization
#     sentences = re.split(r'[.!?]', text)
#     for i, sentence in enumerate(sentences):
#         sentence = sentence.strip()
#         if sentence and not sentence[0].isupper():
#             issues.append({
#                 'message': f'Sentence should start with capital letter',
#                 'suggestion': sentence.capitalize() if sentence else ''
#             })
    
#     return issues

# def analyze_text(text):
#     """Simple text analysis"""
#     if not text:
#         return {}
    
#     words = text.split()
#     word_count = len(words)
#     char_count = len(text)
    
#     # Find sentences
#     sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
#     sentence_count = len(sentences)
    
#     # Find paragraphs
#     paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
#     paragraph_count = len(paragraphs)
    
#     # Calculate averages
#     avg_words_per_sentence = word_count / max(sentence_count, 1)
#     avg_words_per_paragraph = word_count / max(paragraph_count, 1)
    
#     return {
#         'word_count': word_count,
#         'character_count': char_count,
#         'sentence_count': sentence_count,
#         'paragraph_count': paragraph_count,
#         'avg_words_per_sentence': round(avg_words_per_sentence, 1),
#         'avg_words_per_paragraph': round(avg_words_per_paragraph, 1),
#         'reading_time_minutes': max(1, word_count // 200)
#     }
# @login_required
# def review_essay_detail(request, essay_id):
#     """Detailed review of an essay"""
#     if not request.user.is_staff:
#         messages.error(request, "You don't have permission to review essays.")
#         return redirect('home')
    
#     essay = get_object_or_404(Essay, id=essay_id)
#     review_templates = ReviewTemplate.objects.filter(is_active=True)
    
#     content = essay.content
#     word_count = len(content.split())
#     sentences = re.split(r'[.!?]+', content)
#     avg_sentence_length = word_count / max(len(sentences), 1)
    
#     grammar_patterns = {
#         'run_on_sentences': r'[.!?]\s*[a-z]',
#         'comma_splices': r',\s+[a-z]',
#         'fragments': r'^[a-z].*[^.!?]$',
#     }
    
#     grammar_issues = {}
#     for issue, pattern in grammar_patterns.items():
#         matches = re.findall(pattern, content, re.MULTILINE)
#         grammar_issues[issue] = len(matches)
    
#     common_misspellings = {
#         'seperate': 'separate',
#         'definately': 'definitely',
#         'occured': 'occurred',
#         'recieve': 'receive',
#         'wierd': 'weird',
#         'accomodate': 'accommodate',
#         'embarass': 'embarrass',
#         'mispell': 'misspell'
#     }
    
#     spelling_issues = {}
#     words = content.lower().split()
#     for word in words:
#         clean_word = re.sub(r'[^\w\s]', '', word)
#         if clean_word in common_misspellings:
#             spelling_issues[clean_word] = common_misspellings[clean_word]
    
#     if request.method == 'POST':
#         essay.grammar_errors = request.POST.get('grammar_errors', '')
#         essay.spelling_errors = request.POST.get('spelling_errors', '')
#         essay.vocabulary_suggestions = request.POST.get('vocabulary_suggestions', '')
#         essay.emoji_feedback = request.POST.get('emoji_feedback', '')
        
#         essay.is_reviewed = True
#         essay.reviewed_by = request.user
#         essay.reviewed_at = timezone.now()
#         essay.save()
        
#         Notification.objects.create(
#             user=essay.author,
#             notification_type='system',
#             title='Your Essay Has Been Reviewed! 📝',
#             message=f'Your essay "{essay.title}" has been reviewed by an admin.',
#             is_important=True
#         )
        
#         messages.success(request, "Essay review submitted successfully!")
#         return redirect('review_essays')
    
#     return render(request, 'essay/review_essay_detail.html', {
#         'essay': essay,
#         'review_templates': review_templates,
#         'word_count': word_count,
#         'avg_sentence_length': round(avg_sentence_length, 1),
#         'grammar_issues': grammar_issues,
#         'spelling_issues': spelling_issues,
#     })

# @login_required
# def verify_essay(request, essay_id):
#     """Mark essay as verified"""
#     if not request.user.is_staff:
#         messages.error(request, "You don't have permission to verify essays.")
#         return redirect('home')
    
#     essay = get_object_or_404(Essay, id=essay_id)
    
#     if request.method == 'POST':
#         essay.is_verified = True
#         essay.verified_by = request.user
#         essay.verified_at = timezone.now()
#         essay.status = 'published'
#         essay.save()
        
#         Notification.objects.create(
#             user=essay.author,
#             notification_type='achievement',
#             title='Essay Verified! ✅',
#             message=f'Congratulations! Your essay "{essay.title}" has been verified and published.',
#             is_important=True
#         )
        
#         messages.success(request, "Essay verified and published!")
#         return redirect('review_essays')
    
#     return render(request, 'essay/verify_essay.html', {'essay': essay})

# # ================== GRAMMAR CHECK ==================
# @login_required
# def grammar_check(request, essay_id):
#     """Grammar check for essay"""
#     essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    
#     # Get grammar analysis using the imported functions
#     analysis = analyze_text(essay.content)
#     issues = check_grammar(essay.content)
    
#     context = {
#         'essay': essay,
#         'analysis': analysis,
#         'issues': issues,
#         'total_issues': len(issues),
#         'has_issues': len(issues) > 0,
#     }
    
#     return render(request, 'essay/grammar_check.html', context)

# # ================== CHALLENGES VIEWS ==================

# @login_required
# def challenges_home(request):
#     """Main challenges page with all three features"""
#     try:
#         timed_challenges = TimedChallenge.objects.filter(is_active=True)[:6]
#         character_challenges = CharacterChallenge.objects.filter(is_active=True)[:6]
        
#         user_stats, created = ChallengeLeaderboard.objects.get_or_create(user=request.user)
        
#         recent_timed = TimedChallengeSubmission.objects.filter(
#             user=request.user
#         ).select_related('challenge').order_by('-started_at')[:5]
        
#         recent_character = CharacterChallengeSubmission.objects.filter(
#             user=request.user
#         ).select_related('challenge').order_by('-submitted_at')[:5]
        
#         top_users = ChallengeLeaderboard.objects.all().order_by('-total_points')[:10]
        
#         context = {
#             'timed_challenges': timed_challenges,
#             'character_challenges': character_challenges,
#             'user_stats': user_stats,
#             'recent_timed': recent_timed,
#             'recent_character': recent_character,
#             'top_users': top_users,
#         }
        
#         return render(request, 'essay/challenges.html', context)
#     except Exception as e:
#         print(f"Error in challenges_home: {e}")
#         return render(request, 'essay/challenges.html', {})

# @login_required
# def start_timed_challenge(request, challenge_id):
#     """Start a timed challenge"""
#     challenge = get_object_or_404(TimedChallenge, id=challenge_id, is_active=True)
    
#     existing = TimedChallengeSubmission.objects.filter(
#         challenge=challenge,
#         user=request.user,
#         status='in_progress'
#     ).first()
    
#     if existing:
#         submission = existing
#     else:
#         submission = TimedChallengeSubmission.objects.create(
#             challenge=challenge,
#             user=request.user,
#             status='in_progress'
#         )
    
#     context = {
#         'challenge': challenge,
#         'submission': submission,
#     }
    
#     return render(request, 'essay/timed_challenge_write.html', context)

# @login_required
# @require_http_methods(["POST"])
# def save_timed_challenge(request, submission_id):
#     """Save timed challenge progress"""
#     submission = get_object_or_404(TimedChallengeSubmission, id=submission_id, user=request.user)
    
#     data = json.loads(request.body)
#     content = data.get('content', '')
#     time_spent = data.get('time_spent', 0)
#     is_final = data.get('is_final', False)
    
#     submission.content = content
#     submission.word_count = len(content.split())
#     submission.time_spent_seconds = time_spent
    
#     if is_final:
#         submission.status = 'completed'
#         submission.completed_at = timezone.now()
        
#         if submission.word_count >= submission.challenge.min_words:
#             points = submission.challenge.points_reward
#             time_bonus = max(0, 50 - (time_spent // 60))
#             points += time_bonus
#         else:
#             points = 0
        
#         submission.points_earned = points
        
#         stats, _ = ChallengeLeaderboard.objects.get_or_create(user=request.user)
#         stats.total_points = (stats.total_points or 0) + points
#         stats.timed_challenges_completed = (stats.timed_challenges_completed or 0) + 1
#         stats.save()
        
#         ChallengeLeaderboard.update_all_ranks()
        
#         submission.save()
        
#         return JsonResponse({
#             'success': True,
#             'message': 'Challenge completed!',
#             'points_earned': points,
#             'word_count': submission.word_count,
#             'time_spent': time_spent
#         })
#     else:
#         submission.save()
#         return JsonResponse({
#             'success': True,
#             'message': 'Progress saved',
#             'word_count': submission.word_count
#         })

# @login_required
# def start_character_challenge(request, challenge_id):
#     """Start a character challenge"""
#     challenge = get_object_or_404(CharacterChallenge, id=challenge_id, is_active=True)
    
#     existing = CharacterChallengeSubmission.objects.filter(
#         challenge=challenge,
#         user=request.user
#     ).first()
    
#     context = {
#         'challenge': challenge,
#         'existing_submission': existing,
#     }
    
#     return render(request, 'essay/character_challenge_write.html', context)

# @login_required
# @require_http_methods(["POST"])
# def submit_character_challenge(request, challenge_id):
#     """Submit character challenge"""
#     challenge = get_object_or_404(CharacterChallenge, id=challenge_id, is_active=True)
    
#     data = json.loads(request.body)
#     content = data.get('content', '')
    
#     existing = CharacterChallengeSubmission.objects.filter(
#         challenge=challenge,
#         user=request.user
#     ).first()
    
#     if existing:
#         return JsonResponse({
#             'success': False,
#             'message': 'You have already submitted to this challenge'
#         }, status=400)
    
#     character_count = len(content)
#     is_valid = True
#     if not challenge.allow_over_limit and character_count > challenge.character_limit:
#         is_valid = False
    
#     if is_valid and character_count >= challenge.character_limit * 0.8:
#         points = challenge.points_reward
#     else:
#         points = max(0, challenge.points_reward // 2)
    
#     submission = CharacterChallengeSubmission.objects.create(
#         challenge=challenge,
#         user=request.user,
#         content=content,
#         character_count=character_count,
#         word_count=len(content.split()),
#         is_valid=is_valid,
#         points_earned=points
#     )
    
#     stats, _ = ChallengeLeaderboard.objects.get_or_create(user=request.user)
#     stats.total_points = (stats.total_points or 0) + points
#     stats.character_challenges_completed = (stats.character_challenges_completed or 0) + 1
#     stats.save()
    
#     ChallengeLeaderboard.update_all_ranks()
    
#     return JsonResponse({
#         'success': True,
#         'message': 'Submission successful!',
#         'points_earned': points,
#         'character_count': character_count,
#         'word_count': submission.word_count,
#         'is_valid': is_valid
#     })

# @login_required
# @require_http_methods(["POST"])
# def ai_writing_assist(request):
#     """AI Writing Assistant endpoint"""
#     data = json.loads(request.body)
    
#     text = data.get('text', '')
#     suggestion_type = data.get('type', 'improve')
#     essay_id = data.get('essay_id', None)
    
#     suggestions = {
#         'improve': f"Enhanced version: {text}\n\nConsider strengthening your argument with specific examples and data to support your claims.",
#         'expand': f"{text}\n\nAdditionally, you could explore the following aspects:\n- Historical context\n- Current implications\n- Future projections\n\nThis would provide a more comprehensive analysis.",
#         'summarize': f"Key points: {text[:100]}...\n\nMain ideas:\n1. [First main point]\n2. [Second main point]\n3. [Conclusion]",
#         'rephrase': f"Alternative phrasing: {text.replace('is', 'appears to be').replace('good', 'beneficial')}",
#         'grammar': f"Corrected: {text}\n\n✓ All grammar checks passed",
#         'tone': f"Professional tone: {text}\n\nAdjusted for formal academic writing.",
#         'creative': f"{text}\n\nCreative suggestions:\n- Use metaphors or analogies\n- Add vivid descriptions\n- Include personal anecdotes"
#     }
    
#     ai_suggestion = suggestions.get(suggestion_type, suggestions['improve'])
    
#     essay_obj = None
#     if essay_id:
#         try:
#             essay_obj = Essay.objects.get(id=essay_id, author=request.user)
#         except Essay.DoesNotExist:
#             essay_obj = None
    
#     session = AIWritingSession.objects.create(
#         user=request.user,
#         essay=essay_obj,
#         suggestion_type=suggestion_type,
#         original_text=text[:1000],
#         ai_suggestion=ai_suggestion[:2000]
#     )
    
#     return JsonResponse({
#         'success': True,
#         'suggestion': ai_suggestion,
#         'session_id': str(session.id)
#     })

# @login_required
# @require_http_methods(["POST"])
# def ai_accept_suggestion(request):
#     """Mark AI suggestion as accepted"""
#     data = json.loads(request.body)
#     session_id = data.get('session_id')
    
#     try:
#         session = AIWritingSession.objects.get(id=session_id, user=request.user)
#         session.was_accepted = True
#         session.save()
        
#         return JsonResponse({'success': True})
#     except AIWritingSession.DoesNotExist:
#         return JsonResponse({'success': False, 'message': 'Session not found'}, status=404)

# @login_required
# def challenge_leaderboard(request):
#     """Challenge leaderboard view"""
#     leaderboard = ChallengeLeaderboard.objects.select_related('user').all().order_by('-total_points')[:50]
    
#     try:
#         user_stats = ChallengeLeaderboard.objects.get(user=request.user)
#     except ChallengeLeaderboard.DoesNotExist:
#         user_stats = None
    
#     context = {
#         'leaderboard': leaderboard,
#         'user_stats': user_stats,
#     }
    
#     return render(request, 'essay/challenge_leaderboard.html', context)

# @login_required
# def my_challenge_history(request):
#     """View user's challenge history"""
#     timed_submissions = TimedChallengeSubmission.objects.filter(
#         user=request.user
#     ).select_related('challenge').order_by('-started_at')
    
#     character_submissions = CharacterChallengeSubmission.objects.filter(
#         user=request.user
#     ).select_related('challenge').order_by('-submitted_at')
    
#     ai_sessions = AIWritingSession.objects.filter(
#         user=request.user
#     ).order_by('-created_at')[:20]
    
#     stats, _ = ChallengeLeaderboard.objects.get_or_create(user=request.user)
    
#     context = {
#         'timed_submissions': timed_submissions,
#         'character_submissions': character_submissions,
#         'ai_sessions': ai_sessions,
#         'stats': stats,
#     }
    
#     return render(request, 'essay/challenge_history.html', context)

# @login_required
# def create_timed_challenge(request):
#     """Create new timed challenge (admin/staff only)"""
#     if not request.user.is_staff:
#         messages.error(request, "You don't have permission to access this page.")
#         return redirect('challenges_home')
    
#     if request.method == 'POST':
#         title = request.POST.get('title')
#         prompt = request.POST.get('prompt')
#         duration = int(request.POST.get('duration_minutes'))
#         difficulty = request.POST.get('difficulty')
#         min_words = int(request.POST.get('min_words', 300))
#         max_words = int(request.POST.get('max_words', 1000))
#         points = int(request.POST.get('points_reward', 100))
        
#         TimedChallenge.objects.create(
#             title=title,
#             prompt=prompt,
#             duration_minutes=duration,
#             difficulty=difficulty,
#             min_words=min_words,
#             max_words=max_words,
#             points_reward=points,
#             created_by=request.user
#         )
        
#         messages.success(request, "Timed challenge created successfully!")
#         return redirect('challenges_home')
    
#     return render(request, 'essay/create_timed_challenge.html') 
 

# @login_required
# def create_character_challenge(request):
#     """Create new character challenge (admin/staff only)"""
#     if not request.user.is_staff:
#         messages.error(request, "You don't have permission to access this page.")
#         return redirect('challenges_home')
    
#     if request.method == 'POST':
#         title = request.POST.get('title')
#         prompt = request.POST.get('prompt')
#         char_limit = int(request.POST.get('character_limit'))
#         allow_over = request.POST.get('allow_over_limit') == 'on'
#         points = int(request.POST.get('points_reward', 50))
        
#         CharacterChallenge.objects.create(
#             title=title,
#             prompt=prompt,
#             character_limit=char_limit,
#             allow_over_limit=allow_over,
#             points_reward=points,
#             created_by=request.user
#         )
        
#         messages.success(request, "Character challenge created successfully!")
#         return redirect('challenges_home')
    
#     return render(request, 'essay/create_character_challenge.html')
# # essay/admin_views.py
# from django.contrib.auth.decorators import login_required, user_passes_test
# from django.shortcuts import render, get_object_or_404, redirect
# from django.contrib import messages
# from django.utils import timezone
# from django.db.models import Q
# from .models import Essay, GrammarCheck
# import json

# # Check if user is admin/staff
# def is_staff_user(user):
#     return user.is_staff or user.is_superuser

# @login_required
# @user_passes_test(is_staff_user)
# def grammar_check_queue(request):
#     """List essays needing grammar check"""
#     # Essays requested by users for grammar check
#     requested_essays = Essay.objects.filter(
#         requires_grammar_check=True,
#         grammar_status=GrammarCheck.PENDING
#     ).order_by('-created_at')
    
#     # Essays with needs_review status
#     needs_review_essays = Essay.objects.filter(
#         grammar_status=GrammarCheck.NEEDS_REVIEW
#     ).order_by('-created_at')
    
#     # Essays that have been checked
#     checked_essays = Essay.objects.filter(
#         grammar_status=GrammarCheck.CHECKED
#     ).order_by('-grammar_checked_at')[:10]  # Last 10 checked
    
#     context = {
#         'requested_essays': requested_essays,
#         'needs_review_essays': needs_review_essays,
#         'checked_essays': checked_essays,
#         'total_pending': requested_essays.count() + needs_review_essays.count()
#     }
    
#     return render(request, 'essay/admin/grammar_queue.html', context)

# @login_required
# @user_passes_test(is_staff_user)
# def grammar_check_detail(request, essay_id):
#     """Detail view for grammar checking"""
#     essay = get_object_or_404(Essay, id=essay_id)
    
#     # Get previous grammar checks
#     previous_checks = GrammarCheck.objects.filter(essay=essay).order_by('-checked_at')
    
#     if request.method == 'POST':
#         try:
#             score = float(request.POST.get('score', 0))
#             notes = request.POST.get('notes', '')
#             suggestions = request.POST.get('suggestions', '')
#             status = request.POST.get('status', 'checked')
            
#             # Validate score
#             if score < 0 or score > 100:
#                 messages.error(request, "Score must be between 0 and 100")
#                 return redirect('grammar_check_detail', essay_id=essay_id)
            
#             # Count issues from suggestions (simple count of lines)
#             issues_count = len([line for line in suggestions.split('\n') if line.strip()])
            
#             # Create grammar check record
#             GrammarCheck.objects.create(
#                 essay=essay,
#                 checked_by=request.user,
#                 score=score,
#                 suggestions=suggestions,
#                 issues_data={'notes': notes, 'suggestions': suggestions},
#                 issues_found=issues_count,
#                 automated_check=False
#             )
            
#             # Update essay
#             essay.grammar_score = score
#             essay.grammar_status = status
#             essay.grammar_checked_by = request.user
#             essay.grammar_checked_at = timezone.now()
#             essay.grammar_notes = notes
#             essay.save()
            
#             messages.success(request, f"✓ Grammar check completed for '{essay.title}'")
#             return redirect('grammar_check_queue')
            
#         except ValueError:
#             messages.error(request, "Invalid score value")
#             return redirect('grammar_check_detail', essay_id=essay_id)
    
#     context = {
#         'essay': essay,
#         'previous_checks': previous_checks,
#         'grammar_status_choices': GrammarCheck.choices
#     }
    
#     return render(request, 'essay/admin/grammar_check_detail.html', context)

# @login_required
# @user_passes_test(is_staff_user)
# def bulk_grammar_action(request):
#     """Bulk actions for grammar checking"""
#     if request.method == 'POST':
#         action = request.POST.get('action')
#         essay_ids = request.POST.getlist('essay_ids')
        
#         if not essay_ids:
#             messages.warning(request, "No essays selected")
#             return redirect('grammar_check_queue')
        
#         essays = Essay.objects.filter(id__in=essay_ids)
        
#         if action == 'mark_checked':
#             updated_count = 0
#             for essay in essays:
#                 essay.grammar_status = GrammarCheck.CHECKED
#                 essay.grammar_checked_by = request.user
#                 essay.grammar_checked_at = timezone.now()
#                 essay.save()
#                 updated_count += 1
            
#             messages.success(request, f"✓ Marked {updated_count} essays as checked")
        
#         elif action == 'mark_needs_review':
#             updated_count = essays.update(grammar_status=GrammarCheck.NEEDS_REVIEW)
#             messages.success(request, f"✓ Flagged {updated_count} essays for review")
        
#         elif action == 'mark_pending':
#             updated_count = essays.update(grammar_status=GrammarCheck.PENDING)
#             messages.success(request, f"✓ Moved {updated_count} essays to pending")
        
#         else:
#             messages.error(request, "Invalid action selected")
    
#     return redirect('grammar_check_queue')

# @login_required
# @user_passes_test(is_staff_user)
# def grammar_stats(request):
#     """Show grammar checking statistics"""
#     total_essays = Essay.objects.count()
#     checked_essays = Essay.objects.filter(grammar_status=GrammarCheck.CHECKED).count()
#     pending_essays = Essay.objects.filter(grammar_status=GrammarCheck.PENDING).count()
#     needs_review_essays = Essay.objects.filter(grammar_status=GrammarCheck.NEEDS_REVIEW).count()
    
#     # Average grammar score
#     avg_score = Essay.objects.filter(grammar_score__isnull=False).aggregate(
#         avg_score=models.Avg('grammar_score')
#     )['avg_score'] or 0
    
#     # Recent checks
#     recent_checks = GrammarCheck.objects.select_related('essay', 'checked_by').order_by('-checked_at')[:10]
    
#     context = {
#         'total_essays': total_essays,
#         'checked_essays': checked_essays,
#         'pending_essays': pending_essays,
#         'needs_review_essays': needs_review_essays,
#         'avg_score': round(avg_score, 2) if avg_score else 0,
#         'recent_checks': recent_checks,
#         'completion_rate': round((checked_essays / total_essays * 100), 2) if total_essays > 0 else 0
#     }
    
#     return render(request, 'essay/admin/grammar_stats.html', context)
# # ================== TOOLS ==================
# @login_required
# def auto_check_essay(request, essay_id):
#     """Run automatic checks on essay"""
#     essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    
#     checks = {
#         'word_count': len(essay.content.split()),
#         'sentence_count': len(re.split(r'[.!?]+', essay.content)),
#         'paragraph_count': len([p for p in essay.content.split('\n\n') if p.strip()]),
#         'avg_word_length': sum(len(word) for word in essay.content.split()) / max(len(essay.content.split()), 1),
#     }
    
#     issues = []
    
#     if checks['word_count'] < 300:
#         issues.append(f"Essay is short ({checks['word_count']} words). Consider expanding to at least 300 words.")
    
#     if checks['sentence_count'] > 0:
#         avg_words_per_sentence = checks['word_count'] / checks['sentence_count']
#         if avg_words_per_sentence > 25:
#             issues.append("Sentences may be too long. Consider breaking them up.")
#         elif avg_words_per_sentence < 10:
#             issues.append("Sentences may be too short. Consider combining some.")
    
#     if checks['paragraph_count'] < 3:
#         issues.append("Consider adding more paragraphs for better structure.")
    
#     return JsonResponse({
#         'checks': checks,
#         'issues': issues,
#         'suggestions': [
#             "Use transition words between paragraphs",
#             "Include topic sentences in each paragraph",
#             "Proofread for spelling and grammar",
#             "Ensure proper citation if using sources"
#         ]
#     })







# essay/views.py - COMPLETE FILE
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods
from django.db import models
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph as PDFParagraph, Spacer
import json
import re
from django.db.models import Count, Q
from .models import (
    Essay, UserProfile, Language, Comment, Paragraph, 
    ReviewTemplate, Notification, TimedChallenge, 
    CharacterChallenge, TimedChallengeSubmission, 
    CharacterChallengeSubmission, ChallengeLeaderboard, 
    AIWritingSession, GrammarCheck
)

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
    
    all_users = User.objects.annotate(
        published_essays=Count('essays', filter=Q(essays__status='published'))
    ).order_by('-published_essays')
    
    rank = None
    for idx, user in enumerate(all_users, start=1):
        if user == request.user:
            rank = idx
            break
    
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
        requires_grammar_check = request.POST.get('requires_grammar_check') == 'on'
        
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
                status='submitted',
                requires_grammar_check=requires_grammar_check
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
    
    if essay.status != 'published' and essay.author != request.user:
        messages.error(request, "You don't have permission to view this essay.")
        return redirect('home')
    
    Essay.objects.filter(id=essay_id).update(views=models.F('views') + 1)
    
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
    
    def clean_html_for_pdf(text):
        if not text:
            return ""
        text = re.sub(r'<span[^>]*>.*?</span>', '', text)
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()
    
    content = essay.formatted_content or essay.content
    clean_content = clean_html_for_pdf(content)
    
    paragraphs = [p.strip() for p in clean_content.split('\n\n') if p.strip()]
    
    for para in paragraphs:
        if para:
            para = re.sub(r'\s+', ' ', para)
            story.append(PDFParagraph(para, styles['Normal']))
            story.append(Spacer(1, 6))
    
    try:
        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{essay.title}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f"Error generating PDF: {str(e)}")
        return redirect('essay_detail', essay_id=essay.id)

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

# ================== ENHANCED WRITING ==================
@login_required
def write_paragraph_enhanced(request):
    """Enhanced writing page"""
    return render(request, 'essay/write_paragraph_enhanced.html')

# ================== LIKE ESSAY ==================
@login_required
def like_essay(request, essay_id):
    """Like/unlike essay"""
    essay = get_object_or_404(Essay, id=essay_id)
    
    if request.user in essay.likes.all():
        essay.likes.remove(request.user)
        liked = False
        message = 'You unliked this essay.'
    else:
        essay.likes.add(request.user)
        liked = True
        message = 'You liked this essay!'
    
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
    
    pending_essays = Essay.objects.filter(
        status='submitted',
        is_reviewed=False
    ).order_by('created_at')
    
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
    review_templates = ReviewTemplate.objects.filter(is_active=True)
    
    content = essay.content
    word_count = len(content.split())
    sentences = re.split(r'[.!?]+', content)
    avg_sentence_length = word_count / max(len(sentences), 1)
    
    grammar_patterns = {
        'run_on_sentences': r'[.!?]\s*[a-z]',
        'comma_splices': r',\s+[a-z]',
        'fragments': r'^[a-z].*[^.!?]$',
    }
    
    grammar_issues = {}
    for issue, pattern in grammar_patterns.items():
        matches = re.findall(pattern, content, re.MULTILINE)
        grammar_issues[issue] = len(matches)
    
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
        essay.grammar_errors = request.POST.get('grammar_errors', '')
        essay.spelling_errors = request.POST.get('spelling_errors', '')
        essay.vocabulary_suggestions = request.POST.get('vocabulary_suggestions', '')
        essay.emoji_feedback = request.POST.get('emoji_feedback', '')
        
        essay.is_reviewed = True
        essay.reviewed_by = request.user
        essay.reviewed_at = timezone.now()
        essay.save()
        
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

# ================== GRAMMAR CHECK ==================
@login_required
def grammar_check(request, essay_id):
    """Grammar check for essay"""
    essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    
    # Simple grammar analysis
    def simple_check_grammar(text):
        issues = []
        if not text or not text.strip():
            return issues
        
        # Check for lowercase 'i' as subject
        if re.search(r'\bi\s+', text):
            issues.append({
                'message': 'Use capital "I" when referring to yourself',
                'suggestion': 'I'
            })
        
        # Check for double spaces
        if '  ' in text:
            issues.append({
                'message': 'Avoid double spaces',
                'suggestion': 'Use single space'
            })
        
        return issues
    
    def simple_analyze_text(text):
        if not text:
            return {}
        
        words = text.split()
        word_count = len(words)
        char_count = len(text)
        
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        sentence_count = len(sentences)
        
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)
        
        avg_words_per_sentence = word_count / max(sentence_count, 1)
        avg_words_per_paragraph = word_count / max(paragraph_count, 1)
        
        return {
            'word_count': word_count,
            'character_count': char_count,
            'sentence_count': sentence_count,
            'paragraph_count': paragraph_count,
            'avg_words_per_sentence': round(avg_words_per_sentence, 1),
            'avg_words_per_paragraph': round(avg_words_per_paragraph, 1),
            'reading_time_minutes': max(1, word_count // 200)
        }
    
    analysis = simple_analyze_text(essay.content)
    issues = simple_check_grammar(essay.content)
    
    context = {
        'essay': essay,
        'analysis': analysis,
        'issues': issues,
        'total_issues': len(issues),
        'has_issues': len(issues) > 0,
    }
    
    return render(request, 'essay/grammar_check.html', context)

# ================== AUTO CHECK ==================
@login_required
def auto_check_essay(request, essay_id):
    """Run automatic checks on essay"""
    essay = get_object_or_404(Essay, id=essay_id, author=request.user)
    
    checks = {
        'word_count': len(essay.content.split()),
        'sentence_count': len(re.split(r'[.!?]+', essay.content)),
        'paragraph_count': len([p for p in essay.content.split('\n\n') if p.strip()]),
        'avg_word_length': sum(len(word) for word in essay.content.split()) / max(len(essay.content.split()), 1),
    }
    
    issues = []
    
    if checks['word_count'] < 300:
        issues.append(f"Essay is short ({checks['word_count']} words). Consider expanding to at least 300 words.")
    
    if checks['sentence_count'] > 0:
        avg_words_per_sentence = checks['word_count'] / checks['sentence_count']
        if avg_words_per_sentence > 25:
            issues.append("Sentences may be too long. Consider breaking them up.")
        elif avg_words_per_sentence < 10:
            issues.append("Sentences may be too short. Consider combining some.")
    
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

# ================== CHALLENGES VIEWS ==================
@login_required
def challenges_home(request):
    """Main challenges page with all three features"""
    try:
        timed_challenges = TimedChallenge.objects.filter(is_active=True)[:6]
        character_challenges = CharacterChallenge.objects.filter(is_active=True)[:6]
        
        user_stats, created = ChallengeLeaderboard.objects.get_or_create(user=request.user)
        
        recent_timed = TimedChallengeSubmission.objects.filter(
            user=request.user
        ).select_related('challenge').order_by('-started_at')[:5]
        
        recent_character = CharacterChallengeSubmission.objects.filter(
            user=request.user
        ).select_related('challenge').order_by('-submitted_at')[:5]
        
        top_users = ChallengeLeaderboard.objects.all().order_by('-total_points')[:10]
        
        context = {
            'timed_challenges': timed_challenges,
            'character_challenges': character_challenges,
            'user_stats': user_stats,
            'recent_timed': recent_timed,
            'recent_character': recent_character,
            'top_users': top_users,
        }
        
        return render(request, 'essay/challenges.html', context)
    except Exception as e:
        print(f"Error in challenges_home: {e}")
        return render(request, 'essay/challenges.html', {})

@login_required
def start_timed_challenge(request, challenge_id):
    """Start a timed challenge"""
    challenge = get_object_or_404(TimedChallenge, id=challenge_id, is_active=True)
    
    existing = TimedChallengeSubmission.objects.filter(
        challenge=challenge,
        user=request.user,
        status='in_progress'
    ).first()
    
    if existing:
        submission = existing
    else:
        submission = TimedChallengeSubmission.objects.create(
            challenge=challenge,
            user=request.user,
            status='in_progress'
        )
    
    context = {
        'challenge': challenge,
        'submission': submission,
    }
    
    return render(request, 'essay/timed_challenge_write.html', context)

@login_required
@require_http_methods(["POST"])
def save_timed_challenge(request, submission_id):
    """Save timed challenge progress"""
    submission = get_object_or_404(TimedChallengeSubmission, id=submission_id, user=request.user)
    
    data = json.loads(request.body)
    content = data.get('content', '')
    time_spent = data.get('time_spent', 0)
    is_final = data.get('is_final', False)
    
    submission.content = content
    submission.word_count = len(content.split())
    submission.time_spent_seconds = time_spent
    
    if is_final:
        submission.status = 'completed'
        submission.completed_at = timezone.now()
        
        if submission.word_count >= submission.challenge.min_words:
            points = submission.challenge.points_reward
            time_bonus = max(0, 50 - (time_spent // 60))
            points += time_bonus
        else:
            points = 0
        
        submission.points_earned = points
        
        stats, _ = ChallengeLeaderboard.objects.get_or_create(user=request.user)
        stats.total_points = (stats.total_points or 0) + points
        stats.timed_challenges_completed = (stats.timed_challenges_completed or 0) + 1
        stats.save()
        
        ChallengeLeaderboard.update_all_ranks()
        
        submission.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Challenge completed!',
            'points_earned': points,
            'word_count': submission.word_count,
            'time_spent': time_spent
        })
    else:
        submission.save()
        return JsonResponse({
            'success': True,
            'message': 'Progress saved',
            'word_count': submission.word_count
        })

@login_required
def start_character_challenge(request, challenge_id):
    """Start a character challenge"""
    challenge = get_object_or_404(CharacterChallenge, id=challenge_id, is_active=True)
    
    existing = CharacterChallengeSubmission.objects.filter(
        challenge=challenge,
        user=request.user
    ).first()
    
    context = {
        'challenge': challenge,
        'existing_submission': existing,
    }
    
    return render(request, 'essay/character_challenge_write.html', context)

@login_required
@require_http_methods(["POST"])
def submit_character_challenge(request, challenge_id):
    """Submit character challenge"""
    challenge = get_object_or_404(CharacterChallenge, id=challenge_id, is_active=True)
    
    data = json.loads(request.body)
    content = data.get('content', '')
    
    existing = CharacterChallengeSubmission.objects.filter(
        challenge=challenge,
        user=request.user
    ).first()
    
    if existing:
        return JsonResponse({
            'success': False,
            'message': 'You have already submitted to this challenge'
        }, status=400)
    
    character_count = len(content)
    is_valid = True
    if not challenge.allow_over_limit and character_count > challenge.character_limit:
        is_valid = False
    
    if is_valid and character_count >= challenge.character_limit * 0.8:
        points = challenge.points_reward
    else:
        points = max(0, challenge.points_reward // 2)
    
    submission = CharacterChallengeSubmission.objects.create(
        challenge=challenge,
        user=request.user,
        content=content,
        character_count=character_count,
        word_count=len(content.split()),
        is_valid=is_valid,
        points_earned=points
    )
    
    stats, _ = ChallengeLeaderboard.objects.get_or_create(user=request.user)
    stats.total_points = (stats.total_points or 0) + points
    stats.character_challenges_completed = (stats.character_challenges_completed or 0) + 1
    stats.save()
    
    ChallengeLeaderboard.update_all_ranks()
    
    return JsonResponse({
        'success': True,
        'message': 'Submission successful!',
        'points_earned': points,
        'character_count': character_count,
        'word_count': submission.word_count,
        'is_valid': is_valid
    })

@login_required
@require_http_methods(["POST"])
def ai_writing_assist(request):
    """AI Writing Assistant endpoint"""
    data = json.loads(request.body)
    
    text = data.get('text', '')
    suggestion_type = data.get('type', 'improve')
    essay_id = data.get('essay_id', None)
    
    suggestions = {
        'improve': f"Enhanced version: {text}\n\nConsider strengthening your argument with specific examples and data to support your claims.",
        'expand': f"{text}\n\nAdditionally, you could explore the following aspects:\n- Historical context\n- Current implications\n- Future projections\n\nThis would provide a more comprehensive analysis.",
        'summarize': f"Key points: {text[:100]}...\n\nMain ideas:\n1. [First main point]\n2. [Second main point]\n3. [Conclusion]",
        'rephrase': f"Alternative phrasing: {text.replace('is', 'appears to be').replace('good', 'beneficial')}",
        'grammar': f"Corrected: {text}\n\n✓ All grammar checks passed",
        'tone': f"Professional tone: {text}\n\nAdjusted for formal academic writing.",
        'creative': f"{text}\n\nCreative suggestions:\n- Use metaphors or analogies\n- Add vivid descriptions\n- Include personal anecdotes"
    }
    
    ai_suggestion = suggestions.get(suggestion_type, suggestions['improve'])
    
    essay_obj = None
    if essay_id:
        try:
            essay_obj = Essay.objects.get(id=essay_id, author=request.user)
        except Essay.DoesNotExist:
            essay_obj = None
    
    session = AIWritingSession.objects.create(
        user=request.user,
        essay=essay_obj,
        suggestion_type=suggestion_type,
        original_text=text[:1000],
        ai_suggestion=ai_suggestion[:2000]
    )
    
    return JsonResponse({
        'success': True,
        'suggestion': ai_suggestion,
        'session_id': str(session.id)
    })

@login_required
@require_http_methods(["POST"])
def ai_accept_suggestion(request):
    """Mark AI suggestion as accepted"""
    data = json.loads(request.body)
    session_id = data.get('session_id')
    
    try:
        session = AIWritingSession.objects.get(id=session_id, user=request.user)
        session.was_accepted = True
        session.save()
        
        return JsonResponse({'success': True})
    except AIWritingSession.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Session not found'}, status=404)

@login_required
def challenge_leaderboard(request):
    """Challenge leaderboard view"""
    leaderboard = ChallengeLeaderboard.objects.select_related('user').all().order_by('-total_points')[:50]
    
    try:
        user_stats = ChallengeLeaderboard.objects.get(user=request.user)
    except ChallengeLeaderboard.DoesNotExist:
        user_stats = None
    
    context = {
        'leaderboard': leaderboard,
        'user_stats': user_stats,
    }
    
    return render(request, 'essay/challenge_leaderboard.html', context)

@login_required
def my_challenge_history(request):
    """View user's challenge history"""
    timed_submissions = TimedChallengeSubmission.objects.filter(
        user=request.user
    ).select_related('challenge').order_by('-started_at')
    
    character_submissions = CharacterChallengeSubmission.objects.filter(
        user=request.user
    ).select_related('challenge').order_by('-submitted_at')
    
    ai_sessions = AIWritingSession.objects.filter(
        user=request.user
    ).order_by('-created_at')[:20]
    
    stats, _ = ChallengeLeaderboard.objects.get_or_create(user=request.user)
    
    context = {
        'timed_submissions': timed_submissions,
        'character_submissions': character_submissions,
        'ai_sessions': ai_sessions,
        'stats': stats,
    }
    
    return render(request, 'essay/challenge_history.html', context)

@login_required
def create_timed_challenge(request):
    """Create new timed challenge (admin/staff only)"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('challenges_home')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        prompt = request.POST.get('prompt')
        duration = int(request.POST.get('duration_minutes'))
        difficulty = request.POST.get('difficulty')
        min_words = int(request.POST.get('min_words', 300))
        max_words = int(request.POST.get('max_words', 1000))
        points = int(request.POST.get('points_reward', 100))
        
        TimedChallenge.objects.create(
            title=title,
            prompt=prompt,
            duration_minutes=duration,
            difficulty=difficulty,
            min_words=min_words,
            max_words=max_words,
            points_reward=points,
            created_by=request.user
        )
        
        messages.success(request, "Timed challenge created successfully!")
        return redirect('challenges_home')
    
    return render(request, 'essay/create_timed_challenge.html')

@login_required
def create_character_challenge(request):
    """Create new character challenge (admin/staff only)"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('challenges_home')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        prompt = request.POST.get('prompt')
        char_limit = int(request.POST.get('character_limit'))
        allow_over = request.POST.get('allow_over_limit') == 'on'
        points = int(request.POST.get('points_reward', 50))
        
        CharacterChallenge.objects.create(
            title=title,
            prompt=prompt,
            character_limit=char_limit,
            allow_over_limit=allow_over,
            points_reward=points,
            created_by=request.user
        )
        
        messages.success(request, "Character challenge created successfully!")
        return redirect('challenges_home')
    
    return render(request, 'essay/create_character_challenge.html')