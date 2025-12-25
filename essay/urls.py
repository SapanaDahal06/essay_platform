from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('profile/', views.profile, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('community/', views.community, name='community'),
    path('essays/', views.essay_list, name='essay_list'),
    
    path('login/', views.custom_login, name='custom_login'),
    path('logout/', views.custom_logout, name='custom_logout'),
    path('register/', views.register, name='register'),
    
    path('essays/create/', views.create_essay, name='create_essay'),
    path('essay/<uuid:pk>/like/', views.like_essay, name='like_essay'),
    path('essays/my/', views.my_essays, name='my_essays'),
    path('essays/<uuid:essay_id>/', views.essay_detail, name='essay_detail'),
    path('essays/<uuid:essay_id>/edit/', views.edit_essay, name='edit_essay'),
    path('essays/<uuid:essay_id>/delete/', views.delete_essay, name='delete_essay'),
    path('essays/<uuid:essay_id>/grammar-check/', views.grammar_check, name='grammar_check'),
    path('essays/<uuid:essay_id>/download-pdf/', views.download_pdf, name='download_pdf'),
    path('essays/<uuid:essay_id>/comment/', views.add_comment, name='add_comment'),
    
    path('essays/<uuid:essay_id>/write/', views.write_paragraph, name='write_paragraph'),
    path('essays/<uuid:essay_id>/save-paragraph/', views.save_paragraph, name='save_paragraph'),
    path('essays/<uuid:essay_id>/unlock/<int:paragraph_num>/', views.unlock_paragraph, name='unlock_paragraph'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
     path('write-enhanced/', views.write_paragraph_enhanced, name='write_paragraph_enhanced'),
    path('save-secure-paragraph/', views.save_secure_paragraph, name='save_secure_paragraph'),
]
