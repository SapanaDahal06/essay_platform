import os
import re
from io import BytesIO
from datetime import datetime, timedelta
from collections import Counter
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
# 📊 ESSAY ANALYSIS & METRICS
# ==============================================================

def calculate_essay_metrics(content):
    """Calculate basic essay metrics"""
    words = [word for word in content.split() if word.strip()]
    word_count = len(words)
    character_count = len(content)
    sentences = re.split(r'[.!?]+', content)
    sentence_count = len([s for s in sentences if s.strip()])
    paragraphs = [p for p in content.split('\n\n') if p.strip()]
    paragraph_count = len(paragraphs)
    
    return {
        'word_count': word_count,
        'character_count': character_count,
        'sentence_count': sentence_count,
        'paragraph_count': paragraph_count
    }

def analyze_vocabulary(content):
    """Analyze vocabulary usage"""
    words = [word.lower() for word in content.split() if word.strip()]
    unique_words = set(words)
    
    # Calculate Type-Token Ratio
    ttr = len(unique_words) / len(words) if words else 0
    
    # Find most frequent words
    word_freq = Counter(words)
    common_words = word_freq.most_common(10)
    
    # Check for word variety
    word_variety = "Good" if ttr > 0.6 else "Average" if ttr > 0.4 else "Needs Improvement"
    
    return {
        'unique_words': len(unique_words),
        'total_words': len(words),
        'ttr': round(ttr * 100, 2),
        'ttr_percentage': ttr,
        'word_variety': word_variety,
        'common_words': common_words,
        'sentence_count': len(re.split(r'[.!?]+', content)),
        'avg_sentence_length': len(words) / max(1, len(re.split(r'[.!?]+', content)))
    }

def check_grammar_issues(content):
    """Check for common grammar issues"""
    issues = []
    
    # Check for run-on sentences (sentences starting with lowercase after punctuation)
    run_on_pattern = r'[.!?]\s+[a-z]'
    run_ons = re.findall(run_on_pattern, content)
    if run_ons:
        issues.append({
            'type': 'run_on',
            'count': len(run_ons),
            'description': f'Found {len(run_ons)} possible run-on sentences',
            'severity': 'medium',
            'suggestion': 'Start new sentences with capital letters. Consider breaking long sentences into shorter ones.'
        })
    
    # Check for sentence fragments
    fragments = re.findall(r'^[a-z][^.!?]*$', content, re.MULTILINE)
    fragments = [f for f in fragments if len(f.split()) < 10]  # Only short fragments
    if fragments:
        issues.append({
            'type': 'fragment',
            'count': len(fragments),
            'description': f'Found {len(fragments)} possible sentence fragments',
            'severity': 'low',
            'suggestion': 'Complete these thoughts or combine them with other sentences.'
        })
    
    # Check for passive voice
    passive_pattern = r'\b(am|are|is|was|were|be|being|been)\s+\w+ed\b'
    passive = re.findall(passive_pattern, content, re.IGNORECASE)
    if passive:
        issues.append({
            'type': 'passive',
            'count': len(passive),
            'description': f'Found {len(passive)} possible passive voice constructions',
            'severity': 'low',
            'suggestion': 'Use active voice for stronger writing (e.g., "The team completed the project" instead of "The project was completed by the team").'
        })
    
    # Check for repeated words
    words = content.lower().split()
    word_counts = Counter(words)
    repeated = [(word, count) for word, count in word_counts.items() if count > 3 and len(word) > 3]
    if repeated:
        issues.append({
            'type': 'repetition',
            'count': len(repeated),
            'description': f'Found {len(repeated)} words used too frequently',
            'severity': 'low',
            'suggestion': 'Use synonyms or rephrase to avoid repetition.',
            'repeated_words': repeated[:5]  # Show top 5
        })
    
    return issues

