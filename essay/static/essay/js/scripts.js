// Essay Platform - Main JavaScript File

document.addEventListener('DOMContentLoaded', function() {
    console.log('Essay Platform loaded successfully!');
    
    // Initialize all features
    initLikeButtons();
    initCommentForms();
    initDeleteConfirmation();
    initGrammarCheck();
    initCharacterCounter();
    initFormValidation();
});

// ==================== LIKE FUNCTIONALITY ====================
function initLikeButtons() {
    const likeButtons = document.querySelectorAll('.like-button');
    
    likeButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const essayId = this.dataset.essayId;
            const url = `/essay/${essayId}/like/`;
            
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update button appearance
                    if (data.liked) {
                        this.classList.add('liked');
                        this.innerHTML = '<i class="fas fa-heart"></i> ' + data.like_count;
                    } else {
                        this.classList.remove('liked');
                        this.innerHTML = '<i class="far fa-heart"></i> ' + data.like_count;
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });
}

// ==================== COMMENT FORMS ====================
function initCommentForms() {
    const commentForms = document.querySelectorAll('.comment-form');
    
    commentForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const textarea = this.querySelector('textarea');
            if (textarea && textarea.value.trim() === '') {
                e.preventDefault();
                alert('Please enter a comment.');
            }
        });
    });
}

// ==================== DELETE CONFIRMATION ====================
function initDeleteConfirmation() {
    const deleteButtons = document.querySelectorAll('.delete-button, .btn-delete');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
}

// ==================== GRAMMAR CHECK ====================
function initGrammarCheck() {
    const grammarButtons = document.querySelectorAll('.grammar-check-button');
    
    grammarButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const essayId = this.dataset.essayId;
            const content = document.querySelector('#essay-content').value;
            
            if (!content || content.trim().length < 10) {
                alert('Please write at least 10 characters to check grammar.');
                return;
            }
            
            // Show loading state
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Checking...';
            
            fetch('/api/check-grammar/', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: `content=${encodeURIComponent(content)}`
            })
            .then(response => response.json())
            .then(data => {
                displayGrammarResults(data);
                
                // Reset button
                this.disabled = false;
                this.innerHTML = '<i class="fas fa-check-circle"></i> Check Grammar';
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while checking grammar.');
                
                // Reset button
                this.disabled = false;
                this.innerHTML = '<i class="fas fa-check-circle"></i> Check Grammar';
            });
        });
    });
}

function displayGrammarResults(data) {
    const resultsDiv = document.getElementById('grammar-results');
    
    if (!resultsDiv) {
        console.log('Grammar results:', data);
        alert(`Grammar Score: ${data.grammar_score}%\nSpelling Score: ${data.spelling_score}%\nOverall Score: ${data.score}%`);
        return;
    }
    
    let html = '<div class="grammar-results">';
    html += `<h3>Grammar Check Results</h3>`;
    html += `<p><strong>Grammar Score:</strong> ${data.grammar_score}%</p>`;
    html += `<p><strong>Spelling Score:</strong> ${data.spelling_score}%</p>`;
    html += `<p><strong>Overall Score:</strong> ${data.score}%</p>`;
    html += `<p><strong>Grammar Issues:</strong> ${data.grammar_issues}</p>`;
    html += `<p><strong>Spelling Issues:</strong> ${data.spelling_issues}</p>`;
    
    if (data.suggestions && data.suggestions.length > 0) {
        html += '<h4>Suggestions:</h4><ul>';
        data.suggestions.forEach(suggestion => {
            html += `<li>${suggestion.message}</li>`;
        });
        html += '</ul>';
    }
    
    if (data.misspelled_words && data.misspelled_words.length > 0) {
        html += '<h4>Misspelled Words:</h4><ul>';
        data.misspelled_words.forEach(word => {
            html += `<li>${word}</li>`;
        });
        html += '</ul>';
    }
    
    html += '</div>';
    resultsDiv.innerHTML = html;
}

// ==================== CHARACTER COUNTER ====================
function initCharacterCounter() {
    const textareas = document.querySelectorAll('textarea[data-max-length]');
    
    textareas.forEach(textarea => {
        const maxLength = textarea.dataset.maxLength;
        const counterId = textarea.id + '-counter';
        let counter = document.getElementById(counterId);
        
        // Create counter if it doesn't exist
        if (!counter) {
            counter = document.createElement('div');
            counter.id = counterId;
            counter.className = 'character-counter';
            textarea.parentNode.insertBefore(counter, textarea.nextSibling);
        }
        
        // Update counter function
        function updateCounter() {
            const length = textarea.value.length;
            const wordCount = textarea.value.trim().split(/\s+/).filter(w => w.length > 0).length;
            counter.textContent = `${length} characters, ${wordCount} words`;
            
            if (maxLength && length > maxLength) {
                counter.classList.add('error');
            } else {
                counter.classList.remove('error');
            }
        }
        
        // Initial update
        updateCounter();
        
        // Update on input
        textarea.addEventListener('input', updateCounter);
    });
}

// ==================== FORM VALIDATION ====================
function initFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            
            // Check required fields
            const requiredFields = this.querySelectorAll('[required]');
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('error');
                    
                    // Show error message
                    let errorMsg = field.nextElementSibling;
                    if (!errorMsg || !errorMsg.classList.contains('error-message')) {
                        errorMsg = document.createElement('span');
                        errorMsg.className = 'error-message';
                        errorMsg.textContent = 'This field is required.';
                        field.parentNode.insertBefore(errorMsg, field.nextSibling);
                    }
                } else {
                    field.classList.remove('error');
                    const errorMsg = field.nextElementSibling;
                    if (errorMsg && errorMsg.classList.contains('error-message')) {
                        errorMsg.remove();
                    }
                }
            });
            
            // Check password match
            const password = this.querySelector('input[name="password"]');
            const password2 = this.querySelector('input[name="password2"]');
            
            if (password && password2 && password.value !== password2.value) {
                isValid = false;
                password2.classList.add('error');
                alert('Passwords do not match.');
            }
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    });
}

// ==================== UTILITY FUNCTIONS ====================

// Get CSRF token from cookies
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

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Auto-save functionality (if needed)
function setupAutoSave(formSelector, saveUrl) {
    const form = document.querySelector(formSelector);
    if (!form) return;
    
    const inputs = form.querySelectorAll('input, textarea');
    const debouncedSave = debounce(() => {
        const formData = new FormData(form);
        
        fetch(saveUrl, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Saved!', 'success');
            }
        })
        .catch(error => {
            console.error('Auto-save error:', error);
        });
    }, 2000);
    
    inputs.forEach(input => {
        input.addEventListener('input', debouncedSave);
    });
}