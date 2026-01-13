# essay/urls.py
from django.urls import path
from . import views
from . import admin_views

urlpatterns = [
    # Basic Pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('community/', views.community, name='community'),
    path('resources/', views.resources, name='resources'),
    
    # Auth URLs
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    
    # User Profile Pages
    path('profile/', views.profile, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    
    # Essay Pages
    path('essays/', views.essay_list, name='essay_list'),
    path('essays/my/', views.my_essays, name='my_essays'),
    path('essays/create/', views.create_essay, name='create_essay'),
    
    
    # Admin grammar checking URLs
    path('admin/grammar-queue/', admin_views.grammar_check_queue, name='grammar_check_queue'),
    path('admin/grammar-check/<uuid:essay_id>/', admin_views.grammar_check_detail, name='grammar_check_detail'),
    path('admin/bulk-grammar-action/', admin_views.bulk_grammar_action, name='bulk_grammar_action'),
    path('admin/grammar-stats/', admin_views.grammar_stats, name='grammar_stats'),  # NOTE: Comma at end!
    
    # Essay CRUD Operations
    path('essays/<uuid:essay_id>/', views.essay_detail, name='essay_detail'),
    path('essays/<uuid:essay_id>/edit/', views.edit_essay, name='edit_essay'),
    path('essays/<uuid:essay_id>/delete/', views.delete_essay, name='delete_essay'),
    path('essays/<uuid:essay_id>/comment/', views.add_comment, name='add_comment'),
    path('essays/<uuid:essay_id>/like/', views.like_essay, name='like_essay'),
    
    # Essay Features
    path('essays/<uuid:essay_id>/grammar-check/', views.grammar_check, name='grammar_check'),
    path('essays/<uuid:essay_id>/download-pdf/', views.download_pdf, name='download_pdf'),
    
    # Paragraph Writing System
    path('essays/<uuid:essay_id>/write/', views.write_paragraph, name='write_paragraph'),
    path('essays/<uuid:essay_id>/save-paragraph/', views.save_paragraph, name='save_paragraph'),
    
    # Enhanced Writing
    path('write-enhanced/', views.write_paragraph_enhanced, name='write_paragraph_enhanced'),
    
    # Admin
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Review URLs
    path('review-essays/', views.review_essays, name='review_essays'),
    path('review-essay/<uuid:essay_id>/', views.review_essay_detail, name='review_essay_detail'),
    path('verify-essay/<uuid:essay_id>/', views.verify_essay, name='verify_essay'),
    
    # Tools
    path('auto-check/<uuid:essay_id>/', views.auto_check_essay, name='auto_check_essay'),
    
    # Challenge URLs
    path('challenges/', views.challenges_home, name='challenges_home'),
    path('challenges/leaderboard/', views.challenge_leaderboard, name='challenge_leaderboard'),
    path('challenges/history/', views.my_challenge_history, name='challenge_history'),
    
    # Timed Challenges
    path('challenges/timed/<uuid:challenge_id>/start/', views.start_timed_challenge, name='start_timed_challenge'),
    path('challenges/timed/<uuid:submission_id>/save/', views.save_timed_challenge, name='save_timed_challenge'),
    path('challenges/timed/create/', views.create_timed_challenge, name='create_timed_challenge'),
    
    # Character Challenges
    path('challenges/character/<uuid:challenge_id>/start/', views.start_character_challenge, name='start_character_challenge'),
    path('challenges/character/<uuid:challenge_id>/submit/', views.submit_character_challenge, name='submit_character_challenge'),
    path('challenges/character/create/', views.create_character_challenge, name='create_character_challenge'),
    
    # AI Writing Assistant
    path('ai/assist/', views.ai_writing_assist, name='ai_writing_assist'),
    path('ai/accept/', views.ai_accept_suggestion, name='ai_accept_suggestion'),
     ]
