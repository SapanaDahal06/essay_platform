# essay/admin.py - CORRECTED VERSION
from django.contrib import admin
from django.contrib.auth.models import User, Group
from .models import (
    Essay, Paragraph, Comment, UserProfile, Language,
    ReviewTemplate, Notification, Competition, CompetitionSubmission,
    Follow, Bookmark, TimedChallenge, TimedChallengeSubmission,
    CharacterChallenge, CharacterChallengeSubmission,
    AIWritingSession, ChallengeLeaderboard, Badge,
    GrammarCheck
)

# Customize Essay admin
class EssayAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'status', 'grammar_status', 'grammar_score', 'created_at']
    list_filter = ['status', 'category', 'grammar_status', 'created_at']
    search_fields = ['title', 'content', 'author__username']
    readonly_fields = ['created_at', 'updated_at', 'published_at', 'word_count', 'character_count', 'sentence_count', 'paragraph_count', 'views']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'author', 'content', 'formatted_content', 'category', 'primary_language')
        }),
        ('Status', {
            'fields': ('status', 'published_at')
        }),
        ('Grammar Check', {
            'fields': ('requires_grammar_check', 'grammar_status', 'grammar_score', 
                      'grammar_checked_by', 'grammar_checked_at', 'grammar_notes')
        }),
        ('Feedback', {
            'fields': ('emoji_feedback', 'grammar_errors', 'spelling_errors', 'vocabulary_suggestions')
        }),
        ('Review Status', {
            'fields': ('is_reviewed', 'reviewed_by', 'reviewed_at', 'is_verified', 'verified_by', 'verified_at')
        }),
        ('Statistics', {
            'fields': ('views', 'word_count', 'character_count', 'sentence_count', 'paragraph_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    # Add calculated fields to list display
    def get_likes_count(self, obj):
        return obj.likes.count()
    get_likes_count.short_description = 'Likes'
    
    def get_bookmarks_count(self, obj):
        return obj.bookmarks.count()
    get_bookmarks_count.short_description = 'Bookmarks'
    
    # Add these to list_display if you want to see them
    # list_display = ['title', 'author', 'category', 'status', 'grammar_status', 'get_likes_count', 'get_bookmarks_count', 'created_at']

# Customize GrammarCheck admin
class GrammarCheckAdmin(admin.ModelAdmin):
    list_display = ['essay', 'checked_by', 'score', 'issues_found', 'checked_at']
    list_filter = ['checked_by', 'checked_at', 'automated_check']
    search_fields = ['essay__title', 'suggestions', 'checked_by__username']
    readonly_fields = ['checked_at']
    ordering = ['-checked_at']

# Customize UserProfile admin
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'level', 'experience_points', 'streak_days']
    list_filter = ['role', 'level']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']

# Register all models
admin.site.register(Essay, EssayAdmin)
admin.site.register(Paragraph)
admin.site.register(Comment)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Language)
admin.site.register(ReviewTemplate)
admin.site.register(Notification)
admin.site.register(Competition)
admin.site.register(CompetitionSubmission)
admin.site.register(Follow)
admin.site.register(Bookmark)
admin.site.register(TimedChallenge)
admin.site.register(TimedChallengeSubmission)
admin.site.register(CharacterChallenge)
admin.site.register(CharacterChallengeSubmission)
admin.site.register(AIWritingSession)
admin.site.register(ChallengeLeaderboard)
admin.site.register(Badge)
admin.site.register(GrammarCheck, GrammarCheckAdmin)

# Optionally customize Django's built-in User admin
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']

# Unregister default User admin and register custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Customize Group admin if needed
class CustomGroupAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)

# Optional: Custom admin site header
admin.site.site_header = "Essay Platform Administration"
admin.site.site_title = "Essay Platform Admin"
admin.site.index_title = "Welcome to Essay Platform Admin"
/* essay/static/css/admin_custom.css */
.button {
    display: inline-block;
    padding: 10px 15px;
    background: #417690;
    color: white;
    text-decoration: none;
    border-radius: 4px;
    margin: 5px 0;
}

.button:hover {
    background: #205067;
}

.grammar-report {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    padding: 15px;
    border-radius: 4px;
    white-space: pre-wrap;
    font-family: monospace;
    max-height: 300px;
    overflow-y: auto;
}