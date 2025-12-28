# from django.contrib import admin
# from django.utils.html import format_html
# from django.urls import reverse, path
# from django.http import HttpResponseRedirect, FileResponse
# from django.shortcuts import get_object_or_404
# from .models import UserProfile, Language, Essay, Paragraph, Comment
# from django.utils import timezone


# # ========== LANGUAGE ADMIN ==========
# @admin.register(Language)
# class LanguageAdmin(admin.ModelAdmin):
#     list_display = ('name', 'code', 'is_active')
#     list_filter = ('is_active',)
#     search_fields = ('name', 'code')


# # ========== PARAGRAPH INLINE ==========
# class ParagraphInline(admin.TabularInline):
#     model = Paragraph
#     extra = 0
#     readonly_fields = ('paragraph_number', 'word_count', 'is_locked', 'created_at')
#     can_delete = False
#     show_change_link = True

#     def has_add_permission(self, request, obj=None):
#         return False

#     def has_change_permission(self, request, obj=None):
#         return False


# # ========== ESSAY ADMIN ==========
# @admin.register(Essay)
# class EssayAdmin(admin.ModelAdmin):
#     list_display = (
#         'title', 'author', 'language_display', 'word_count',
#         'status', 'writing_mode', 'pdf_status', 'pdf_actions'
#     )
#     list_filter = (
#         'status', 'category', 'writing_mode',
#         'primary_language', 'created_at'
#     )
#     search_fields = ('title', 'author__username', 'content')
#     readonly_fields = (
#         'id', 'created_at', 'updated_at', 'word_count', 'views',
#         'pdf_generated_at', 'pdf_preview', 'pdf_details', 'grade'
#     )
#     inlines = [ParagraphInline]
#     actions = ['generate_pdfs_action', 'delete_pdfs_action', 'export_as_csv']

#     fieldsets = (
#         ('Basic Information', {
#             'fields': ('title', 'author', 'primary_language', 'category', 'status', 'writing_mode')
#         }),
#         ('Content', {
#             'fields': ('content',)
#         }),
#         ('Statistics', {
#             'fields': (
#                 'word_count', 'views', 'grammar_score', 'spelling_score',
#                 'content_score', 'score', 'grade'
#             )
#         }),
#         ('PDF Information', {
#             'fields': ('pdf_file', 'pdf_generated_at', 'pdf_preview', 'pdf_details')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at')
#         }),
#     )

#     # ----- Display helpers -----
#     def language_display(self, obj):
#         if obj.primary_language:
#             return f"{obj.primary_language.name} ({obj.primary_language.code})"
#         return "Not set"
#     language_display.short_description = 'Language'

#     def pdf_status(self, obj):
#         if obj.pdf_file:
#             try:
#                 size_kb = obj.pdf_file.size // 1024 if obj.pdf_file.size else 0
#                 return format_html(
#                     '<span style="color: green; font-weight: bold;">✓ Generated</span><br>'
#                     '<small>{} KB</small>',
#                     size_kb,
#                 )
#             except:
#                 return format_html('<span style="color: orange;">⚠️ File error</span>')
#         return format_html('<span style="color: red;">✗ No PDF</span>')
#     pdf_status.short_description = 'PDF Status'

#     def pdf_actions(self, obj):
#         if obj.pdf_file and hasattr(obj.pdf_file, 'url'):
#             return format_html(
#                 '<a href="{}" target="_blank" class="button">👁️ View</a>&nbsp;'
#                 '<a href="{}" class="button">📥 Download</a>',
#                 obj.pdf_file.url,
#                 reverse('admin:essay_essay_download_pdf', args=[obj.id]),
#             )
#         return format_html(
#             '<span style="color: #999;">No PDF</span>'
#         )
#     pdf_actions.short_description = 'Actions'

