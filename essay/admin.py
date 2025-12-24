from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.http import HttpResponseRedirect, FileResponse
from django.shortcuts import get_object_or_404
import os
from .models import UserProfile, Language, Essay, Paragraph, Comment


# ========== LANGUAGE ADMIN ==========

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')


# ========== PARAGRAPH INLINE ==========

class ParagraphInline(admin.TabularInline):
    model = Paragraph
    extra = 0
    readonly_fields = ('paragraph_number', 'word_count', 'is_locked')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ========== ESSAY ADMIN ==========

@admin.register(Essay)
class EssayAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'author', 'language_display', 'word_count',
        'status', 'pdf_status', 'pdf_actions'
    )
    list_filter = (
        'status', 'category',
        'primary_language', 'created_at', 'pdf_generated_at'
    )
    search_fields = ('title', 'author__username', 'content')
    readonly_fields = (
        'id', 'created_at', 'updated_at', 'word_count', 'views',
        'pdf_generated_at', 'pdf_preview', 'pdf_details'
    )
    inlines = [ParagraphInline]
    actions = ['generate_pdfs_action', 'delete_pdfs_action', 'export_as_pdf_list']

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'author', 'primary_language', 'category', 'status')
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('Statistics', {
            'fields': (
                'word_count', 'views', 'grammar_score', 'spelling_score',
                'content_score', 'score', 'grade'
            )
        }),
        ('PDF Information', {
            'fields': ('pdf_file', 'pdf_generated_at', 'pdf_preview', 'pdf_details')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    # ----- Display helpers -----
    def language_display(self, obj):
        if obj.primary_language:
            return f"{obj.primary_language.name} ({obj.primary_language.code})"
        return "Not set"
    language_display.short_description = 'Language'

    def pdf_status(self, obj):
        if obj.pdf_file:
            try:
                size_kb = obj.pdf_file.size // 1024 if obj.pdf_file.size else 0
                return format_html(
                    '<span style="color: green; font-weight: bold;">✓ Generated</span><br>'
                    '<small>{} KB</small>',
                    size_kb,
                )
            except:
                return format_html('<span style="color: orange;">⚠️ File error</span>')
        return format_html('<span style="color: red;">✗ No PDF</span>')
    pdf_status.short_description = 'PDF Status'

    def pdf_actions(self, obj):
        if obj.pdf_file:
            return format_html(
                '<a href="{}" target="_blank" class="button">👁️ View</a>&nbsp;'
                '<a href="{}" class="button">📥 Download</a>',
                obj.pdf_file.url,
                reverse('admin:essay_essay_download_pdf', args=[obj.id]),
            )
        return format_html(
            '<a href="#" class="button">No PDF</a>'
        )
    pdf_actions.short_description = 'Actions'

    def pdf_preview(self, obj):
        if obj.pdf_file and hasattr(obj.pdf_file, 'url'):
            return format_html(
                '<div style="border: 1px solid #ddd; padding: 10px; margin: 10px 0;">'
                '<h4>PDF Preview</h4>'
                '<iframe src="{}" width="100%" height="600px" style="border: none;"></iframe>'
                '</div>',
                obj.pdf_file.url + "#toolbar=0&navpanes=0&scrollbar=0"
            )
        return "No PDF available for preview"
    pdf_preview.short_description = 'PDF Preview'

    def pdf_details(self, obj):
        if obj.pdf_file:
            try:
                file_size = obj.pdf_file.size if obj.pdf_file.size else 0
                return format_html(
                    '<div style="background: #f5f5f5; padding: 15px; border-radius: 5px;">'
                    '<h4>📊 PDF Details</h4>'
                    '<table style="width: 100%;">'
                    '<tr><td><strong>File Size:</strong></td><td>{:.2f} MB</td></tr>'
                    '<tr><td><strong>Generated At:</strong></td><td>{}</td></tr>'
                    '</table>'
                    '</div>',
                    file_size / (1024 * 1024),
                    obj.pdf_generated_at.strftime('%Y-%m-%d %H:%M:%S') if obj.pdf_generated_at else 'N/A',
                )
            except Exception as e:
                return f"Error loading PDF details: {e}"
        return "No PDF details available"
    pdf_details.short_description = 'PDF File Information'

    # ----- Admin actions -----
    def generate_pdfs_action(self, request, queryset):
        count = 0
        for essay in queryset:
            # Simple PDF generation placeholder
            try:
                essay.save()
                count += 1
            except:
                pass
        self.message_user(request, f"Processed {count} essays.")
    generate_pdfs_action.short_description = "Process selected essays"

    def delete_pdfs_action(self, request, queryset):
        count = 0
        for essay in queryset:
            if essay.pdf_file:
                essay.pdf_file.delete(save=False)
                essay.pdf_file = None
                essay.pdf_generated_at = None
                essay.save()
                count += 1
        self.message_user(request, f"Deleted PDFs for {count} essays.")
    delete_pdfs_action.short_description = "Delete PDFs from selected essays"

    def export_as_pdf_list(self, request, queryset):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="essays_list.csv"'
        writer = csv.writer(response)
        writer.writerow(['Title', 'Author', 'Language', 'Word Count', 'Status'])

        for essay in queryset:
            writer.writerow([
                essay.title,
                essay.author.username,
                essay.primary_language.name if essay.primary_language else '',
                essay.word_count,
                essay.status
            ])

        return response
    export_as_pdf_list.short_description = "Export essays as CSV"

    # ----- Custom admin routes -----
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<uuid:object_id>/download-pdf/', self.admin_site.admin_view(self.download_pdf_view),
                 name='essay_essay_download_pdf'),
        ]
        return custom_urls + urls

    def download_pdf_view(self, request, object_id):
        essay = get_object_or_404(Essay, id=object_id)
        if not essay.pdf_file:
            self.message_user(request, "No PDF available.", level='error')
            return HttpResponseRedirect(reverse('admin:essay_essay_change', args=[object_id]))

        response = FileResponse(essay.pdf_file.open(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{essay.title}.pdf"'
        return response


# ========== USER PROFILE ADMIN ==========

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'preferred_language', 'is_verified', 'points')
    list_filter = ('role', 'is_verified')
    search_fields = ('user__username', 'student_id')


# ========== COMMENT ADMIN ==========

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'essay', 'created_at')
    search_fields = ('content', 'author__username')