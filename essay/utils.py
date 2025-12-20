import os
import uuid
from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib import colors
from bs4 import BeautifulSoup
from datetime import datetime
from io import BytesIO
from django.core.files.base import ContentFile
from django.db.models import Count, Avg, Sum, Min
from django.utils import timezone
from datetime import timedelta
from .models import Essay, UserProfile, Submission

def generate_essay_pdf(essay):
    """
    Generate PDF for an essay and save it in media/essays/pdfs/
    Returns True if successful, False otherwise
    """
    try:
        # Create PDF in memory
        buffer = BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Define styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#667eea'),
            alignment=1  # Center aligned
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=12,
            leading=18,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        )
        
        # Build content
        story = []
        
        # Title
        story.append(Paragraph(essay.title, title_style))
        story.append(Spacer(1, 20))
        
        # Metadata
        meta_text = f"""
        <b>Author:</b> {essay.author.username}<br/>
        <b>Created:</b> {essay.created_at.strftime('%B %d, %Y')}<br/>
        <b>Language:</b> {essay.primary_language.name if essay.primary_language else 'English'}<br/>
        <b>Word Count:</b> {essay.word_count}<br/>
        <b>Category:</b> {essay.get_category_display()}
        """
        story.append(Paragraph(meta_text, body_style))
        story.append(Spacer(1, 40))
        
        # Content
        if essay.writing_mode == 'paragraph' and essay.paragraphs.exists():
            paragraphs = essay.paragraphs.all().order_by('paragraph_number')
            for idx, para in enumerate(paragraphs, 1):
                para_title = f"<b>Paragraph {idx}</b>"
                if para.language:
                    para_title += f" ({para.language.name})"
                if para.is_locked:
                    para_title += " [LOCKED]"
                
                story.append(Paragraph(para_title, body_style))
                story.append(Spacer(1, 10))
                
                if para.content:
                    # Clean HTML
                    soup = BeautifulSoup(para.content, 'html.parser')
                    clean_content = soup.get_text()
                    story.append(Paragraph(clean_content, body_style))
                
                story.append(Spacer(1, 20))
        else:
            # Clean HTML content
            soup = BeautifulSoup(essay.content, 'html.parser')
            clean_content = soup.get_text()
            story.append(Paragraph(clean_content, body_style))
        
        # Analytics page
        story.append(PageBreak())
        story.append(Paragraph("Essay Analytics", title_style))
        story.append(Spacer(1, 30))
        
        analytics = f"""
        <b>Detailed Analysis:</b><br/><br/>
        • <b>Total Words:</b> {essay.word_count}<br/>
        • <b>Sentences:</b> {essay.sentence_count}<br/>
        • <b>Unique Words:</b> {essay.unique_words}<br/>
        • <b>Avg Sentence Length:</b> {essay.avg_sentence_length:.1f} words<br/><br/>
        
        <b>Scores:</b><br/><br/>
        • <b>Grammar:</b> {essay.grammar_score:.1f}/10<br/>
        • <b>Spelling:</b> {essay.spelling_score:.1f}/10<br/>
        • <b>Content:</b> {essay.content_score:.1f}/10<br/>
        • <b>Overall:</b> {essay.score:.1f}/10<br/>
        • <b>Grade:</b> {essay.grade if essay.grade else 'Not graded'}<br/><br/>
        
        <b>Writing Mode:</b> {essay.get_writing_mode_display()}<br/>
        <b>Status:</b> {essay.get_status_display()}<br/>
        <b>Views:</b> {essay.views}<br/>
        <b>Likes:</b> {essay.likes.count()}
        """
        story.append(Paragraph(analytics, body_style))
        
        # Build PDF
        doc.build(story)
        
        # Save to file
        buffer.seek(0)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_title = ''.join(c for c in essay.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"essay_{safe_title[:50]}_{timestamp}.pdf"
        
        # Save PDF to essay model
        essay.pdf_file.save(filename, ContentFile(buffer.getvalue()))
        essay.pdf_generated_at = datetime.now()
        essay.save()
        
        print(f"✓ PDF generated for essay: {essay.title}")
        return True
        
    except Exception as e:
        print(f"✗ Error generating PDF for essay {essay.id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    # essay/utils.py
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.core.files import File
from django.utils import timezone
import os

def generate_essay_pdf(essay):
    """Generate PDF and save to media folder - Users cannot access directly"""
    try:
        if not essay.content:
            return False
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            fontSize=16,
            spaceAfter=30,
            alignment=1
        )
        
        meta_style = ParagraphStyle(
            'Meta',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=20,
            alignment=1,
            textColor=colors.gray
        )
        
        content_style = ParagraphStyle(
            'Content',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            leading=14
        )
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.gray,
            alignment=1
        )
        
        # Build story
        story = []
        
        # Title
        story.append(Paragraph(essay.title, title_style))
        
        # Metadata
        meta_text = f"""
        Author: {essay.author.username} | 
        Created: {essay.created_at.strftime('%B %d, %Y')} | 
        Words: {essay.word_count} | 
        Grade: {essay.grade or 'N/A'}
        """
        story.append(Paragraph(meta_text, meta_style))
        story.append(Spacer(1, 20))
        
        # Content
        paragraphs = essay.content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                story.append(Paragraph(para.replace('\n', '<br/>'), content_style))
                story.append(Spacer(1, 8))
        
        # Footer with scores
        if essay.grammar_score > 0 or essay.spelling_score > 0:
            story.append(Spacer(1, 30))
            scores_text = f"""
            Grammar: {essay.grammar_score:.1f}% | 
            Spelling: {essay.spelling_score:.1f}% | 
            Overall: {essay.score:.1f}%
            """
            story.append(Paragraph(scores_text, footer_style))
        
        # Build PDF
        doc.build(story)
        
        # Save to media folder
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        safe_title = ''.join(c for c in essay.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        pdf_name = f'essay_{essay.id}_{safe_title[:50]}_{timestamp}.pdf'
        
        # Delete old PDF if exists
        if essay.pdf_file:
            try:
                essay.pdf_file.delete(save=False)
            except:
                pass
        
        # Save new PDF
        essay.pdf_file.save(pdf_name, File(buffer))
        essay.pdf_generated_at = timezone.now()
        essay.save()
        
        buffer.close()
        
        # Log PDF generation
        print(f"✅ PDF generated: {pdf_name}")
        print(f"   Path: {essay.pdf_file.path}")
        print(f"   URL: {essay.pdf_file.url}")
        print(f"   Size: {essay.pdf_file.size // 1024} KB")
        
        return True
        
    except Exception as e:
        print(f"❌ PDF generation failed: {str(e)}")
        return False
    
    
    # Add to utils.py (at the end or beginning)


class LeaderboardCalculator:
    """Utility class to calculate and update leaderboard scores"""
    
    @staticmethod
    def calculate_user_stats(user):
        """Calculate and update user statistics"""
        try:
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            # Get all published essays by user
            essays = Essay.objects.filter(
                author=user, 
                status__in=['published', 'submitted']
            )
            
            total_essays = essays.count()
            
            # Calculate average scores
            if total_essays > 0:
                avg_score = essays.aggregate(avg=Avg('score'))['avg'] or 0.0
                total_likes = sum(essay.likes.count() for essay in essays)
            else:
                avg_score = 0.0
                total_likes = 0
            
            # Get competition stats
            submissions = Submission.objects.filter(submitted_by=user)
            competitions_entered = submissions.count()
            
            # Count wins (rank 1, 2, or 3)
            competitions_won = submissions.filter(rank__lte=3).count()
            
            # Get best rank (lowest number is best)
            best_rank_obj = submissions.exclude(rank__isnull=True).order_by('rank').first()
            best_rank = best_rank_obj.rank if best_rank_obj else 0
            
            # Calculate leaderboard score using your existing formula
            # Grammar (40%) + Content (30%) + Spelling (30%) from essay.score
            # Plus bonuses for activity and competitions
            
            activity_bonus = min(total_essays * 2, 50)  # Cap at 50
            like_bonus = min(total_likes * 0.5, 30)     # Cap at 30
            competition_bonus = 0
            
            if best_rank > 0:
                if best_rank == 1:
                    competition_bonus = 50
                elif best_rank == 2:
                    competition_bonus = 30
                elif best_rank == 3:
                    competition_bonus = 20
                else:
                    competition_bonus = max(0, 10 - (best_rank - 3))
            
            leaderboard_score = (
                (avg_score * 0.7) +      # 70% essay quality
                activity_bonus +         # Activity bonus
                like_bonus +            # Popularity bonus
                competition_bonus       # Competition bonus
            )
            
            # Update profile
            profile.total_essays = total_essays
            profile.total_likes_received = total_likes
            profile.avg_essay_score = round(avg_score, 2)
            profile.leaderboard_score = round(leaderboard_score, 2)
            profile.competitions_entered = competitions_entered
            profile.competitions_won = competitions_won
            profile.best_competition_rank = best_rank
            profile.last_score_update = timezone.now()
            profile.save()
            
            return profile
            
        except Exception as e:
            print(f"Error calculating user stats: {e}")
            return None
    
    @staticmethod
    def update_all_leaderboards():
        """Update leaderboard scores for all users"""
        from django.contrib.auth.models import User
        
        # Get active users (with essays in last 90 days)
        ninety_days_ago = timezone.now() - timedelta(days=90)
        active_users = User.objects.filter(
            essays__created_at__gte=ninety_days_ago
        ).distinct()
        
        updated_count = 0
        for user in active_users:
            LeaderboardCalculator.calculate_user_stats(user)
            updated_count += 1
        
        # Update ranks
        profiles = UserProfile.objects.filter(
            leaderboard_score__gt=0
        ).order_by('-leaderboard_score')
        
        rank = 1
        for profile in profiles:
            profile.user.leaderboard_rank = rank
            profile.save()
            rank += 1
        
        return updated_count