# from django.contrib import admin
# from django.utils.html import format_html
# from django.urls import reverse, path
# from django.http import HttpResponseRedirect, FileResponse
# from django.shortcuts import get_object_or_404
# import os
# from .models import UserProfile, Language, Essay, Paragraph, Competition, Comment, Submission
# from .utils import generate_essay_pdf

# # Language Admin
# @admin.register(Language)
# class LanguageAdmin(admin.ModelAdmin):
#     list_display = ('name', 'code', 'is_active')
#     list_filter = ('is_active',)
#     search_fields = ('name', 'code')

# # Paragraph Admin
# class ParagraphInline(admin.TabularInline):
#     model = Paragraph
#     extra = 0
#     readonly_fields = ('paragraph_number', 'word_count', 'is_locked', 'created_at')
#     can_delete = False
    
#     def has_add_permission(self, request, obj=None):
#         return False
    
#     def has_change_permission(self, request, obj=None):
#         return False

# # Essay Admin with PDF features
# @admin.register(Essay)
# class EssayAdmin(admin.ModelAdmin):
#     list_display = ('title', 'author', 'language_display', 'word_count', 'status', 
#                    'writing_mode', 'pdf_status', 'pdf_actions')
#     list_filter = ('status', 'writing_mode', 'category', 'primary_language', 'created_at', 'pdf_generated_at')
#     search_fields = ('title', 'author__username', 'content')
#     readonly_fields = ('id', 'created_at', 'updated_at', 'pdf_preview', 
#                       'pdf_details', 'word_count', 'views', 'pdf_generated_at')
#     inlines = [ParagraphInline]
#     actions = ['generate_pdfs_action', 'delete_pdfs_action', 'export_as_pdf_list']
    
#     fieldsets = (
#         ('Basic Information', {
#             'fields': ('title', 'author', 'primary_language', 'category', 'status')
#         }),
#         ('Content', {
#             'fields': ('content', 'writing_mode', 'current_paragraph', 'max_paragraphs')
#         }),
#         ('Statistics', {
#             'fields': ('word_count', 'views', 'likes', 'grammar_score', 'spelling_score', 
#                       'content_score', 'score', 'grade')
#         }),
#         ('PDF Information', {
#             'fields': ('pdf_file', 'pdf_generated_at', 'pdf_preview', 'pdf_details')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at')
#         }),
#     )
    
#     def language_display(self, obj):
#         if obj.primary_language:
#             return f"{obj.primary_language.name} ({obj.primary_language.code})"
#         return "Not set"
#     language_display.short_description = 'Language'
    
#     def pdf_status(self, obj):
#         if obj.pdf_file:
#             size_kb = obj.pdf_file.size // 1024 if obj.pdf_file.size else 0
#             return format_html(
#                 '<span style="color: green; font-weight: bold;">'
#                 '✓ Generated</span><br>'
#                 '<small>{} KB • {}</small>',
#                 size_kb,
#                 obj.pdf_generated_at.strftime('%Y-%m-%d %H:%M') if obj.pdf_generated_at else 'N/A'
#             )
#         return format_html('<span style="color: red;">✗ No PDF</span>')
#     pdf_status.short_description = 'PDF Status'
    
#     def pdf_actions(self, obj):
#         if obj.pdf_file:
#             return format_html(
#                 '<a href="{}" target="_blank" class="button">👁️ View</a>&nbsp;'
#                 '<a href="{}" class="button">📥 Download</a>&nbsp;'
#                 '<a href="{}" class="button" style="color: red;">🗑️ Delete</a>',
#                 obj.pdf_file.url,
#                 reverse('admin:essay_essay_download_pdf', args=[obj.id]),
#                 reverse('admin:essay_essay_delete_pdf', args=[obj.id])
#             )
#         return format_html(
#             '<a href="{}" class="button">🔄 Generate PDF</a>',
#             reverse('admin:essay_essay_generate_pdf', args=[obj.id])
#         )
#     pdf_actions.short_description = 'Actions'
    
