from django.urls import path
from . import views

urlpatterns = [
    # Basic Pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('community/', views.community, name='community'),
    path('resources/', views.resources, name='resources'),
    
    # Auth URLs - using names that match template
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
    
    # Essay CRUD Operations
    path('essays/<uuid:essay_id>/', views.essay_detail, name='essay_detail'),
    path('essays/<uuid:essay_id>/edit/', views.edit_essay, name='edit_essay'),
    path('essays/<uuid:essay_id>/delete/', views.delete_essay, name='delete_essay'),
    path('essays/<uuid:essay_id>/comment/', views.add_comment, name='add_comment'),
    path('essay/<uuid:pk>/like/', views.like_essay, name='like_essay'),
    
    # Essay Features
    path('essays/<uuid:essay_id>/grammar-check/', views.grammar_check, name='grammar_check'),
    path('essays/<uuid:essay_id>/download-pdf/', views.download_pdf, name='download_pdf'),
    
    # Paragraph Writing System
    path('essays/<uuid:essay_id>/write/', views.write_paragraph, name='write_paragraph'),
    path('essays/<uuid:essay_id>/save-paragraph/', views.save_paragraph, name='save_paragraph'),
    path('essays/<uuid:essay_id>/unlock/<int:paragraph_num>/', views.unlock_paragraph, name='unlock_paragraph'),
    
    # Enhanced Writing
    path('write-enhanced/', views.write_paragraph_enhanced, name='write_paragraph_enhanced'),
    path('save-secure-paragraph/', views.save_secure_paragraph, name='save_secure_paragraph'),
    
    # Admin
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    
    # Review URLs
    path('review-essays/', views.review_essays, name='review_essays'),
    path('review-essay/<uuid:essay_id>/', views.review_essay_detail, name='review_essay_detail'),
    path('verify-essay/<uuid:essay_id>/', views.verify_essay, name='verify_essay'),
    
    # Tools
    path('grammar-check/<uuid:essay_id>/', views.grammar_check_tool, name='grammar_check_tool'),
    path('spell-check/<uuid:essay_id>/', views.spell_check_tool, name='spell_check_tool'),
    path('auto-check/<uuid:essay_id>/', views.auto_check_essay, name='auto_check_essay'),
    
    
    
] 

