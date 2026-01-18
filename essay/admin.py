# essay/admin.py - CLEAN VERSION (Updated imports)
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import (
    Essay, Paragraph, Comment, UserProfile, Language,
    ReviewTemplate, Notification, Competition, CompetitionSubmission,
    Follow, Bookmark, TimedChallenge, TimedChallengeSubmission,
    CharacterChallenge, CharacterChallengeSubmission,
    AIWritingSession, ChallengeLeaderboard, Badge,
    GrammarCheck
)

# ================== ESSAY ADMIN ==================
class EssayAdmin(admin.ModelAdmin):
    class Media:
        css = {
            'all': ('css/admin_custom.css', 'css/grammar_highlights.css')
        }
    
    list_display = ['title', 'author', 'category', 'status', 'grammar_status', 
                   'grammar_score', 'ranking_position_display', 'overall_quality_score', 
                   'created_at', 'grammar_check_actions']
    
    list_filter = ['status', 'category', 'grammar_status', 'created_at']
    search_fields = ['title', 'content', 'author__username']
    readonly_fields = ['created_at', 'updated_at', 'published_at', 'word_count', 
                      'character_count', 'sentence_count', 'paragraph_count', 
                      'views', 'highlighted_content_display', 'readability_score',
                      'overall_quality_score', 'ranking_score', 'ranking_position',
                      'error_statistics', 'get_likes_count', 'get_bookmarks_count']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'author', 'content', 'category', 'primary_language')
        }),
        ('Grammar Check Results', {
            'fields': ('highlighted_content_display', 'error_statistics', 
                      'readability_score', 'overall_quality_score')
        }),
        ('Grammar Status', {
            'fields': ('requires_grammar_check', 'grammar_status', 'grammar_score',
                      'grammar_errors_json', 'spelling_errors_json', 
                      'style_suggestions_json', 'grammar_notes')
        }),
        ('Ranking', {
            'fields': ('ranking_score', 'ranking_position')
        }),
        ('Status & Review', {
            'fields': ('status', 'published_at', 'is_reviewed', 'reviewed_by', 
                      'reviewed_at', 'is_verified', 'verified_by', 'verified_at')
        }),
        ('Statistics', {
            'fields': ('views', 'word_count', 'character_count', 'sentence_count', 
                      'paragraph_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['run_grammar_check', 'update_rankings', 
              'export_grammar_reports', 'mark_as_reviewed']
    
    ordering = ['-ranking_score', '-created_at']
    
    # Custom display methods
    def ranking_position_display(self, obj):
        if obj.ranking_position == 1:
            return format_html('<span class="ranking-badge ranking-1">🥇 {}</span>', obj.ranking_position)
        elif obj.ranking_position == 2:
            return format_html('<span class="ranking-badge ranking-2">🥈 {}</span>', obj.ranking_position)
        elif obj.ranking_position == 3:
            return format_html('<span class="ranking-badge ranking-3">🥉 {}</span>', obj.ranking_position)
        elif obj.ranking_position <= 10:
            return format_html('<span class="ranking-badge ranking-top10">#{}</span>', obj.ranking_position)
        else:
            return format_html('<span class="ranking-badge ranking-other">#{}</span>', obj.ranking_position)
    ranking_position_display.short_description = 'Rank'
    
    def highlighted_content_display(self, obj):
        """Display content with highlighted errors"""
        if not obj.content:
            return "No content"
        
        # Generate highlighted content if not exists
        if not obj.highlighted_content:
            obj.highlighted_content = self.generate_highlighted_content(obj)
            obj.save()
        
        # Display with proper HTML
        return format_html(
            '<div class="essay-content" style="border: 1px solid #ddd; padding: 15px; '
            'border-radius: 5px; background: #f9f9f9; max-height: 400px; overflow-y: auto;">'
            '{}'
            '<div class="legend" style="margin-top: 20px; padding: 10px; background: #fff; border-radius: 3px;">'
            '<strong>Legend:</strong> '
            '<span class="grammar-legend" style="color: #e74c3c; text-decoration: underline wavy #e74c3c; margin-right: 15px;">Grammar Errors</span>'
            '<span class="spelling-legend" style="color: #3498db; text-decoration: underline wavy #3498db;">Spelling Errors</span>'
            '</div>'
            '</div>',
            format_html(obj.highlighted_content or obj.content)
        )
    highlighted_content_display.short_description = 'Content with Error Highlights'
    
    def generate_highlighted_content(self, obj):
        """Generate HTML with error highlights"""
        if not obj.content:
            return ""
        
        content = obj.content
        
        # Grammar errors from JSON
        if obj.grammar_errors_json and 'errors' in obj.grammar_errors_json:
            for error in obj.grammar_errors_json['errors']:
                word = error.get('word', '')
                suggestion = error.get('suggestion', '')
                if word and suggestion:
                    highlighted = f'<span class="grammar-error highlight-grammar" title="Grammar: {suggestion}">{word}</span>'
                    content = content.replace(word, highlighted, 1)
        
        # Spelling errors from JSON
        if obj.spelling_errors_json and 'errors' in obj.spelling_errors_json:
            for error in obj.spelling_errors_json['errors']:
                word = error.get('word', '')
                suggestions = error.get('suggestions', [])
                if word and suggestions:
                    suggestion_text = "Suggestions: " + ", ".join(suggestions[:3])
                    highlighted = f'<span class="spelling-error highlight-spelling" title="{suggestion_text}">{word}</span>'
                    content = content.replace(word, highlighted, 1)
        
        return content
    
    def error_statistics(self, obj):
        """Display error statistics"""
        grammar_count = len(obj.grammar_errors_json.get('errors', [])) if obj.grammar_errors_json else 0
        spelling_count = len(obj.spelling_errors_json.get('errors', [])) if obj.spelling_errors_json else 0
        total_errors = grammar_count + spelling_count
        
        return format_html(
            '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
            '<strong>Error Statistics:</strong><br>'
            f'Grammar Errors: <span style="color: {"#e74c3c" if grammar_count > 5 else "#f39c12" if grammar_count > 0 else "#2ecc71"}">{grammar_count}</span><br>'
            f'Spelling Errors: <span style="color: {"#e74c3c" if spelling_count > 5 else "#f39c12" if spelling_count > 0 else "#2ecc71"}">{spelling_count}</span><br>'
            f'Total Errors: <strong>{total_errors}</strong><br>'
            f'Error Density: {total_errors / (obj.word_count or 1):.2%}<br>'
            f'Grammar Score: <strong>{obj.grammar_score or "N/A"}/100</strong>'
            '</div>'
        )
    error_statistics.short_description = 'Error Analysis'
    
    def grammar_check_actions(self, obj):
        """Display action buttons for grammar checking"""
        return format_html(
            '<div style="display: flex; gap: 5px;">'
            '<a class="button" href="/admin/essay/essay/{}/run-grammar-check/" '
            'style="background: #3498db; color: white; padding: 3px 8px; border-radius: 3px; '
            'text-decoration: none; font-size: 12px;">🔍 Check</a>'
            '<a class="button" href="/admin/essay/essay/{}/view-highlights/" '
            'style="background: #9b59b6; color: white; padding: 3px 8px; border-radius: 3px; '
            'text-decoration: none; font-size: 12px;">👁 View</a>'
            '</div>',
            obj.id, obj.id
        )
    grammar_check_actions.short_description = 'Actions'
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    get_likes_count.short_description = 'Likes'
    
    def get_bookmarks_count(self, obj):
        return obj.bookmarks.count()
    get_bookmarks_count.short_description = 'Bookmarks'
    
    # Admin actions
    def run_grammar_check(self, request, queryset):
        """Run grammar check on selected essays"""
        for essay in queryset:
            # Simple grammar check implementation
            result = self._simple_grammar_check(essay)
            
            if result:
                essay.grammar_errors_json = {'errors': result.get('grammar_errors', [])}
                essay.spelling_errors_json = {'errors': result.get('spelling_errors', [])}
                essay.grammar_score = result.get('overall_score', 0)
                essay.readability_score = result.get('readability_score', 0)
                essay.overall_quality_score = result.get('overall_score', 0)
                essay.highlighted_content = self.generate_highlighted_content(essay)
                essay.grammar_status = 'checked'
                essay.grammar_notes = f"Manual check by {request.user.username}"
                essay.grammar_checked_by = request.user
                essay.grammar_checked_at = timezone.now()
                essay.save()
                
        self.message_user(request, f"Grammar check completed for {queryset.count()} essays.")
    run_grammar_check.short_description = "🔍 Run grammar check"
    
    def _simple_grammar_check(self, essay):
        """Simple inline grammar check"""
        content = essay.content
        if not content:
            return None
        
        # Common checks
        grammar_errors = []
        spelling_errors = []
        
        # Check for common mistakes
        common_errors = {
            'their': ["they're", "there"],
            'your': ["you're"],
            'its': ["it's"],
            'then': ["than"],
        }
        
        common_misspellings = {
            'recieve': ['receive'],
            'seperate': ['separate'],
            'definately': ['definitely'],
            'wierd': ['weird'],
        }
        
        words = content.split()
        for i, word in enumerate(words):
            cleaned_word = ''.join(c for c in word if c.isalpha()).lower()
            
            if cleaned_word in common_errors:
                grammar_errors.append({
                    'word': word,
                    'suggestions': common_errors[cleaned_word],
                    'suggestion': f"Consider: {common_errors[cleaned_word][0]}"
                })
            
            if cleaned_word in common_misspellings:
                spelling_errors.append({
                    'word': word,
                    'suggestions': common_misspellings[cleaned_word]
                })
        
        # Simple scoring
        total_errors = len(grammar_errors) + len(spelling_errors)
        word_count = len(words)
        
        if word_count > 0:
            error_density = total_errors / word_count * 100
            base_score = max(0, 100 - (error_density * 10))
        else:
            base_score = 0
        
        # Simple readability (just word/sentence ratio)
        sentences = len([s for s in content.split('.') if s.strip()])
        readability = 70  # Default
        
        if sentences > 0 and word_count > 0:
            words_per_sentence = word_count / sentences
            if 15 <= words_per_sentence <= 25:
                readability = 85
            elif words_per_sentence < 10:
                readability = 60
            elif words_per_sentence > 30:
                readability = 55
        
        overall_score = (base_score * 0.7) + (readability * 0.3)
        
        return {
            'grammar_errors': grammar_errors,
            'spelling_errors': spelling_errors,
            'readability_score': readability,
            'overall_score': min(100, overall_score)
        }
    
    def update_rankings(self, request, queryset):
        """Update rankings for selected essays"""
        # Calculate rankings based on overall quality score
        essays = list(queryset.order_by('-overall_quality_score', '-created_at'))
        
        for i, essay in enumerate(essays, 1):
            essay.ranking_position = i
            essay.ranking_score = essay.overall_quality_score or 0
            essay.save()
        
        self.message_user(request, f"Rankings updated for {len(essays)} essays.")
    update_rankings.short_description = "📊 Update rankings"
    
    def export_grammar_reports(self, request, queryset):
        """Export grammar reports for selected essays"""
        self.message_user(request, f"Export feature coming soon for {queryset.count()} essays.")
    export_grammar_reports.short_description = "📤 Export grammar reports"
    
    def mark_as_reviewed(self, request, queryset):
        """Mark selected essays as reviewed"""
        queryset.update(
            is_reviewed=True,
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"Marked {queryset.count()} essays as reviewed.")
    mark_as_reviewed.short_description = "✅ Mark as reviewed"
    
    # Custom URLs
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/run-grammar-check/', self.run_grammar_check_view, name='essay_grammar_check'),
            path('<path:object_id>/view-highlights/', self.view_highlights_view, name='essay_view_highlights'),
        ]
        return custom_urls + urls
    
    def run_grammar_check_view(self, request, object_id):
        """View for running grammar check on single essay"""
        essay = get_object_or_404(Essay, id=object_id)
        result = self._simple_grammar_check(essay)
        
        if result:
            essay.grammar_errors_json = {'errors': result.get('grammar_errors', [])}
            essay.spelling_errors_json = {'errors': result.get('spelling_errors', [])}
            essay.grammar_score = result.get('overall_score', 0)
            essay.readability_score = result.get('readability_score', 0)
            essay.overall_quality_score = result.get('overall_score', 0)
            essay.highlighted_content = self.generate_highlighted_content(essay)
            essay.grammar_status = 'checked'
            essay.grammar_notes = f"Manual check by {request.user.username}"
            essay.grammar_checked_by = request.user
            essay.grammar_checked_at = timezone.now()
            essay.save()
            
            messages.success(request, 
                f"Grammar check completed! Score: {result.get('overall_score', 0):.1f}/100")
        else:
            messages.error(request, "Could not perform grammar check.")
        
        return redirect('admin:essay_essay_change', object_id=object_id)
    
    def view_highlights_view(self, request, object_id):
        """View for displaying highlighted errors"""
        essay = get_object_or_404(Essay, id=object_id)
        
        context = {
            'essay': essay,
            'title': f'Grammar Highlights - {essay.title}',
        }
        
        return render(request, 'admin/essay/grammar_highlights.html', context)

# ================== GRAMMAR CHECK ADMIN ==================
class GrammarCheckAdmin(admin.ModelAdmin):
    list_display = ['essay', 'checked_by', 'score', 'issues_found', 'checked_at']
    list_filter = ['checked_by', 'checked_at', 'automated_check']
    search_fields = ['essay__title', 'suggestions', 'checked_by__username']
    readonly_fields = ['checked_at']
    ordering = ['-checked_at']

# ================== USER PROFILE ADMIN ==================
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'level', 'experience_points', 'streak_days']
    list_filter = ['role', 'level']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']

# ================== CHALLENGE LEADERBOARD ADMIN ==================
class ChallengeLeaderboardAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_points', 'total_challenges_completed', 'rank', 'current_streak']
    list_filter = ['rank']
    search_fields = ['user__username']
    ordering = ['rank']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')

# ================== REGISTER MODELS ==================
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
admin.site.register(ChallengeLeaderboard, ChallengeLeaderboardAdmin)
admin.site.register(Badge)
admin.site.register(GrammarCheck, GrammarCheckAdmin)

# ================== CUSTOM USER ADMIN ==================
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

class CustomGroupAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)

# ================== CUSTOM ADMIN SITE ==================
admin.site.site_header = "Essay Platform Administration"
admin.site.site_title = "Essay Platform Admin"
admin.site.index_title = "Welcome to Essay Platform Admin"