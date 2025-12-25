// Secure Paragraph Writing Functionality
document.addEventListener('DOMContentLoaded', function() {
    // Get elements
    const secureInput = document.getElementById('secureInput');
    const hiddenContent = document.getElementById('hiddenContent');
    const submitBtn = document.getElementById('submitBtn');
    const resultSection = document.getElementById('resultSection');
    const submittedText = document.getElementById('submittedText');
    const form = document.getElementById('secureEssayForm');
    
    let typedContent = '';
    let isSubmitted = false;
    
    // Check if elements exist
    if (!secureInput || !form) {
        console.error('Required elements not found');
        return;
    }
    
    // ========== SECURITY FEATURES ==========
    
    // Disable copy, paste, cut on secure input
    secureInput.addEventListener('copy', function(e) {
        e.preventDefault();
        showMessage('Copying is not allowed', 'warning');
        return false;
    });
    
    secureInput.addEventListener('paste', function(e) {
        e.preventDefault();
        showMessage('Pasting is not allowed', 'warning');
        return false;
    });
    
    secureInput.addEventListener('cut', function(e) {
        e.preventDefault();
        showMessage('Cutting is not allowed', 'warning');
        return false;
    });
    
    // Additional security: Prevent context menu
    secureInput.addEventListener('contextmenu', function(e) {
        e.preventDefault();
        return false;
    });
    
    // Prevent drag and drop
    secureInput.addEventListener('dragstart', function(e) {
        e.preventDefault();
        return false;
    });
    
    secureInput.addEventListener('drop', function(e) {
        e.preventDefault();
        showMessage('Drag and drop is not allowed', 'warning');
        return false;
    });
    
    // ========== TYPING LOGIC ==========
    
    // Capture typed content without displaying it
    secureInput.addEventListener('input', function(e) {
        if (isSubmitted) return;
        
        // Get the current value (more reliable than e.data)
        const currentValue = secureInput.value;
        
        if (currentValue.length > 0) {
            // Add the last character typed
            const lastChar = currentValue.charAt(currentValue.length - 1);
            typedContent += lastChar;
            
            // Update hidden field
            hiddenContent.value = typedContent;
            
            // Immediately clear the visible input field
            secureInput.value = '';
            
            // Enable submit if we have content
            if (typedContent.length > 0) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Save Paragraph (' + typedContent.length + ' chars)';
            }
        }
    });
    
    // Handle keyboard events
    secureInput.addEventListener('keydown', function(e) {
        if (isSubmitted) {
            e.preventDefault();
            return;
        }
        
        // Handle Backspace
        if (e.key === 'Backspace') {
            e.preventDefault(); // Prevent browser back navigation
            if (typedContent.length > 0) {
                // Remove last character
                typedContent = typedContent.slice(0, -1);
                hiddenContent.value = typedContent;
                
                // Update button text
                if (typedContent.length === 0) {
                    submitBtn.disabled = true;
                    submitBtn.textContent = 'Save Paragraph';
                } else {
                    submitBtn.textContent = 'Save Paragraph (' + typedContent.length + ' chars)';
                }
            }
        }
        
        // Handle Enter key to lock input
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (typedContent.length > 0 && !isSubmitted) {
                lockInput();
                showSubmittedText();
                showMessage('Input locked. Press Submit to save.', 'info');
            } else if (typedContent.length === 0) {
                showMessage('Please type something first', 'warning');
            }
        }
        
        // Handle Tab key - allow it for accessibility
        if (e.key === 'Tab') {
            // Allow default tab behavior
            return;
        }
    });
    
    // ========== FORM SUBMISSION ==========
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (typedContent.length === 0) {
            showMessage('Please type some content first', 'warning');
            return false;
        }
        
        if (!isSubmitted) {
            showMessage('Please press Enter first to lock your input', 'warning');
            return false;
        }
        
        // Show loading state
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
        submitBtn.disabled = true;
        
        // Submit form via AJAX
        const formData = new FormData(form);
        
        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage('Paragraph saved successfully!', 'success');
                submitBtn.disabled = true;
                submitBtn.textContent = 'Saved ✓';
            } else {
                showMessage('Error: ' + data.message, 'error');
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('Network error. Please try again.', 'error');
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        });
    });
    
    // ========== HELPER FUNCTIONS ==========
    
    function lockInput() {
        isSubmitted = true;
        secureInput.disabled = true;
        secureInput.style.backgroundColor = '#e9ecef';
        secureInput.style.cursor = 'not-allowed';
        secureInput.placeholder = 'Input locked - Press Submit to save';
    }
    
    function showSubmittedText() {
        if (!submittedText || !resultSection) return;
        
        submittedText.textContent = typedContent;
        resultSection.style.display = 'block';
        
        // Add character count
        const charCount = document.createElement('small');
        charCount.className = 'text-muted d-block mt-1';
        charCount.textContent = typedContent.length + ' characters';
        
        // Remove existing count if present
        const existingCount = submittedText.nextElementSibling;
        if (existingCount && existingCount.className.includes('text-muted')) {
            existingCount.remove();
        }
        
        submittedText.parentNode.appendChild(charCount);
        
        // Scroll to result smoothly
        setTimeout(() => {
            resultSection.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'nearest' 
            });
        }, 100);
    }
    
    // Copy to clipboard function
    window.copyToClipboard = function() {
        if (!typedContent) {
            showMessage('No content to copy', 'warning');
            return;
        }
        
        navigator.clipboard.writeText(typedContent).then(function() {
            showMessage('Text copied to clipboard!', 'success');
        }).catch(function(err) {
            console.error('Could not copy text: ', err);
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = typedContent;
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                showMessage('Text copied to clipboard!', 'success');
            } catch (err) {
                showMessage('Failed to copy text. Please select and copy manually.', 'error');
            }
            document.body.removeChild(textArea);
        });
    };
    
    // Show message function
    function showMessage(message, type = 'info') {
        // Remove existing messages
        const existingMsg = document.querySelector('.alert-message');
        if (existingMsg) {
            existingMsg.remove();
        }
        
        // Create message element
        const msgDiv = document.createElement('div');
        msgDiv.className = 'alert alert-' + (type === 'error' ? 'danger' : type) + ' alert-message mt-2';
        msgDiv.style.position = 'fixed';
        msgDiv.style.top = '20px';
        msgDiv.style.right = '20px';
        msgDiv.style.zIndex = '9999';
        msgDiv.style.minWidth = '300px';
        msgDiv.textContent = message;
        
        // Add to page
        document.body.appendChild(msgDiv);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            if (msgDiv.parentNode) {
                msgDiv.remove();
            }
        }, 3000);
    }
    
    // ========== INITIALIZATION ==========
    
    console.log('Secure paragraph editor loaded successfully');
});