#     def pdf_preview(self, obj):
#         if obj.pdf_file:
#             return format_html(
#                 '<div style="border: 1px solid #ddd; padding: 10px; margin: 10px 0;">'
#                 '<h4>PDF Preview</h4>'
#                 '<iframe src="{}" width="100%" height="600px" '
#                 'style="border: none;"></iframe>'
#                 '</div>',
#                 obj.pdf_file.url + "#toolbar=0&navpanes=0&scrollbar=0"
#             )
#         return "No PDF available for preview"
#     pdf_preview.short_description = 'PDF Preview'
    
#     def pdf_details(self, obj):
#         if obj.pdf_file:
#             pdf_path = obj.pdf_file.path
#             file_exists = os.path.exists(pdf_path)
#             file_size = os.path.getsize(pdf_path) if file_exists else 0
            
#             return format_html(
#                 '<div style="background: #f5f5f5; padding: 15px; border-radius: 5px;">'
#                 '<h4>📊 PDF Details</h4>'
#                 '<table style="width: 100%;">'
#                 '<tr><td><strong>File Path:</strong></td><td><code>{}</code></td></tr>'
#                 '<tr><td><strong>File Exists:</strong></td><td>{}</td></tr>'
#                 '<tr><td><strong>File Size:</strong></td><td>{:.2f} MB</td></tr>'
#                 '<tr><td><strong>Generated At:</strong></td><td>{}</td></tr>'
#                 '<tr><td><strong>Media URL:</strong></td><td><a href="{}" target="_blank">{}</a></td></tr>'
#                 '</table>'
#                 '</div>',
#                 pdf_path,
#                 '✅ Yes' if file_exists else '❌ No',
#                 file_size / (1024 * 1024),
#                 obj.pdf_generated_at.strftime('%Y-%m-%d %H:%M:%S') if obj.pdf_generated_at else 'N/A',
#                 obj.pdf_file.url,
#                 obj.pdf_file.url
#             )
#         return "No PDF details available"
#     pdf_details.short_description = 'PDF File Information'
    
#     # Custom admin actions
#     def generate_pdfs_action(self, request, queryset):
#         count = 0
#         for essay in queryset:
#             if generate_essay_pdf(essay):
#                 count += 1
#         self.message_user(request, f"Generated PDFs for {count} essays.")
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
    
#     def export_as_pdf_list(self, request, queryset):
#         import csv
#         from django.http import HttpResponse
        
#         response = HttpResponse(content_type='text/csv')
#         response['Content-Disposition'] = 'attachment; filename="essays_pdf_list.csv"'
        
#         writer = csv.writer(response)
#         writer.writerow(['Title', 'Author', 'Language', 'Word Count', 
#                         'PDF Generated', 'PDF URL', 'Generated At'])
        
#         for essay in queryset:
#             pdf_url = essay.pdf_file.url if essay.pdf_file else ''
#             generated_at = essay.pdf_generated_at.strftime('%Y-%m-%d %H:%M') if essay.pdf_generated_at else ''
#             writer.writerow([
#                 essay.title,
#                 essay.author.username,
#                 essay.primary_language.name if essay.primary_language else '',
#                 essay.word_count,
#                 'Yes' if essay.pdf_file else 'No',
#                 pdf_url,
#                 generated_at
#             ])
        
#         return response
#     export_as_pdf_list.short_description = "Export PDF information as CSV"
    
#     # Custom admin views
#     def get_urls(self):
#         urls = super().get_urls()
#         custom_urls = [
#             path('<uuid:object_id>/generate-pdf/', self.admin_site.admin_view(self.generate_pdf_view), 
#                  name='essay_essay_generate_pdf'),
#             path('<uuid:object_id>/download-pdf/', self.admin_site.admin_view(self.download_pdf_view), 
#                  name='essay_essay_download_pdf'),
#             path('<uuid:object_id>/delete-pdf/', self.admin_site.admin_view(self.delete_pdf_view), 
#                  name='essay_essay_delete_pdf'),
#         ]
#         return custom_urls + urls
    