def check_spelling(content):
    """Check for common spelling mistakes"""
    common_mistakes = {
        'seperate': 'separate',
        'definately': 'definitely',
        'occured': 'occurred',
        'recieve': 'receive',
        'wierd': 'weird',
        'accomodate': 'accommodate',
        'embarass': 'embarrass',
        'mispell': 'misspell',
        'truely': 'truly',
        'argument': 'argument',
        'government': 'government',
        'environment': 'environment',
        'developement': 'development',
        'judgement': 'judgment',
        'occassion': 'occasion',
        'occurrance': 'occurrence',
        'persistance': 'persistence',
        'refered': 'referred',
        'tommorow': 'tomorrow',
        'untill': 'until',
        'wich': 'which',
        'alot': 'a lot',
        'could of': 'could have',
        'should of': 'should have',
        'would of': 'would have',
        'your': 'you\'re',
        'their': 'they\'re',
        'its': 'it\'s',
        'than': 'then',
        'then': 'than',
        'effect': 'affect',
        'affect': 'effect',
        'loose': 'lose',
        'loosing': 'losing',
        'definate': 'definite',
        'independant': 'independent',
        'maintainance': 'maintenance',
        'neccessary': 'necessary',
        'occurence': 'occurrence',
        'seperate': 'separate',
        'successful': 'successful',
    }
    
    content_lower = content.lower()
    found_errors = {}
    
    # Check single words
    words = content_lower.split()
    for word in words:
        clean_word = re.sub(r'[^\w\s]', '', word)
        if clean_word in common_mistakes:
            if clean_word not in found_errors:
                found_errors[clean_word] = {
                    'correction': common_mistakes[clean_word],
                    'count': 1
                }
            else:
                found_errors[clean_word]['count'] += 1
    
    # Check common phrases
    for mistake, correction in common_mistakes.items():
        if ' ' in mistake:  # It's a phrase
            count = content_lower.count(mistake)
            if count > 0:
                found_errors[mistake] = {
                    'correction': correction,
                    'count': count
                }
    
    return found_errors

def analyze_readability(content):
    """Analyze readability using Flesch Reading Ease"""
    words = content.split()
    sentences = re.split(r'[.!?]+', content)
    
    if not words or not sentences:
        return {
            'score': 0,
            'level': 'N/A',
            'description': 'Not enough content to analyze'
        }
    
    word_count = len(words)
    sentence_count = len([s for s in sentences if s.strip()])
    
    # Estimate syllables (simple approach)
    syllable_count = sum(count_syllables(word) for word in words)
    
    # Flesch Reading Ease formula
    if word_count > 0 and sentence_count > 0:
        flesch_score = 206.835 - (1.015 * (word_count / sentence_count)) - (84.6 * (syllable_count / word_count))
    else:
        flesch_score = 0
    
    # Determine readability level
    if flesch_score >= 90:
        level = 'Very Easy'
        description = '5th grade level. Very easy to read.'
    elif flesch_score >= 80:
        level = 'Easy'
        description = '6th grade level. Easy to read.'
    elif flesch_score >= 70:
        level = 'Fairly Easy'
        description = '7th grade level. Fairly easy to read.'
    elif flesch_score >= 60:
        level = 'Standard'
        description = '8th-9th grade level. Plain English.'
    elif flesch_score >= 50:
        level = 'Fairly Difficult'
        description = '10th-12th grade level. Fairly difficult to read.'
    elif flesch_score >= 30:
        level = 'Difficult'
        description = 'College level. Difficult to read.'
    else:
        level = 'Very Difficult'
        description = 'College graduate level. Very difficult to read.'
    
    return {
        'score': round(flesch_score, 1),
        'level': level,
        'description': description,
        'sentence_count': sentence_count,
        'avg_sentence_length': round(word_count / sentence_count, 1)
    }

def count_syllables(word):
    """Count syllables in a word (approximate)"""
    word = word.lower()
    if len(word) <= 3:
        return 1
    
    vowels = 'aeiouy'
    count = 0
    prev_char_was_vowel = False
    
    for char in word:
        if char in vowels:
            if not prev_char_was_vowel:
                count += 1
            prev_char_was_vowel = True
        else:
            prev_char_was_vowel = False
    
    # Adjustments
    if word.endswith('e'):
        count -= 1
    if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
        count += 1
    if count == 0:
        count = 1
    
    return count

