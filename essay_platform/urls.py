# # # essay_platform/urls.py (Main Project URLs)
# # """
# # URL configuration for essay_platform project.

# # The `urlpatterns` list routes URLs to views. For more information please see:
# #     https://docs.djangoproject.com/en/5.2/topics/http/urls/
# # """
# # from django.contrib import admin
# # from django.urls import path, include
# # from django.conf import settings
# # from django.conf.urls.static import static

# # urlpatterns = [
# #     # Django Admin
# #     path('admin/', admin.site.urls),
# #     path('', include('essay.urls')),
# #     # Include Essay App URLs
# #     path('', include('essay.urls')),
# # ]

# # # ============================================
# # # SERVE MEDIA & STATIC FILES IN DEVELOPMENT
# # # ============================================
# # # This is ONLY for development. In production, use Nginx/Apache to serve files
# # if settings.DEBUG:
# #     # Serve media files (PDFs, user uploads)
# #     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
# #     # Serve static files (CSS, JS, Images)
# #     urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# #     if settings.DEBUG:
# #        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# from django.contrib import admin
# from django.urls import path, include
# from django.conf import settings
# from django.conf.urls.static import static
# from essay import views as essay_views
# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('', include('essay.urls')),  # or your app name
    
#     # Your custom admin dashboard URLs
#     path('admin-dashboard/', essay_views.admin_dashboard, name='admin_dashboard'),
#     path('admin-dashboard/essays/', essay_views.admin_essay_management, name='admin_essay_management'),
#     path('admin-dashboard/users/', essay_views.admin_user_management, name='admin_user_management'),
#     path('admin-dashboard/competitions/', essay_views.admin_competition_management, name='admin_competition_management'),
#     path('admin-dashboard/analytics/', essay_views.admin_analytics, name='admin_analytics'),
#     path('admin-dashboard/settings/', essay_views.admin_system_settings, name='admin_system_settings'),
    
#     path('', include('essay.urls')),  # Your regular app URLs
# ]


# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
#     urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('essay.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)