#     def generate_pdf_view(self, request, object_id):
#         essay = get_object_or_404(Essay, id=object_id)
#         if generate_essay_pdf(essay):
#             self.message_user(request, "PDF generated successfully!")
#         else:
#             self.message_user(request, "Failed to generate PDF.", level='error')
#         return HttpResponseRedirect(reverse('admin:essay_essay_change', args=[object_id]))
    
#     def download_pdf_view(self, request, object_id):
#         essay = get_object_or_404(Essay, id=object_id)
#         if not essay.pdf_file:
#             self.message_user(request, "No PDF available.", level='error')
#             return HttpResponseRedirect(reverse('admin:essay_essay_change', args=[object_id]))
        
#         response = FileResponse(essay.pdf_file.open(), content_type='application/pdf')
#         response['Content-Disposition'] = f'attachment; filename="{essay.title}.pdf"'
#         return response
    
#     def delete_pdf_view(self, request, object_id):
#         essay = get_object_or_404(Essay, id=object_id)
#         if essay.pdf_file:
#             essay.pdf_file.delete(save=False)
#             essay.pdf_file = None
#             essay.pdf_generated_at = None
#             essay.save()
#             self.message_user(request, "PDF deleted successfully!")
#         else:
#             self.message_user(request, "No PDF to delete.", level='error')
#         return HttpResponseRedirect(reverse('admin:essay_essay_change', args=[object_id]))

# # UserProfile Admin
# @admin.register(UserProfile)
# class UserProfileAdmin(admin.ModelAdmin):
#     list_display = ('user', 'role', 'preferred_language', 'is_verified', 'points')
#     list_filter = ('role', 'is_verified')
#     search_fields = ('user__username', 'student_id')

# # Competition Admin
# @admin.register(Competition)
# class CompetitionAdmin(admin.ModelAdmin):
#     list_display = ('title', 'start_date', 'end_date', 'is_active', 'is_open')
#     list_filter = ('is_active',)
#     filter_horizontal = ('allowed_languages',)

# # Comment Admin
# @admin.register(Comment)
# class CommentAdmin(admin.ModelAdmin):
#     list_display = ('author', 'essay', 'created_at')
#     search_fields = ('content', 'author__username')

# # Submission Admin
# @admin.register(Submission)
# class SubmissionAdmin(admin.ModelAdmin):
#     list_display = ('competition', 'essay', 'submitted_by', 'score', 'rank', 'submitted_at')
#     list_filter = ('competition',)
#     search_fields = ('essay__title', 'submitted_by__username')
# essay/admin.py - CLEAN VERSION


from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.http import HttpResponseRedirect, FileResponse
from django.shortcuts import get_object_or_404
import os

# Import models (EXCEPT UserProfile for now)
from .models import Language, Essay, Paragraph, Competition, Comment, Submission
from .utils import generate_essay_pdf

# ============================================
# DO NOT import UserProfile here for now
# ============================================

# Language Admin
@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')