# ==============================================================
# 📈 SCORE CALCULATION FUNCTIONS
# ==============================================================

def calculate_grammar_score(content, issues=None):
    """Calculate grammar score based on issues found"""
    if issues is None:
        issues = check_grammar_issues(content)
    
    words = len(content.split())
    total_issues = sum(issue['count'] for issue in issues)
    
    # Base score: 100 minus penalty for issues
    issue_penalty = min(total_issues * 2, 30)  # Max 30% penalty
    score = max(50, 100 - issue_penalty)  # Minimum 50
    
    # Adjust based on sentence structure
    sentences = re.split(r'[.!?]+', content)
    if sentences:
        avg_length = words / len(sentences)
        if 15 <= avg_length <= 25:
            score += 5  # Bonus for good sentence length
    
    return min(round(score, 1), 100)

def calculate_spelling_score(errors, word_count):
    """Calculate spelling score"""
    if not errors:
        return 100
    
    error_count = sum(error['count'] for error in errors.values())
    error_rate = (error_count / max(1, word_count)) * 100
    
    if error_rate < 0.5:
        return 100
    elif error_rate < 1:
        return 95
    elif error_rate < 2:
        return 85
    elif error_rate < 3:
        return 75
    elif error_rate < 5:
        return 65
    else:
        return 55

def calculate_content_score(metrics, vocabulary):
    """Calculate content score based on structure and vocabulary"""
    score = 0
    
    # Word count (max 25 points)
    if metrics['word_count'] >= 500:
        score += 25
    elif metrics['word_count'] >= 300:
        score += 20
    elif metrics['word_count'] >= 200:
        score += 15
    elif metrics['word_count'] >= 100:
        score += 10
    else:
        score += 5
    
    # Paragraph structure (max 25 points)
    if metrics['paragraph_count'] >= 5:
        score += 25
    elif metrics['paragraph_count'] >= 3:
        score += 20
    elif metrics['paragraph_count'] >= 2:
        score += 15
    elif metrics['paragraph_count'] >= 1:
        score += 10
    
    # Sentence variety (max 25 points)
    if metrics['sentence_count'] >= 10:
        score += 25
    elif metrics['sentence_count'] >= 5:
        score += 20
    elif metrics['sentence_count'] >= 3:
        score += 15
    else:
        score += 10
    
    # Vocabulary diversity (max 25 points)
    if vocabulary['ttr_percentage'] > 0.6:
        score += 25
    elif vocabulary['ttr_percentage'] > 0.5:
        score += 20
    elif vocabulary['ttr_percentage'] > 0.4:
        score += 15
    else:
        score += 10
    
    return min(score, 100)

def calculate_overall_score(grammar_score, spelling_score, content_score):
    """Calculate overall essay score with weights"""
    weights = {
        'grammar': 0.35,
        'spelling': 0.25,
        'content': 0.40
    }
    
    overall = (
        grammar_score * weights['grammar'] +
        spelling_score * weights['spelling'] +
        content_score * weights['content']
    )
    
    return round(overall, 1)

def calculate_grade(score):
    """Convert score to letter grade"""
    if score >= 90:
        return 'A+'
    elif score >= 85:
        return 'A'
    elif score >= 80:
        return 'A-'
    elif score >= 75:
        return 'B+'
    elif score >= 70:
        return 'B'
    elif score >= 65:
        return 'B-'
    elif score >= 60:
        return 'C+'
    elif score >= 55:
        return 'C'
    elif score >= 50:
        return 'C-'
    elif score >= 40:
        return 'D'
    else:
        return 'F'

