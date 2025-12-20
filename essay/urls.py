from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('profile/', views.profile, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('community/', views.community, name='community'),
    path('resources/', views.resources, name='resources'),
    path('winners/', views.winners, name='winners'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    
    path('login/', views.custom_login, name='custom_login'),
    path('logout/', views.custom_logout, name='custom_logout'),
    path('register/', views.register, name='register'),
    path('my-submissions/', views.my_submissions, name='my_submissions'),
    
    path('essays/', views.essay_list, name='essay_list'),
    path('essays/create/', views.create_essay, name='create_essay'),
    path('essays/my/', views.my_essays, name='my_essays'),
    path('essays/<uuid:essay_id>/', views.essay_detail, name='essay_detail'),
    path('essays/<uuid:essay_id>/edit/', views.edit_essay, name='edit_essay'),
    path('essays/<uuid:essay_id>/delete/', views.delete_essay, name='delete_essay'),
    path('essays/<uuid:essay_id>/results/', views.essay_results, name='essay_results'),
    path('essays/<uuid:essay_id>/like/', views.like_essay, name='like_essay'),
    path('essays/<uuid:essay_id>/grammar-check/', views.grammar_check, name='grammar_check'),
    path('essays/<uuid:essay_id>/download-pdf/', views.download_pdf, name='download_pdf'),
    
    path('essays/<uuid:essay_id>/write/', views.write_paragraph, name='write_paragraph'),
    path('essays/<uuid:essay_id>/save-paragraph/', views.save_paragraph, name='save_paragraph'),
    path('essays/<uuid:essay_id>/unlock/<int:paragraph_num>/', views.unlock_paragraph, name='unlock_paragraph'),
    
    path('essays/<uuid:essay_id>/comment/', views.add_comment, name='add_comment'),
    
    path('competitions/', views.competition_list, name='competition_list'),
    path('competitions/<uuid:competition_id>/', views.competition_detail, name='competition_detail'),
    path('competitions/<uuid:competition_id>/submit/', views.submit_essay, name='submit_essay'),
    
    path('api/languages/', views.get_languages, name='get_languages'),
    path('api/check-auth/', views.check_auth, name='check_auth'),
    path('api/essays/<uuid:essay_id>/paragraphs/', views.get_paragraphs, name='get_paragraphs'),
    path('api/check-grammar/', views.check_grammar_api, name='check_grammar_api'),
    
    path('admin/essays/', views.admin_essay_list, name='admin_essay_list'),
    path('update-scores/', views.update_all_scores, name='update_all_scores'),
]