# Paragraph Admin
class ParagraphInline(admin.TabularInline):
    model = Paragraph
    extra = 0
    readonly_fields = ('paragraph_number', 'word_count', 'is_locked', 'created_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

# In essay/admin.py - Replace EssayAdmin with this:

@admin.register(Essay)
class EssayAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'language_display', 'word_count', 'status', 
                   'writing_mode', 'pdf_status', 'pdf_actions')
    list_filter = ('status', 'writing_mode', 'category', 'primary_language', 'created_at', 'pdf_generated_at')
    search_fields = ('title', 'author__username', 'content')
    readonly_fields = ('id', 'created_at', 'updated_at', 'word_count', 'views', 
                      'pdf_generated_at', 'pdf_preview', 'pdf_details')
    inlines = [ParagraphInline]
    actions = ['generate_pdfs_action', 'delete_pdfs_action', 'export_as_pdf_list']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'author', 'primary_language', 'category', 'status')
        }),
        ('Content', {
            'fields': ('content', 'writing_mode', 'current_paragraph', 'max_paragraphs')
        }),
        ('Statistics', {
            'fields': ('word_count', 'views', 'grammar_score', 'spelling_score', 
                      'content_score', 'score', 'grade')
        }),
        ('PDF Information', {
            'fields': ('pdf_file', 'pdf_generated_at', 'pdf_preview', 'pdf_details')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
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
                    '<span style="color: green; font-weight: bold;">'
                    '✓ Generated</span><br>'
                    '<small>{} KB • {}</small>',
                    size_kb,
                    obj.pdf_generated_at.strftime('%Y-%m-%d %H:%M') if obj.pdf_generated_at else 'N/A'
                )
            except:
                return format_html('<span style="color: orange;">⚠️ File error</span>')
        return format_html('<span style="color: red;">✗ No PDF</span>')
    pdf_status.short_description = 'PDF Status'
    
    def pdf_actions(self, obj):
        if obj.pdf_file:
            return format_html(
                '<a href="{}" target="_blank" class="button">👁️ View</a>&nbsp;'
                '<a href="{}" class="button">📥 Download</a>&nbsp;'
                '<a href="{}" class="button" style="color: red;">🗑️ Delete</a>',
                obj.pdf_file.url if obj.pdf_file else '#',
                reverse('admin:essay_essay_download_pdf', args=[obj.id]),
                reverse('admin:essay_essay_delete_pdf', args=[obj.id])
            )
        return format_html(
            '<a href="{}" class="button">🔄 Generate PDF</a>',
            reverse('admin:essay_essay_generate_pdf', args=[obj.id])
        )
    pdf_actions.short_description = 'Actions'
    
    def pdf_preview(self, obj):
        if obj.pdf_file and hasattr(obj.pdf_file, 'url'):
            return format_html(
                '<div style="border: 1px solid #ddd; padding: 10px; margin: 10px 0;">'
                '<h4>PDF Preview</h4>'
                '<iframe src="{}" width="100%" height="600px" '
                'style="border: none;"></iframe>'
                '</div>',
                obj.pdf_file.url + "#toolbar=0&navpanes=0&scrollbar=0"
            )
        return "No PDF available for preview"
    pdf_preview.short_description = 'PDF Preview'
    
    def pdf_details(self, obj):
        if obj.pdf_file:
            try:
                pdf_path = obj.pdf_file.path
                file_exists = os.path.exists(pdf_path)
                file_size = os.path.getsize(pdf_path) if file_exists else 0
                
                return format_html(
                    '<div style="background: #f5f5f5; padding: 15px; border-radius: 5px;">'
                    '<h4>📊 PDF Details</h4>'
                    '<table style="width: 100%;">'
                    '<tr><td><strong>File Path:</strong></td><td><code>{}</code></td></tr>'
                    '<tr><td><strong>File Exists:</strong></td><td>{}</td></tr>'
                    '<tr><td><strong>File Size:</strong></td><td>{:.2f} MB</td></tr>'
                    '<tr><td><strong>Generated At:</strong></td><td>{}</td></tr>'
                    '<tr><td><strong>Media URL:</strong></td><td><a href="{}" target="_blank">{}</a></td></tr>'
                    '</table>'
                    '</div>',
                    pdf_path,
                    '✅ Yes' if file_exists else '❌ No',
                    file_size / (1024 * 1024),
                    obj.pdf_generated_at.strftime('%Y-%m-%d %H:%M:%S') if obj.pdf_generated_at else 'N/A',
                    obj.pdf_file.url if obj.pdf_file else '#',
                    obj.pdf_file.url if obj.pdf_file else 'Not available'
                )
            except Exception as e:
                return format_html(
                    '<div style="background: #fff3cd; padding: 15px; border-radius: 5px; color: #856404;">'
                    '<h4>⚠️ PDF Error</h4>'
                    '<p>Error accessing PDF: {}</p>'
                    '</div>',
                    str(e)
                )
        return "No PDF details available"
    pdf_details.short_description = 'PDF File Information'
    
    # Custom admin actions
    def generate_pdfs_action(self, request, queryset):
        count = 0
        for essay in queryset:
            if generate_essay_pdf(essay):
                count += 1
        self.message_user(request, f"Generated PDFs for {count} essays.")
    generate_pdfs_action.short_description = "Generate PDFs for selected essays"
    
    def delete_pdfs_action(self, request, queryset):
        count = 0
        for essay in queryset:
            if essay.pdf_file:
                try:
                    essay.pdf_file.delete(save=False)
                    essay.pdf_file = None
                    essay.pdf_generated_at = None
                    essay.save()
                    count += 1
                except Exception as e:
                    self.message_user(request, f"Error deleting PDF for {essay.title}: {e}", level='error')
        self.message_user(request, f"Deleted PDFs for {count} essays.")
    delete_pdfs_action.short_description = "Delete PDFs from selected essays"
    
    def export_as_pdf_list(self, request, queryset):
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="essays_pdf_list.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Title', 'Author', 'Language', 'Word Count', 
                        'PDF Generated', 'PDF URL', 'Generated At'])
        
        for essay in queryset:
            pdf_url = essay.pdf_file.url if essay.pdf_file and hasattr(essay.pdf_file, 'url') else ''
            generated_at = essay.pdf_generated_at.strftime('%Y-%m-%d %H:%M') if essay.pdf_generated_at else ''
            writer.writerow([
                essay.title,
                essay.author.username,
                essay.primary_language.name if essay.primary_language else '',
                essay.word_count,
                'Yes' if essay.pdf_file else 'No',
                pdf_url,
                generated_at
            ])
        
        return response
    export_as_pdf_list.short_description = "Export PDF information as CSV"
    
    # Custom admin views
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<uuid:object_id>/generate-pdf/', self.admin_site.admin_view(self.generate_pdf_view), 
                 name='essay_essay_generate_pdf'),
            path('<uuid:object_id>/download-pdf/', self.admin_site.admin_view(self.download_pdf_view), 
                 name='essay_essay_download_pdf'),
            path('<uuid:object_id>/delete-pdf/', self.admin_site.admin_view(self.delete_pdf_view), 
                 name='essay_essay_delete_pdf'),
        ]
        return custom_urls + urls
    
    def generate_pdf_view(self, request, object_id):
        essay = get_object_or_404(Essay, id=object_id)
        if generate_essay_pdf(essay):
            self.message_user(request, "PDF generated successfully!")
        else:
            self.message_user(request, "Failed to generate PDF.", level='error')
        return HttpResponseRedirect(reverse('admin:essay_essay_change', args=[object_id]))
    
    def download_pdf_view(self, request, object_id):
        essay = get_object_or_404(Essay, id=object_id)
        if not essay.pdf_file:
            self.message_user(request, "No PDF available.", level='error')
            return HttpResponseRedirect(reverse('admin:essay_essay_change', args=[object_id]))
        
        try:
            response = FileResponse(essay.pdf_file.open(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{essay.title}.pdf"'
            return response
        except Exception as e:
            self.message_user(request, f"Error downloading PDF: {e}", level='error')
            return HttpResponseRedirect(reverse('admin:essay_essay_change', args=[object_id]))
    
    def delete_pdf_view(self, request, object_id):
        essay = get_object_or_404(Essay, id=object_id)
        if essay.pdf_file:
            try:
                essay.pdf_file.delete(save=False)
                essay.pdf_file = None
                essay.pdf_generated_at = None
                essay.save()
                self.message_user(request, "PDF deleted successfully!")
            except Exception as e:
                self.message_user(request, f"Error deleting PDF: {e}", level='error')
        else:
            self.message_user(request, "No PDF to delete.", level='error')
        return HttpResponseRedirect(reverse('admin:essay_essay_change', args=[object_id]))