#     def pdf_preview(self, obj):
#         if obj.pdf_file and hasattr(obj.pdf_file, 'url'):
#             return format_html(
#                 '<div style="border: 1px solid #ddd; padding: 10px; margin: 10px 0;">'
#                 '<h4>PDF Preview</h4>'
#                 '<iframe src="{}" width="100%" height="600px" style="border: none;"></iframe>'
#                 '</div>',
#                 obj.pdf_file.url + "#toolbar=0&navpanes=0&scrollbar=0"
#             )
#         return "No PDF available for preview"
#     pdf_preview.short_description = 'PDF Preview'

#     def pdf_details(self, obj):
#         if obj.pdf_file:
#             try:
#                 file_size = obj.pdf_file.size if obj.pdf_file.size else 0
#                 return format_html(
#                     '<div style="background: #f5f5f5; padding: 15px; border-radius: 5px;">'
#                     '<h4>📊 PDF Details</h4>'
#                     '<table style="width: 100%;">'
#                     '<tr><td><strong>File Size:</strong></td><td>{:.2f} MB</td></tr>'
#                     '<tr><td><strong>Generated At:</strong></td><td>{}</td></tr>'
#                     '</table>'
#                     '</div>',
#                     file_size / (1024 * 1024),
#                     obj.pdf_generated_at.strftime('%Y-%m-%d %H:%M:%S') if obj.pdf_generated_at else 'N/A',
#                 )
#             except Exception as e:
#                 return f"Error loading PDF details: {e}"
#         return "No PDF details available"
#     pdf_details.short_description = 'PDF File Information'

#     # ----- Admin actions -----
#     def generate_pdfs_action(self, request, queryset):
#         count = 0
#         for essay in queryset:
#             try:
#                 # Trigger PDF generation (you can implement this)
#                 # For now, just mark as processed
#                 essay.pdf_generated_at = timezone.now()
#                 essay.save()
#                 count += 1
#             except:
#                 pass
#         self.message_user(request, f"Processed {count} essays.")
#     generate_pdfs_action.short_description = "Generate PDFs for selected essays"

#     def delete_pdfs_action(self, request, queryset):
#         count = 0
#         for essay in queryset:
#             if essay.pdf_file:
#                 essay.pdf_file.delete(save=False)
#                 essay.pdf_file = None
#                 essay.pdf_generated_at = None
#                 essay.save()
#                 count += 1
#         self.message_user(request, f"Deleted PDFs for {count} essays.")
#     delete_pdfs_action.short_description = "Delete PDFs from selected essays"

#     def export_as_csv(self, request, queryset):
#         import csv
#         from django.http import HttpResponse
#         from django.utils import timezone

#         response = HttpResponse(content_type='text/csv')
#         response['Content-Disposition'] = f'attachment; filename="essays_export_{timezone.now().strftime("%Y%m%d")}.csv"'
        
#         writer = csv.writer(response)
#         writer.writerow(['Title', 'Author', 'Language', 'Word Count', 'Status', 'Writing Mode'])
        
#         for essay in queryset:
#             writer.writerow([
#                 essay.title,
#                 essay.author.username,
#                 essay.primary_language.name if essay.primary_language else '',
#                 essay.word_count,
#                 essay.get_status_display(),
#                 essay.get_writing_mode_display()
#             ])
        
#         return response
#     export_as_csv.short_description = "Export selected essays as CSV"

#     # ----- Custom admin routes -----
#     def get_urls(self):
#         urls = super().get_urls()
#         custom_urls = [
#             path('<uuid:object_id>/download-pdf/', self.admin_site.admin_view(self.download_pdf_view),
#                  name='essay_essay_download_pdf'),
#         ]
#         return custom_urls + urls

#     def download_pdf_view(self, request, object_id):
#         essay = get_object_or_404(Essay, id=object_id)
#         if not essay.pdf_file:
#             self.message_user(request, "No PDF available.", level='error')
#             return HttpResponseRedirect(reverse('admin:essay_essay_change', args=[object_id]))

#         response = FileResponse(essay.pdf_file.open(), content_type='application/pdf')
#         response['Content-Disposition'] = f'attachment; filename="{essay.title}.pdf"'
#         return response


