import os
from io import BytesIO
from datetime import datetime, timedelta
from django.conf import settings
from django.core.files import File
from django.core.files.base import ContentFile

from django.utils import timezone
from django.db.models import Avg
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib import colors
from bs4 import BeautifulSoup
from .models import Essay, UserProfile


# ==============================================================
# 🧾 PDF GENERATION (clean + safe)
# ==============================================================

def generate_essay_pdf(essay):
    """
    Generate a well-formatted PDF for an Essay and save it.
    Compatible with both single and paragraph-based essays.
    """
    try:
        if not essay.content and not essay.paragraphs.exists():
            print(f"⚠️ Skipping empty essay: {essay.title}")
            return False

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        styles = getSampleStyleSheet()

        # Title and body styles
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=20,
            textColor=colors.HexColor('#3949ab'),
            alignment=1
        )

        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['BodyText'],
            fontSize=12,
            leading=18,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        )

        story = []

        # Title
        story.append(Paragraph(essay.title, title_style))
        story.append(Spacer(1, 20))

        # Meta info
        meta_text = f"""
        <b>Author:</b> {essay.author.username}<br/>
        <b>Created:</b> {essay.created_at.strftime('%B %d, %Y')}<br/>
        <b>Language:</b> {essay.primary_language.name if essay.primary_language else 'English'}<br/>
        <b>Word Count:</b> {essay.word_count}<br/>
        <b>Category:</b> {essay.get_category_display()}
        """
        story.append(Paragraph(meta_text, body_style))
        story.append(Spacer(1, 30))

        # Content
        if hasattr(essay, 'paragraphs') and essay.paragraphs.exists():
            for idx, para in enumerate(essay.paragraphs.all().order_by('paragraph_number'), 1):
                story.append(Paragraph(f"<b>Paragraph {idx}</b>", body_style))
                story.append(Spacer(1, 5))
                soup = BeautifulSoup(para.content, 'html.parser')
                clean_text = soup.get_text()
                story.append(Paragraph(clean_text, body_style))
                story.append(Spacer(1, 15))
        else:
            soup = BeautifulSoup(essay.content or "", 'html.parser')
            clean_text = soup.get_text()
            story.append(Paragraph(clean_text, body_style))

        # Analytics Page
        story.append(PageBreak())
        story.append(Paragraph("Essay Analytics", title_style))
        story.append(Spacer(1, 20))
        analytics = f"""
        • Grammar: {essay.grammar_score:.1f}/10<br/>
        • Spelling: {essay.spelling_score:.1f}/10<br/>
        • Content: {essay.content_score:.1f}/10<br/>
        • Overall Score: {essay.score:.1f}/10<br/>
        • Grade: {essay.grade or 'Not graded'}<br/>
        • Views: {essay.views}<br/>
        • Likes: {essay.likes.count()}
        """
        story.append(Paragraph(analytics, body_style))

        # Build PDF
        doc.build(story)

        # Save PDF
        buffer.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_title = ''.join(c for c in essay.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"essay_{safe_title[:50]}_{timestamp}.pdf"
        essay.pdf_file.save(filename, ContentFile(buffer.getvalue()))
        essay.pdf_generated_at = timezone.now()
        essay.save()

        buffer.close()
        print(f"✅ PDF generated successfully for: {essay.title}")
        return True

    except Exception as e:
        print(f"❌ PDF generation failed for essay {essay.id}: {str(e)}")
        return False


# ==============================================================
# 🏆 LEADERBOARD CALCULATOR (competition-free)
# ==============================================================

class LeaderboardCalculator:
    """
    Utility to calculate and update leaderboard stats without competitions.
    """

    @staticmethod
    def calculate_user_stats(user):
        """Update user's writing and activity stats."""
        try:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            essays = Essay.objects.filter(author=user, status__in=['published', 'submitted'])

            total_essays = essays.count()
            avg_score = essays.aggregate(avg=Avg('score'))['avg'] or 0.0
            total_likes = sum(essay.likes.count() for essay in essays)

            # Activity & quality bonuses
            activity_bonus = min(total_essays * 2, 50)
            like_bonus = min(total_likes * 0.5, 30)

            # Leaderboard score = essay quality + bonuses
            leaderboard_score = (avg_score * 0.7) + activity_bonus + like_bonus

            # Update profile
            profile.total_essays = total_essays
            profile.total_likes_received = total_likes
            profile.avg_essay_score = round(avg_score, 2)
            profile.leaderboard_score = round(leaderboard_score, 2)
            profile.last_score_update = timezone.now()
            profile.save()

            print(f"✅ Updated stats for user: {user.username}")
            return profile

        except Exception as e:
            print(f"❌ Error updating stats for {user.username}: {e}")
            return None

    @staticmethod
    def update_all_leaderboards():
        """Recalculate leaderboard scores for all active users."""
        from django.contrib.auth.models import User
        ninety_days_ago = timezone.now() - timedelta(days=90)

        active_users = User.objects.filter(essays__created_at__gte=ninety_days_ago).distinct()
        updated_count = 0
        for user in active_users:
            LeaderboardCalculator.calculate_user_stats(user)
            updated_count += 1

        profiles = UserProfile.objects.filter(leaderboard_score__gt=0).order_by('-leaderboard_score')

        rank = 1
        for profile in profiles:
            profile.user.leaderboard_rank = rank
            profile.save()
            rank += 1

        print(f"🏁 Leaderboard updated for {updated_count} users.")
        return updated_count
