// ===== WRITEVERSE CHALLENGES JAVASCRIPT =====

document.addEventListener('DOMContentLoaded', function() {
    
    // ===== TAB SWITCHING =====
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            
            // Remove active class from all tabs
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked tab
            this.classList.add('active');
            document.getElementById(`${tabName}-tab`).classList.add('active');
        });
    });
    
    // ===== AI WRITING ASSISTANT =====
    const aiTextInput = document.getElementById('ai-text-input');
    const aiSuggestionType = document.getElementById('ai-suggestion-type');
    const aiGetSuggestionBtn = document.getElementById('ai-get-suggestion-btn');
    const aiOutput = document.getElementById('ai-output');
    const aiOutputContent = document.getElementById('ai-output-content');
    const aiLoading = document.getElementById('ai-loading');
    const aiCopyBtn = document.getElementById('ai-copy-btn');
    const aiAcceptBtn = document.getElementById('ai-accept-btn');
    const aiRejectBtn = document.getElementById('ai-reject-btn');
    
    let currentSessionId = null;
    
    if (aiGetSuggestionBtn) {
        aiGetSuggestionBtn.addEventListener('click', async function() {
            const text = aiTextInput.value.trim();
            const type = aiSuggestionType.value;
            
            if (!text) {
                alert('Please enter some text to get suggestions');
                return;
            }
            
            // Show loading
            aiLoading.style.display = 'block';
            aiOutput.style.display = 'none';
            aiGetSuggestionBtn.disabled = true;
            
            try {
                const response = await fetch('/ai/assist/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        text: text,
                        type: type
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Hide loading, show output
                    aiLoading.style.display = 'none';
                    aiOutput.style.display = 'block';
                    aiOutputContent.textContent = data.suggestion;
                    currentSessionId = data.session_id;
                    
                    // Add animation
                    aiOutput.style.animation = 'fadeIn 0.4s ease';
                }
            } catch (error) {
                console.error('AI Error:', error);
                alert('Failed to get AI suggestion. Please try again.');
            } finally {
                aiLoading.style.display = 'none';
                aiGetSuggestionBtn.disabled = false;
            }
        });
    }
    
    // Copy AI suggestion
    if (aiCopyBtn) {
        aiCopyBtn.addEventListener('click', function() {
            const text = aiOutputContent.textContent;
            navigator.clipboard.writeText(text).then(() => {
                const originalHtml = aiCopyBtn.innerHTML;
                aiCopyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                setTimeout(() => {
                    aiCopyBtn.innerHTML = originalHtml;
                }, 2000);
            });
        });
    }
    
    // Accept AI suggestion
    if (aiAcceptBtn) {
        aiAcceptBtn.addEventListener('click', async function() {
            if (!currentSessionId) return;
            
            try {
                const response = await fetch('/ai/accept/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        session_id: currentSessionId
                    })
                });
                
                if (response.ok) {
                    // Replace original text with suggestion
                    aiTextInput.value = aiOutputContent.textContent;
                    aiOutput.style.display = 'none';
                    
                    // Show success message
                    showToast('Suggestion applied successfully!', 'success');
                }
            } catch (error) {
                console.error('Accept Error:', error);
            }
        });
    }
    
    // Reject AI suggestion
    if (aiRejectBtn) {
        aiRejectBtn.addEventListener('click', function() {
            aiOutput.style.display = 'none';
            currentSessionId = null;
        });
    }
    
    // ===== HELPER FUNCTIONS =====
    
    // Get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Show toast notification
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        `;
        
        // Add to body
        document.body.appendChild(toast);
        
        // Show toast
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Hide and remove toast
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    // Add toast styles if not exists
    if (!document.querySelector('#toast-styles')) {
        const style = document.createElement('style');
        style.id = 'toast-styles';
        style.textContent = `
            .toast {
                position: fixed;
                bottom: 2rem;
                right: 2rem;
                background: white;
                padding: 1rem 1.5rem;
                border-radius: 0.75rem;
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2);
                display: flex;
                align-items: center;
                gap: 0.75rem;
                opacity: 0;
                transform: translateY(1rem);
                transition: all 0.3s ease;
                z-index: 9999;
                border-left: 4px solid #2563eb;
            }
            
            .toast.show {
                opacity: 1;
                transform: translateY(0);
            }
            
            .toast-success {
                border-left-color: #10b981;
            }
            
            .toast-success i {
                color: #10b981;
            }
            
            .toast-error {
                border-left-color: #ef4444;
            }
            
            .toast-error i {
                color: #ef4444;
            }
            
            .toast i {
                font-size: 1.25rem;
                color: #2563eb;
            }
            
            .toast span {
                font-weight: 600;
                color: #0f172a;
            }
        `;
        document.head.appendChild(style);
    }
    
    console.log('✅ Challenges page initialized');
});