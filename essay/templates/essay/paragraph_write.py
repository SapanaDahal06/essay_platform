# essay/paragraph_writer.py
import json
import re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Essay, Paragraph

class ParagraphWriter:
    """Handles paragraph-by-paragraph writing with locking"""
    
    @staticmethod
    @csrf_exempt
    @login_required
    def save_paragraph(request):
        """Save a single paragraph"""
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                essay_id = data.get('essay_id')
                content = data.get('content', '')
                paragraph_num = data.get('paragraph_num', 1)
                
                essay = Essay.objects.get(id=essay_id, author=request.user)
                
                # Create or update paragraph
                paragraph, created = Paragraph.objects.get_or_create(
                    essay=essay,
                    paragraph_number=paragraph_num,
                    defaults={'content': content}
                )
                
                if not created:
                    paragraph.content = content
                    paragraph.save()
                
                # Update word count
                paragraph.word_count = len(content.split())
                paragraph.save()
                
                return JsonResponse({
                    'success': True,
                    'paragraph_id': str(paragraph.id),
                    'word_count': paragraph.word_count
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
        
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)
    
    @staticmethod
    @csrf_exempt
    @login_required  
    def lock_paragraph(request):
        """Lock a paragraph"""
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                essay_id = data.get('essay_id')
                paragraph_num = data.get('paragraph_num')
                
                essay = Essay.objects.get(id=essay_id, author=request.user)
                paragraph = Paragraph.objects.get(
                    essay=essay,
                    paragraph_number=paragraph_num
                )
                
                paragraph.is_locked = True
                paragraph.locked_by = request.user
                paragraph.save()
                
                return JsonResponse({'success': True})
                
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=400)
        
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)
    
    @staticmethod
    @csrf_exempt
    @login_required
    def unlock_paragraph(request):
        """Unlock a paragraph"""
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                essay_id = data.get('essay_id')
                paragraph_num = data.get('paragraph_num')
                
                essay = Essay.objects.get(id=essay_id, author=request.user)
                paragraph = Paragraph.objects.get(
                    essay=essay,
                    paragraph_number=paragraph_num
                )
                
                paragraph.is_locked = False
                paragraph.locked_by = None
                paragraph.save()
                
                return JsonResponse({'success': True})
                
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=400)
        
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)
    
    @staticmethod
    def check_grammar(text, language='en-US'):
        """Check grammar for text"""
        if not text:
            return []
        
        issues = []
        
        # Basic grammar checks
        if language.startswith('en'):
            # English checks
            if re.search(r'\bi\s+', text):
                issues.append({
                    'type': 'Capitalization',
                    'message': "Use capital 'I' when referring to yourself",
                    'suggestion': 'Change "i" to "I"'
                })
            
            if 'alot' in text.lower():
                issues.append({
                    'type': 'Spelling',
                    'message': '"alot" should be "a lot"',
                    'suggestion': 'Change "alot" to "a lot"'
                })
            
            # Check sentence capitalization
            sentences = re.split(r'[.!?]+', text)
            for i, sentence in enumerate(sentences):
                sentence = sentence.strip()
                if sentence and sentence[0].isalpha() and not sentence[0].isupper():
                    issues.append({
                        'type': 'Capitalization',
                        'message': f'Sentence should start with capital letter',
                        'suggestion': f'Change "{sentence[0]}" to "{sentence[0].upper()}"'
                    })
            
            # Check for common mistakes
            common_mistakes = [
                (r'\byour\b.*\byou\'re\b', "your/you're confusion"),
                (r'\bthere\b.*\btheir\b', "there/their confusion"),
                (r'\bits\b.*\bit\'s\b', "its/it's confusion"),
            ]
            
            for pattern, message in common_mistakes:
                if re.search(pattern, text, re.IGNORECASE):
                    issues.append({
                        'type': 'Common Mistake',
                        'message': message,
                        'suggestion': 'Review usage'
                    })
        
        elif language == 'ne':
            # Nepali checks (basic)
            issues.append({
                'type': 'नेपाली व्याकरण',
                'message': 'नेपाली भाषाको व्याकरण जाँच',
                'suggestion': 'भाषा सही प्रयोग गर्नुहोस्'
            })
        
        # Check for very long sentences
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            words = sentence.split()
            if len(words) > 30:
                issues.append({
                    'type': 'Style',
                    'message': 'Sentence is very long',
                    'suggestion': 'Break into shorter sentences'
                })
        
        return issues