# ==============================================================
# 🧾 PDF GENERATION (clean + safe) - UPDATED
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

        # Analysis Page
        story.append(PageBreak())
        story.append(Paragraph("Essay Analysis Report", title_style))
        story.append(Spacer(1, 20))
        
        # Run analysis
        analysis_data = analyze_essay(essay.content)
        
        analytics = f"""
        <b>📊 Overall Scores:</b><br/>
        • Grammar: {analysis_data['grammar_score']}/100<br/>
        • Spelling: {analysis_data['spelling_score']}/100<br/>
        • Content: {analysis_data['content_score']}/100<br/>
        • <b>Overall: {analysis_data['overall_score']}/100 ({analysis_data['grade']})</b><br/><br/>
        
        <b>📈 Readability:</b><br/>
        • Level: {analysis_data['readability']['level']}<br/>
        • Score: {analysis_data['readability']['score']}/100<br/><br/>
        
        <b>📝 Vocabulary:</b><br/>
        • Unique Words: {analysis_data['vocabulary']['unique_words']}<br/>
        • Word Variety: {analysis_data['vocabulary']['word_variety']}<br/><br/>
        
        <b>📋 Statistics:</b><br/>
        • Word Count: {analysis_data['metrics']['word_count']}<br/>
        • Sentences: {analysis_data['metrics']['sentence_count']}<br/>
        • Paragraphs: {analysis_data['metrics']['paragraph_count']}
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
# 🎯 MAIN ANALYSIS FUNCTION
# ==============================================================

def analyze_essay(content):
    """
    Comprehensive essay analysis - runs all checks and returns detailed results
    """
    metrics = calculate_essay_metrics(content)
    vocabulary = analyze_vocabulary(content)
    grammar_issues = check_grammar_issues(content)
    spelling_errors = check_spelling(content)
    readability = analyze_readability(content)
    
    grammar_score = calculate_grammar_score(content, grammar_issues)
    spelling_score = calculate_spelling_score(spelling_errors, metrics['word_count'])
    content_score = calculate_content_score(metrics, vocabulary)
    overall_score = calculate_overall_score(grammar_score, spelling_score, content_score)
    grade = calculate_grade(overall_score)
    
    return {
        'metrics': metrics,
        'vocabulary': vocabulary,
        'grammar_issues': grammar_issues,
        'spelling_errors': spelling_errors,
        'readability': readability,
        'grammar_score': grammar_score,
        'spelling_score': spelling_score,
        'content_score': content_score,
        'overall_score': overall_score,
        'grade': grade,
        'suggestions': generate_suggestions(grammar_issues, spelling_errors, metrics, vocabulary)
    }

def generate_suggestions(grammar_issues, spelling_errors, metrics, vocabulary):
    """Generate improvement suggestions based on analysis"""
    suggestions = []
    
    # Grammar suggestions
    for issue in grammar_issues:
        if issue['severity'] in ['medium', 'high']:
            suggestions.append(issue['suggestion'])
    
    # Spelling suggestions
    if spelling_errors:
        error_count = sum(error['count'] for error in spelling_errors.values())
        if error_count > 3:
            suggestions.append(f"Review {error_count} spelling errors. Consider using spell check or proofreading more carefully.")
    
    # Structure suggestions
    if metrics['paragraph_count'] < 3:
        suggestions.append("Add more paragraphs to improve essay structure. Aim for at least 3-5 paragraphs.")
    
    if metrics['sentence_count'] < 5:
        suggestions.append("Add more sentences to develop your ideas fully.")
    
    # Vocabulary suggestions
    if vocabulary['ttr_percentage'] < 0.4:
        suggestions.append("Use more varied vocabulary. Try replacing repeated words with synonyms.")
    
    # Default suggestions if none generated
    if not suggestions:
        suggestions = [
            "Good overall structure. Continue practicing!",
            "Consider adding more specific examples or evidence.",
            "Proofread for minor errors before final submission."
        ]
    
    return suggestions[:5]  # Return top 5 suggestions

# ==============================================================
# 🏆 LEADERBOARD CALCULATOR (competition-free) - UPDATED
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
            avg_score = essays.aggregate(avg=Avg('overall_score'))['avg'] or 0.0
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