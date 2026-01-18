# essay/signals.py - SIMPLIFIED VERSION
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import re
from .models import Essay, Notification, UserProfile, User

@receiver(post_save, sender=Essay)
def auto_grammar_check_on_submission(sender, instance, created, **kwargs):
    """Automatically check grammar when essay is submitted"""
    if instance.status == 'submitted' and instance.grammar_status == 'pending':
        # Perform simple grammar check inline
        result = simple_grammar_check(instance.content)
        
        if result:
            instance.grammar_errors_json = {'errors': result.get('grammar_errors', [])}
            instance.spelling_errors_json = {'errors': result.get('spelling_errors', [])}
            instance.grammar_score = result.get('overall_score', 0)
            instance.readability_score = result.get('readability_score', 0)
            instance.overall_quality_score = result.get('overall_score', 0)
            instance.ranking_score = result.get('overall_score', 0)
            instance.grammar_status = 'checked'
            instance.grammar_notes = f"Auto-checked on submission. Score: {result.get('overall_score', 0):.1f}/100"
            instance.grammar_checked_at = timezone.now()
            
            # Generate highlighted content
            instance.highlighted_content = generate_highlighted_content(instance)
            
            # Save all fields
            instance.save()
            
            # Create notification for user
            Notification.objects.create(
                user=instance.author,
                notification_type='system',
                title='Grammar Check Complete',
                message=f'Your essay "{instance.title}" has been automatically checked for grammar. Score: {result.get("overall_score", 0):.1f}/100',
                is_actionable=True
            )

def simple_grammar_check(content):
    """Simple inline grammar checker"""
    if not content:
        return None
    
    # Common grammar mistakes
    common_errors = {
        'their': ["they're", "there"],
        'your': ["you're"],
        'its': ["it's"],
        'then': ["than"],
        'affect': ["effect"],
        'accept': ["except"],
        'complement': ["compliment"]
    }
    
    # Common misspellings
    common_misspellings = {
        'recieve': ['receive'],
        'seperate': ['separate'],
        'occured': ['occurred'],
        'definately': ['definitely'],
        'wierd': ['weird'],
        'grammer': ['grammar'],
        'arguement': ['argument'],
        'maintainance': ['maintenance'],
        'neccessary': ['necessary'],
        'occassion': ['occasion']
    }
    
    grammar_errors = []
    spelling_errors = []
    
    # Split into sentences
    sentences = content.split('. ')
    for i, sentence in enumerate(sentences):
        if not sentence.strip():
            continue
            
        words = sentence.split()
        
        # Check grammar errors
        for j, word in enumerate(words):
            cleaned_word = ''.join(c for c in word if c.isalpha()).lower()
            if cleaned_word in common_errors:
                grammar_errors.append({
                    'sentence': i + 1,
                    'word': word,
                    'suggestions': common_errors[cleaned_word],
                    'suggestion': f"Consider: {common_errors[cleaned_word][0]}"
                })
        
        # Check sentence fragments
        if len(words) < 3:
            grammar_errors.append({
                'sentence': i + 1,
                'issue': 'Possible sentence fragment',
                'suggestion': 'Consider expanding this thought'
            })
    
    # Check spelling errors
    words = content.split()
    for i, word in enumerate(words):
        cleaned_word = ''.join(c for c in word if c.isalpha()).lower()
        if cleaned_word in common_misspellings:
            spelling_errors.append({
                'position': i,
                'word': word,
                'suggestions': common_misspellings[cleaned_word]
            })
    
    # Calculate readability (simplified)
    sentences_count = len([s for s in content.split('.') if s.strip()])
    words_count = len(words)
    readability = 70  # Default
    
    if sentences_count > 0 and words_count > 0:
        words_per_sentence = words_count / sentences_count
        if 15 <= words_per_sentence <= 25:
            readability = 85
        elif words_per_sentence < 10:
            readability = 60
        elif words_per_sentence > 30:
            readability = 55
    
    # Calculate overall score
    total_errors = len(grammar_errors) + len(spelling_errors)
    if words_count > 0:
        error_density = total_errors / words_count * 100
        base_score = max(0, 100 - (error_density * 10))
    else:
        base_score = 0
    
    overall_score = (base_score * 0.7) + (readability * 0.3)
    
    return {
        'grammar_errors': grammar_errors,
        'spelling_errors': spelling_errors,
        'readability_score': readability,
        'overall_score': min(100, overall_score)
    }

def generate_highlighted_content(essay):
    """Generate HTML with highlighted errors"""
    if not essay.content:
        return ""
    
    content = essay.content
    
    # Grammar errors from JSON
    if essay.grammar_errors_json and 'errors' in essay.grammar_errors_json:
        for error in essay.grammar_errors_json['errors']:
            word = error.get('word', '')
            suggestion = error.get('suggestion', '')
            if word and suggestion:
                highlighted = f'<span class="grammar-error" title="Grammar: {suggestion}">{word}</span>'
                content = content.replace(word, highlighted, 1)
    
    # Spelling errors from JSON
    if essay.spelling_errors_json and 'errors' in essay.spelling_errors_json:
        for error in essay.spelling_errors_json['errors']:
            word = error.get('word', '')
            suggestions = error.get('suggestions', [])
            if word and suggestions:
                suggestion_text = "Suggestions: " + ", ".join(suggestions[:3])
                highlighted = f'<span class="spelling-error" title="{suggestion_text}">{word}</span>'
                content = content.replace(word, highlighted, 1)
    
    return content

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when a new User is created"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=Essay)
def update_user_streak(sender, instance, created, **kwargs):
    """Update user's streak when they create/update an essay"""
    if created and instance.author:
        try:
            profile = instance.author.profile
            profile.update_streak()
        except UserProfile.DoesNotExist:
            # Create profile if it doesn't exist
            UserProfile.objects.create(user=instance.author)
            instance.author.profile.update_streak()
            # In essay/signals.py (create if not exists)
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Essay, UserScore

@receiver(post_save, sender=Essay)
def update_user_score_on_essay_save(sender, instance, **kwargs):
    """Update UserScore when an essay is saved"""
    if instance.author and instance.is_reviewed:
        user_score, created = UserScore.objects.get_or_create(user=instance.author)
        user_score.update_from_essays()