# # ========== USER PROFILE ADMIN ==========
# @admin.register(UserProfile)
# class UserProfileAdmin(admin.ModelAdmin):
#     list_display = ('user', 'role', 'preferred_language', 'is_verified', 'points', 'essays_written')
#     list_filter = ('role', 'is_verified')
#     search_fields = ('user__username', 'student_id')
#     readonly_fields = ('id', 'created_at', 'updated_at')
    
#     fieldsets = (
#         ('User Information', {
#             'fields': ('user', 'role', 'student_id', 'bio')
#         }),
#         ('Preferences', {
#             'fields': ('preferred_language',)
#         }),
#         ('Verification', {
#             'fields': ('is_verified',)
#         }),
#         ('Statistics', {
#             'fields': ('points', 'leaderboard_score', 'essays_written')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at')
#         }),
#     )


# # ========== COMMENT ADMIN ==========
# @admin.register(Comment)
# class CommentAdmin(admin.ModelAdmin):
#     list_display = ('author', 'essay_preview', 'created_at', 'content_preview')
#     list_filter = ('created_at',)
#     search_fields = ('content', 'author__username', 'essay__title')
#     readonly_fields = ('id', 'created_at', 'updated_at')
    
#     def essay_preview(self, obj):
#         return format_html(
#             '<a href="{}">{}</a>',
#             reverse('admin:essay_essay_change', args=[obj.essay.id]),
#             obj.essay.title[:50] + '...' if len(obj.essay.title) > 50 else obj.essay.title
#         )
#     essay_preview.short_description = 'Essay'
    
#     def content_preview(self, obj):
#         return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
#     content_preview.short_description = 'Comment Preview'




from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.http import HttpResponseRedirect, FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
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


