# essay/admin_views.py (Simplified version without grammar_checker import)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import re
from .models import Essay

def staff_required(view_func):
    """Decorator for views that require staff permission"""
    decorated_view_func = user_passes_test(
        lambda u: u.is_staff,
        login_url='/admin/login/'
    )(view_func)
    return decorated_view_func

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

@staff_required
def bulk_grammar_check(request):
    """Bulk grammar check view for staff"""
    if request.method == 'POST':
        essay_ids = request.POST.getlist('essay_ids')
        essays = Essay.objects.filter(id__in=essay_ids)
        
        count = 0
        
        for essay in essays:
            result = simple_grammar_check(essay.content)
            if result:
                essay.grammar_errors_json = {'errors': result.get('grammar_errors', [])}
                essay.spelling_errors_json = {'errors': result.get('spelling_errors', [])}
                essay.grammar_score = result.get('overall_score', 0)
                essay.grammar_status = 'checked'
                essay.save()
                count += 1
        
        messages.success(request, f"Grammar check completed for {count} essays.")
        return redirect('grammar_check_queue')
    
    # GET request - show form
    essays = Essay.objects.filter(grammar_status='pending')[:50]
    return render(request, 'admin/bulk_grammar_check.html', {
        'essays': essays,
        'title': 'Bulk Grammar Check'
    })

@staff_required
def grammar_check_queue(request):
    """Show queue of essays needing grammar check"""
    pending_essays = Essay.objects.filter(grammar_status='pending').order_by('-created_at')[:100]
    checked_essays = Essay.objects.filter(grammar_status='checked').order_by('-grammar_checked_at')[:50]
    
    return render(request, 'admin/grammar_check_queue.html', {
        'pending_essays': pending_essays,
        'checked_essays': checked_essays,
        'title': 'Grammar Check Queue'
    })

@staff_required
def grammar_check_detail(request, essay_id):
    """Detailed grammar check view for single essay"""
    essay = get_object_or_404(Essay, id=essay_id)
    
    if request.method == 'POST':
        # Process manual grammar check
        grammar_score = request.POST.get('grammar_score')
        grammar_notes = request.POST.get('grammar_notes')
        
        if grammar_score:
            essay.grammar_score = grammar_score
            essay.grammar_notes = grammar_notes
            essay.grammar_status = 'checked'
            essay.grammar_checked_by = request.user
            essay.save()
            
            messages.success(request, f"Grammar check saved for '{essay.title}'.")
            return redirect('grammar_check_queue')
    
    return render(request, 'admin/grammar_check_detail.html', {
        'essay': essay,
        'title': f'Grammar Check - {essay.title}'
    })

@require_POST
@staff_required
def bulk_grammar_action(request):
    """Handle bulk actions for grammar checking"""
    action = request.POST.get('action')
    essay_ids = request.POST.getlist('essay_ids')
    
    if not essay_ids:
        messages.error(request, "No essays selected.")
        return redirect('grammar_check_queue')
    
    essays = Essay.objects.filter(id__in=essay_ids)
    
    if action == 'mark_checked':
        essays.update(
            grammar_status='checked',
            grammar_checked_by=request.user
        )
        messages.success(request, f"Marked {essays.count()} essays as checked.")
    
    elif action == 'mark_pending':
        essays.update(grammar_status='pending')
        messages.success(request, f"Marked {essays.count()} essays as pending.")
    
    elif action == 'run_auto_check':
        count = 0
        
        for essay in essays:
            result = simple_grammar_check(essay.content)
            if result:
                essay.grammar_score = result.get('overall_score', 0)
                essay.grammar_status = 'checked'
                essay.save()
                count += 1
        
        messages.success(request, f"Auto grammar check completed for {count} essays.")
    
    return redirect('grammar_check_queue')

@staff_required
def grammar_stats(request):
    """Show grammar checking statistics"""
    from django.db.models import Count, Avg
    
    stats = {
        'total_essays': Essay.objects.count(),
        'pending_checks': Essay.objects.filter(grammar_status='pending').count(),
        'checked_essays': Essay.objects.filter(grammar_status='checked').count(),
        'avg_grammar_score': Essay.objects.filter(grammar_score__isnull=False).aggregate(
            avg=Avg('grammar_score')
        )['avg'] or 0,
        'top_essays': Essay.objects.filter(grammar_score__isnull=False)
                        .order_by('-grammar_score')[:10],
        'worst_essays': Essay.objects.filter(grammar_score__isnull=False)
                         .order_by('grammar_score')[:10],
    }
    
    return render(request, 'admin/grammar_stats.html', {
        'stats': stats,
        'title': 'Grammar Check Statistics'
    })