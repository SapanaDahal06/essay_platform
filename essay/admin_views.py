# essay/admin_views.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Avg, Count
from .models import Essay, GrammarCheck, User

# Check if user is admin/staff
def is_staff_user(user):
    return user.is_staff or user.is_superuser

# Define grammar status choices
GRAMMAR_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('checked', 'Checked'),
    ('needs_review', 'Needs Review'),
    ('auto_approved', 'Auto Approved'),
]

@login_required
@user_passes_test(is_staff_user)
def grammar_check_queue(request):
    """List essays needing grammar check"""
    # Essays requested by users for grammar check
    requested_essays = Essay.objects.filter(
        requires_grammar_check=True,
        grammar_status='pending'
    ).order_by('-created_at')
    
    # Essays with needs_review status
    needs_review_essays = Essay.objects.filter(
        grammar_status='needs_review'
    ).order_by('-created_at')
    
    # Essays that have been checked
    checked_essays = Essay.objects.filter(
        grammar_status='checked'
    ).order_by('-grammar_checked_at')[:10]
    
    context = {
        'requested_essays': requested_essays,
        'needs_review_essays': needs_review_essays,
        'checked_essays': checked_essays,
        'total_pending': requested_essays.count() + needs_review_essays.count()
    }
    
    return render(request, 'essay/admin/grammar_queue.html', context)

@login_required
@user_passes_test(is_staff_user)
def grammar_check_detail(request, essay_id):
    """Detail view for grammar checking"""
    essay = get_object_or_404(Essay, id=essay_id)
    
    # Get previous grammar checks
    previous_checks = GrammarCheck.objects.filter(essay=essay).order_by('-checked_at')
    
    if request.method == 'POST':
        try:
            score = float(request.POST.get('score', 0))
            notes = request.POST.get('notes', '')
            suggestions = request.POST.get('suggestions', '')
            status = request.POST.get('status', 'checked')
            
            # Validate score
            if score < 0 or score > 100:
                messages.error(request, "Score must be between 0 and 100")
                return redirect('grammar_check_detail', essay_id=essay_id)
            
            # Count issues from suggestions
            issues_count = len([line for line in suggestions.split('\n') if line.strip()])
            
            # Create grammar check record
            GrammarCheck.objects.create(
                essay=essay,
                checked_by=request.user,
                score=score,
                suggestions=suggestions,
                issues_data={'notes': notes, 'suggestions': suggestions},
                issues_found=issues_count,
                automated_check=False
            )
            
            # Update essay
            essay.grammar_score = score
            essay.grammar_status = status
            essay.grammar_checked_by = request.user
            essay.grammar_checked_at = timezone.now()
            essay.grammar_notes = notes
            essay.save()
            
            messages.success(request, f"Grammar check completed for '{essay.title}'")
            return redirect('grammar_check_queue')
            
        except ValueError:
            messages.error(request, "Invalid score value")
    
    context = {
        'essay': essay,
        'previous_checks': previous_checks,
        'grammar_status_choices': GRAMMAR_STATUS_CHOICES
    }
    
    return render(request, 'essay/admin/grammar_check_detail.html', context)

@login_required
@user_passes_test(is_staff_user)
def bulk_grammar_action(request):
    """Bulk actions for grammar checking"""
    if request.method == 'POST':
        action = request.POST.get('action')
        essay_ids = request.POST.getlist('essay_ids')
        
        if not essay_ids:
            messages.warning(request, "No essays selected")
            return redirect('grammar_check_queue')
        
        essays = Essay.objects.filter(id__in=essay_ids)
        
        if action == 'mark_checked':
            updated_count = 0
            for essay in essays:
                essay.grammar_status = 'checked'
                essay.grammar_checked_by = request.user
                essay.grammar_checked_at = timezone.now()
                essay.save()
                updated_count += 1
            
            messages.success(request, f"Marked {updated_count} essays as checked")
        
        elif action == 'mark_needs_review':
            updated_count = essays.update(grammar_status='needs_review')
            messages.success(request, f"Flagged {updated_count} essays for review")
        
        elif action == 'mark_pending':
            updated_count = essays.update(grammar_status='pending')
            messages.success(request, f"Moved {updated_count} essays to pending")
        
        else:
            messages.error(request, "Invalid action selected")
    
    return redirect('grammar_check_queue')

@login_required
@user_passes_test(is_staff_user)
def grammar_stats(request):
    """Show grammar checking statistics"""
    total_essays = Essay.objects.count()
    checked_essays = Essay.objects.filter(grammar_status='checked').count()
    pending_essays = Essay.objects.filter(grammar_status='pending').count()
    needs_review_essays = Essay.objects.filter(grammar_status='needs_review').count()
    
    # Average grammar score
    avg_result = Essay.objects.filter(grammar_score__isnull=False).aggregate(
        avg_score=Avg('grammar_score')
    )
    avg_score = avg_result['avg_score'] or 0
    
    # Recent grammar checks
    recent_checks = GrammarCheck.objects.select_related('essay', 'checked_by').order_by('-checked_at')[:10]
    
    # Top users by grammar score
    top_users = User.objects.annotate(
        avg_grammar_score=Avg('essays__grammar_score'),
        essay_count=Count('essays')
    ).filter(
        avg_grammar_score__isnull=False,
        essay_count__gt=0
    ).order_by('-avg_grammar_score')[:10]
    
    context = {
        'total_essays': total_essays,
        'checked_essays': checked_essays,
        'pending_essays': pending_essays,
        'needs_review_essays': needs_review_essays,
        'avg_score': round(avg_score, 2),
        'recent_checks': recent_checks,
        'top_users': top_users,
        'completion_rate': round((checked_essays / total_essays * 100), 2) if total_essays > 0 else 0
    }
    
    return render(request, 'essay/admin/grammar_stats.html', context)