from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.http import HttpResponseRedirect, FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *

# ========== LANGUAGE ADMIN ==========
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')

# ========== PARAGRAPH INLINE ==========
class ParagraphInline(admin.TabularInline):
    model = Paragraph
    extra = 0
    readonly_fields = ('paragraph_number', 'content_preview', 'formatted_content_preview', 
                       'word_count', 'is_locked', 'created_at')
    fields = ('paragraph_number', 'content_preview', 'formatted_content_preview', 
              'word_count', 'is_locked', 'created_at')
    can_delete = False
    show_change_link = True
    
    def content_preview(self, obj):
        """Show plain content preview"""
        if obj.content:
            return format_html(
                '<div style="max-height: 80px; overflow-y: auto; background: #f8f9fa; padding: 8px; border-radius: 4px; margin: 5px 0;">'
                '<small style="color: #495057;">{}</small>'
                '</div>',
                obj.content[:150] + "..." if len(obj.content) > 150 else obj.content
            )
        return "-"
    content_preview.short_description = 'Plain Text'
    
    def formatted_content_preview(self, obj):
        """Show formatted content preview"""
        if obj.formatted_content:
            return format_html(
                '<div style="max-height: 80px; overflow-y: auto; background: #e8f4f8; padding: 8px; border-radius: 4px; margin: 5px 0;">'
                '<small>{}</small>'
                '</div>',
                obj.formatted_content[:200] + "..." if len(obj.formatted_content) > 200 else obj.formatted_content
            )
        return format_html('<span style="color: #999;">No formatted version</span>')
    formatted_content_preview.short_description = 'Formatted HTML'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

# ========== USER PROFILE INLINE FOR USER ADMIN ==========
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    extra = 0
    
    def get_readonly_fields(self, request, obj=None):
        return ['essays_count_display_admin']
    
    def essays_count_display_admin(self, obj):
        """Safely display essays count"""
        if obj and obj.user:
            count = Essay.objects.filter(author=obj.user).count()
            return format_html(
                '<div style="background: #007bff; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; margin: 5px 0; display: inline-block;">{} essays</div>',
                count
            )
        return format_html('<div style="color: #999;">No essays</div>')

# ========== CUSTOM USER ADMIN ==========
class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_essays_count')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    
    def get_essays_count(self, obj):
        """Get essays count for user"""
        count = Essay.objects.filter(author=obj).count()
        return format_html(
            '<span style="color: #007bff; font-weight: bold;">{}</span>',
            count
        )
    get_essays_count.short_description = 'Essays'
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

# ========== ESSAY ADMIN ==========
class EssayAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'author', 'language_display', 'word_count',
        'status', 'emoji_feedback', 'is_reviewed', 'is_verified', 'created_at'
    )
    list_filter = (
        'status', 'category', 'is_reviewed', 'is_verified', 'emoji_feedback', 'created_at'
    )
    search_fields = ('title', 'author__username', 'content')
    readonly_fields = (
        'created_at', 'updated_at', 'published_at', 'word_count', 
        'character_count', 'sentence_count', 'paragraph_count', 'views'
    )
    inlines = [ParagraphInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'content', 'formatted_content', 'abstract', 'author', 'primary_language')
        }),
        ('Metadata', {
            'fields': ('category', 'tags', 'status', 'writing_mode', 'difficulty_level', 'is_public')
        }),
        ('Statistics', {
            'fields': ('word_count', 'character_count', 'sentence_count', 'paragraph_count', 'views', 'likes')
        }),
        ('Feedback', {
            'fields': ('emoji_feedback', 'grammar_errors', 'spelling_errors', 'punctuation_errors',
                      'style_suggestions', 'vocabulary_suggestions',
                      'structure_comments', 'content_feedback')
        }),
        ('Review Status', {
            'fields': ('is_reviewed', 'reviewed_by', 'reviewed_at', 
                      'is_verified', 'verified_by', 'verified_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at')
        }),
    )

    def language_display(self, obj):
        if obj.primary_language:
            return format_html(
                '<span style="font-weight: bold;">{}</span><br><small>{}</small>',
                obj.primary_language.name,
                obj.primary_language.code
            )
        return format_html('<span style="color: #999;">Not set</span>')
    language_display.short_description = 'Language'

# ========== USER PROFILE ADMIN ==========
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_verified_writer', 'email_verified', 'created_at')
    list_filter = ('role', 'is_verified_writer', 'email_verified')

# ========== COMMENT ADMIN ==========
class CommentAdmin(admin.ModelAdmin):
    list_display = ('essay', 'author', 'created_at', 'is_approved')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('content', 'author__username', 'essay__title')

# ========== PARAGRAPH ADMIN ==========
class ParagraphAdmin(admin.ModelAdmin):
    list_display = ('essay', 'paragraph_number', 'word_count', 'is_completed')
    list_filter = ('is_completed', 'created_at')

# ========== REVIEW TEMPLATE ADMIN ==========
class ReviewTemplateAdmin(admin.ModelAdmin):
    list_display = ('category', 'title', 'severity', 'is_active')
    list_filter = ('category', 'severity', 'is_active')
    search_fields = ('title', 'description', 'example')

# ========== NOTIFICATION ADMIN ==========
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username')

# ========== COMPETITION ADMIN ==========
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'category', 'registration_start', 'registration_end')
    list_filter = ('status', 'category', 'is_featured')
    search_fields = ('title', 'description', 'theme')

# ========== COMPETITION SUBMISSION ADMIN ==========
class CompetitionSubmissionAdmin(admin.ModelAdmin):
    list_display = ('competition', 'participant', 'submitted_at', 'is_approved', 'score')
    list_filter = ('is_approved', 'competition')
    search_fields = ('competition__title', 'participant__username')

# ========== BADGE ADMIN ==========
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'badge_type', 'level', 'requirement_value')
    list_filter = ('badge_type', 'level')
    search_fields = ('name', 'description')

# ========== FOLLOW ADMIN ==========
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('follower__username', 'following__username')

# ========== BOOKMARK ADMIN ==========
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'essay', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'essay__title')

# ========== REGISTER MODELS (ONCE!) ==========

# Unregister default User admin if already registered
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

# Register all models ONCE

admin.site.register(Essay, EssayAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Language, LanguageAdmin)