# ========== ESSAY ADMIN ==========
@admin.register(Essay)
class EssayAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'author', 'language_display', 'word_count',
        'status', 'writing_mode_display', 'pdf_status', 'pdf_actions'
    )
    list_filter = (
        'status', 'category', 'writing_mode',
        'primary_language', 'created_at'
    )
    search_fields = ('title', 'author__username', 'content', 'formatted_content')
    readonly_fields = (
        'id', 'created_at', 'updated_at', 'word_count', 'views',
        'pdf_generated_at', 'pdf_preview', 'pdf_details', 'grade',
        'content_preview', 'formatted_content_display'
    )
    inlines = [ParagraphInline]
    actions = ['generate_pdfs_action', 'delete_pdfs_action', 'export_as_csv']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'author', 'primary_language', 'category', 'status', 'writing_mode')
        }),
        ('Content', {
            'fields': ('content_preview', 'formatted_content_display', 'content', 'formatted_content')
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
            return format_html(
                '<span style="font-weight: bold;">{}</span><br><small>{}</small>',
                obj.primary_language.name,
                obj.primary_language.code
            )
        return format_html('<span style="color: #999;">Not set</span>')
    language_display.short_description = 'Language'
    
    def writing_mode_display(self, obj):
        if obj.writing_mode == 'paragraph':
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">📝 Paragraph Mode</span>'
            )
        return format_html(
            '<span style="color: #007bff;">✏️ Normal Mode</span>'
        )
    writing_mode_display.short_description = 'Writing Mode'

    def pdf_status(self, obj):
        """Display PDF status with clear indicators"""
        if obj.pdf_file:
            try:
                size_kb = obj.pdf_file.size // 1024 if obj.pdf_file.size else 0
                return format_html(
                    '<div style="display: flex; align-items: center; gap: 8px;">'
                    '<span style="color: #28a745; font-size: 16px;">✅</span>'
                    '<div>'
                    '<div style="font-weight: bold; color: #28a745;">PDF Generated</div>'
                    '<div style="font-size: 11px; color: #666;">{} KB • {}</div>'
                    '</div>'
                    '</div>',
                    size_kb,
                    obj.pdf_generated_at.strftime('%Y-%m-%d') if obj.pdf_generated_at else 'Unknown'
                )
            except:
                return format_html(
                    '<div style="display: flex; align-items: center; gap: 8px;">'
                    '<span style="color: orange; font-size: 16px;">⚠️</span>'
                    '<div style="color: orange; font-weight: bold;">File Error</div>'
                    '</div>'
                )
        elif obj.formatted_content:
            # Has formatted content but no PDF yet
            words = len(obj.formatted_content.split()) if obj.formatted_content else 0
            return format_html(
                '<div style="display: flex; align-items: center; gap: 8px;">'
                '<span style="color: #007bff; font-size: 16px;">📝</span>'
                '<div>'
                '<div style="font-weight: bold; color: #007bff;">Yes (Formatted)</div>'
                '<div style="font-size: 11px; color: #666;">{} words • Ready for PDF</div>'
                '</div>'
                '</div>',
                words
            )
        elif obj.content:
            # Has plain content only
            words = len(obj.content.split()) if obj.content else 0
            return format_html(
                '<div style="display: flex; align-items: center; gap: 8px;">'
                '<span style="color: #ffc107; font-size: 16px;">📄</span>'
                '<div>'
                '<div style="font-weight: bold; color: #ffc107;">Plain Text Only</div>'
                '<div style="font-size: 11px; color: #666;">{} words • Needs formatting</div>'
                '</div>'
                '</div>',
                words
            )
        else:
            # No content at all
            return format_html(
                '<div style="display: flex; align-items: center; gap: 8px;">'
                '<span style="color: #dc3545; font-size: 16px;">❌</span>'
                '<div style="color: #dc3545; font-weight: bold;">No Content</div>'
                '</div>'
            )
    pdf_status.short_description = 'PDF Status'

    def pdf_actions(self, obj):
        if obj.pdf_file and hasattr(obj.pdf_file, 'url'):
            return format_html(
                '<div style="display: flex; gap: 5px;">'
                '<a href="{}" target="_blank" class="button" style="background: #28a745; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 12px;">👁️ View</a>'
                '<a href="{}" class="button" style="background: #17a2b8; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 12px;">📥 Download</a>'
                '</div>',
                obj.pdf_file.url,
                reverse('admin:essay_essay_download_pdf', args=[obj.id]),
            )
        elif obj.formatted_content:
            return format_html(
                '<span style="display: inline-flex; align-items: center; gap: 5px; color: #007bff; background: #e7f1ff; padding: 4px 10px; border-radius: 4px; font-size: 12px;">'
                '<span>📝</span>'
                '<span>Formatted content ready</span>'
                '</span>'
            )
        elif obj.content:
            return format_html(
                '<span style="display: inline-flex; align-items: center; gap: 5px; color: #6c757d; background: #f8f9fa; padding: 4px 10px; border-radius: 4px; font-size: 12px;">'
                '<span>📄</span>'
                '<span>Plain text only</span>'
                '</span>'
            )
        return format_html(
            '<span style="color: #999; font-size: 12px;">No content</span>'
        )
    pdf_actions.short_description = 'Actions'

    # ----- Content Display Methods -----
    def content_preview(self, obj):
        """Show plain content preview"""
        if obj.content:
            return format_html(
                '<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; max-height: 200px; overflow-y: auto;">'
                '<h4 style="margin-top: 0; color: #6c757d; font-size: 14px;">📄 Plain Text Content</h4>'
                '<hr style="margin: 10px 0;">'
                '<pre style="white-space: pre-wrap; font-family: Arial, sans-serif; margin: 0; font-size: 13px;">{}</pre>'
                '</div>',
                obj.content[:1000] + "..." if len(obj.content) > 1000 else obj.content
            )
        return "No plain text content"
    content_preview.short_description = 'Plain Text Preview'

    def formatted_content_display(self, obj):
        """Show formatted content in admin"""
        if obj.formatted_content:
            return format_html(
                '<div style="background: #e8f4f8; padding: 15px; border-radius: 5px; margin: 10px 0; max-height: 400px; overflow-y: auto;">'
                '<h4 style="margin-top: 0; color: #007bff; font-size: 14px;">🎨 Formatted Content (Used for PDF)</h4>'
                '<hr style="margin: 10px 0;">'
                '<div style="font-family: Arial, sans-serif; line-height: 1.6; font-size: 14px;">{}</div>'
                '</div>',
                obj.formatted_content
            )
        elif obj.writing_mode == 'paragraph':
            # For paragraph mode essays, show paragraphs
            paragraphs = Paragraph.objects.filter(essay=obj).order_by('paragraph_number')
            if paragraphs.exists():
                content_html = ""
                for para in paragraphs:
                    content_html += f'<div style="margin-bottom: 15px; padding: 10px; background: white; border-radius: 4px; border-left: 3px solid #28a745;">'
                    content_html += f'<strong>Paragraph {para.paragraph_number}:</strong><br>'
                    content_html += f'{para.content}'
                    if para.formatted_content:
                        content_html += f'<div style="margin-top: 5px; padding: 5px; background: #f8f9fa; border-radius: 3px; font-size: 12px;">'
                        content_html += f'<em>Formatted: {para.formatted_content[:100]}...</em>'
                        content_html += f'</div>'
                    content_html += f'</div>'
                
                return format_html(
                    '<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; max-height: 400px; overflow-y: auto;">'
                    '<h4 style="margin-top: 0; color: #28a745; font-size: 14px;">📝 Paragraph Mode Content</h4>'
                    '<hr style="margin: 10px 0;">'
                    '{}'
                    '</div>',
                    content_html
                )
        return format_html(
            '<div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 10px 0;">'
            '<p style="margin: 0; color: #856404;">⚠️ No formatted content available. PDF generation requires formatted content.</p>'
            '</div>'
        )
    formatted_content_display.short_description = 'Formatted Content'

    def pdf_preview(self, obj):
        if obj.pdf_file and hasattr(obj.pdf_file, 'url'):
            return format_html(
                '<div style="border: 1px solid #ddd; padding: 10px; margin: 10px 0;">'
                '<h4 style="margin-top: 0; color: #28a745;">📊 PDF Preview</h4>'
                '<iframe src="{}" width="100%" height="600px" style="border: none;"></iframe>'
                '</div>',
                obj.pdf_file.url + "#toolbar=0&navpanes=0&scrollbar=0"
            )
        elif obj.formatted_content:
            # Show formatted content as it would appear in PDF
            return format_html(
                '<div style="border: 1px solid #007bff; padding: 15px; margin: 10px 0; background: #f8f9fa;">'
                '<h4 style="margin-top: 0; color: #007bff;">📝 PDF Content Preview</h4>'
                '<p style="color: #6c757d; font-size: 13px;">This is how your content will look in the PDF:</p>'
                '<div style="background: white; padding: 20px; border-radius: 5px; max-height: 400px; overflow-y: auto; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">'
                '<h1 style="text-align: center; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px;">{}</h1>'
                '<div style="font-family: Arial, sans-serif; line-height: 1.6; font-size: 14px;">{}</div>'
                '</div>'
                '</div>',
                obj.title,
                obj.formatted_content[:2000] + "..." if len(obj.formatted_content) > 2000 else obj.formatted_content
            )
        return format_html(
            '<div style="padding: 30px; text-align: center; background: #f8f9fa; border-radius: 5px; margin: 10px 0;">'
            '<h4 style="color: #6c757d;">No PDF Available</h4>'
            '<p style="color: #999;">PDF cannot be generated without formatted content.</p>'
            '</div>'
        )
    pdf_preview.short_description = 'PDF/Content Preview'

    def pdf_details(self, obj):
        if obj.pdf_file:
            try:
                file_size = obj.pdf_file.size if obj.pdf_file.size else 0
                size_mb = file_size / (1024 * 1024)
                
                return format_html(
                    '<div style="background: #d4edda; padding: 15px; border-radius: 5px;">'
                    '<h4 style="margin-top: 0; color: #155724;">📊 PDF Details</h4>'
                    '<table style="width: 100%; border-collapse: collapse;">'
                    '<tr style="border-bottom: 1px solid #c3e6cb;">'
                    '<td style="padding: 8px;"><strong>File Size:</strong></td>'
                    '<td style="padding: 8px;">{:.2f} MB</td>'
                    '</tr>'
                    '<tr style="border-bottom: 1px solid #c3e6cb;">'
                    '<td style="padding: 8px;"><strong>Generated At:</strong></td>'
                    '<td style="padding: 8px;">{}</td>'
                    '</tr>'
                    '<tr>'
                    '<td style="padding: 8px;"><strong>Writing Mode:</strong></td>'
                    '<td style="padding: 8px;">{}</td>'
                    '</tr>'
                    '</table>'
                    '</div>',
                    size_mb,
                    obj.pdf_generated_at.strftime('%Y-%m-%d %H:%M:%S') if obj.pdf_generated_at else 'N/A',
                    obj.get_writing_mode_display()
                )
            except Exception as e:
                return f"Error loading PDF details: {e}"
        
        # Show content details if no PDF
        return format_html(
            '<div style="background: #cce5ff; padding: 15px; border-radius: 5px;">'
            '<h4 style="margin-top: 0; color: #004085;">📝 Content Details</h4>'
            '<table style="width: 100%; border-collapse: collapse;">'
            '<tr style="border-bottom: 1px solid #b8daff;">'
            '<td style="padding: 8px;"><strong>Writing Mode:</strong></td>'
            '<td style="padding: 8px;">{}</td>'
            '</tr>'
            '<tr style="border-bottom: 1px solid #b8daff;">'
            '<td style="padding: 8px;"><strong>Has Formatted Content:</strong></td>'
            '<td style="padding: 8px;">{}</td>'
            '</tr>'
            '<tr>'
            '<td style="padding: 8px;"><strong>Paragraphs:</strong></td>'
            '<td style="padding: 8px;">{}</td>'
            '</tr>'
            '</table>'
            '</div>',
            obj.get_writing_mode_display(),
            "✅ Yes" if obj.formatted_content else "❌ No",
            Paragraph.objects.filter(essay=obj).count()
        )
    pdf_details.short_description = 'File Information'

    # ----- Admin actions -----
    def generate_pdfs_action(self, request, queryset):
        from django.utils import timezone
        count = 0
        
        for essay in queryset:
            try:
                # Check if we have content to generate PDF
                if not essay.formatted_content and essay.content:
                    # Create basic formatted content from plain text
                    paragraphs = [p.strip() for p in essay.content.split('\n\n') if p.strip()]
                    formatted_paragraphs = []
                    
                    for para in paragraphs:
                        formatted_paragraphs.append(f'<p style="margin-bottom: 15px; line-height: 1.6;">{para}</p>')
                    
                    if formatted_paragraphs:
                        essay.formatted_content = '\n'.join(formatted_paragraphs)
                        essay.save()
                
                if essay.formatted_content:
                    # Mark as PDF generated (in real app, you'd generate actual PDF)
                    essay.pdf_generated_at = timezone.now()
                    
                    # Add success message
                    self.message_user(
                        request,
                        f"✓ PDF ready for '{essay.title}' (Formatted content available)",
                        level='success'
                    )
                    count += 1
                else:
                    self.message_user(
                        request,
                        f"⚠️ No content for PDF generation: '{essay.title}'",
                        level='warning'
                    )
                    
            except Exception as e:
                self.message_user(
                    request,
                    f"❌ Error with '{essay.title}': {str(e)}",
                    level='error'
                )
        
        if count > 0:
            self.message_user(request, f"✅ Processed {count} essays for PDF generation.", level='success')
    generate_pdfs_action.short_description = "📄 Generate PDFs (Mark as ready)"

    def delete_pdfs_action(self, request, queryset):
        count = 0
        for essay in queryset:
            if essay.pdf_file:
                essay.pdf_file.delete(save=False)
                essay.pdf_file = None
                essay.pdf_generated_at = None
                essay.save()
                count += 1
        
        if count > 0:
            self.message_user(request, f"🗑️ Deleted PDFs for {count} essays.", level='success')
        else:
            self.message_user(request, "No PDFs to delete.", level='info')
    delete_pdfs_action.short_description = "🗑️ Delete PDFs"

    def export_as_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="essays_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Title', 'Author', 'Language', 'Word Count', 
            'Status', 'Writing Mode', 'Formatted Content', 
            'PDF Generated', 'Created At'
        ])
        
        for essay in queryset:
            writer.writerow([
                essay.title,
                essay.author.username,
                essay.primary_language.name if essay.primary_language else '',
                essay.word_count,
                essay.get_status_display(),
                essay.get_writing_mode_display(),
                'Yes' if essay.formatted_content else 'No',
                'Yes' if essay.pdf_generated_at else 'No',
                essay.created_at.strftime('%Y-%m-%d %H:%M')
            ])
        
        return response
    export_as_csv.short_description = "📊 Export as CSV"

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
            self.message_user(request, "No PDF file available for download.", level='error')
            return HttpResponseRedirect(reverse('admin:essay_essay_change', args=[object_id]))

        response = FileResponse(essay.pdf_file.open(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{essay.title.replace(" ", "_")}.pdf"'
        return response


# ========== USER PROFILE ADMIN ==========
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'preferred_language_display', 'is_verified_badge', 'points', 'essays_count')
    list_filter = ('role', 'is_verified')
    search_fields = ('user__username', 'student_id')
    readonly_fields = ('id', 'created_at', 'updated_at', 'essays_count_display')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'role', 'student_id', 'bio')
        }),
        ('Preferences', {
            'fields': ('preferred_language',)
        }),
        ('Verification', {
            'fields': ('is_verified',)
        }),
        ('Statistics', {
            'fields': ('points', 'leaderboard_score', 'essays_count_display')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def preferred_language_display(self, obj):
        if obj.preferred_language:
            return format_html(
                '<span style="font-weight: bold;">{}</span><br><small>{}</small>',
                obj.preferred_language.name,
                obj.preferred_language.code
            )
        return "-"
    preferred_language_display.short_description = 'Preferred Language'
    
    def is_verified_badge(self, obj):
        if obj.is_verified:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 10px; font-size: 12px;">✅ Verified</span>'
            )
        return format_html(
            '<span style="background: #6c757d; color: white; padding: 3px 8px; border-radius: 10px; font-size: 12px;">⏳ Pending</span>'
        )
    is_verified_badge.short_description = 'Verification'
    
    def essays_count(self, obj):
        count = Essay.objects.filter(author=obj.user).count()
        return format_html(
            '<span style="font-weight: bold; color: #007bff;">{}</span>',
            count
        )
    essays_count.short_description = 'Essays'
    
    def essays_count_display(self, obj):
        count = Essay.objects.filter(author=obj.user).count()
        return format_html(
            '<div style="background: #e9ecef; padding: 10px; border-radius: 5px;">'
            '<h4 style="margin-top: 0; color: #495057;">Essay Statistics</h4>'
            '<p><strong>Total Essays Written:</strong> <span style="color: #007bff; font-size: 18px;">{}</span></p>'
            '</div>',
            count
        )
    essays_count_display.short_description = 'Essay Statistics'


# ========== COMMENT ADMIN ==========
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'essay_preview', 'created_at', 'content_preview')
    list_filter = ('created_at',)
    search_fields = ('content', 'author__username', 'essay__title')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def essay_preview(self, obj):
        return format_html(
            '<a href="{}" style="font-weight: bold; color: #007bff;">{}</a>',
            reverse('admin:essay_essay_change', args=[obj.essay.id]),
            obj.essay.title[:50] + '...' if len(obj.essay.title) > 50 else obj.essay.title
        )
    essay_preview.short_description = 'Essay'
    
    def content_preview(self, obj):
        return format_html(
            '<div style="max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{}</div>',
            obj.content
        )
    content_preview.short_description = 'Comment'