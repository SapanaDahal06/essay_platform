// Secure Paragraph Writing Functionality
document.addEventListener('DOMContentLoaded', function() {
    const secureInput = document.getElementById('secureInput');
    const hiddenContent = document.getElementById('hiddenContent');
    const submitBtn = document.getElementById('submitBtn');
    const resultSection = document.getElementById('resultSection');
    const submittedText = document.getElementById('submittedText');
    const form = document.getElementById('secureEssayForm');
    
    let typedContent = '';
    
    // Disable copy, paste, cut on secure input
    secureInput.addEventListener('copy', function(e) {
        e.preventDefault();
        alert('Copying is not allowed');
        return false;
    });
    
    secureInput.addEventListener('paste', function(e) {
        e.preventDefault();
        alert('Pasting is not allowed');
        return false;
    });
    
    secureInput.addEventListener('cut', function(e) {
        e.preventDefault();
        alert('Cutting is not allowed');
        return false;
    });
    
    // Capture typed content without displaying it
    secureInput.addEventListener('input', function(e) {
        const inputChar = e.data;
        
        // Only add if it's a single character (not backspace, etc.)
        if (inputChar && inputChar.length === 1) {
            typedContent += inputChar;
        }
        
        // Update hidden field
        hiddenContent.value = typedContent;
        
        // Clear the visible input field but keep cursor position
        setTimeout(() => {
            secureInput.value = '';
        }, 0);
        
        // Enable submit if we have content
        if (typedContent.length > 0) {
            submitBtn.disabled = false;
        }
    });
    
    // Handle backspace
    secureInput.addEventListener('keydown', function(e) {
        if (e.key === 'Backspace') {
            // Remove last character
            typedContent = typedContent.slice(0, -1);
            hiddenContent.value = typedContent;
            
            if (typedContent.length === 0) {
                submitBtn.disabled = true;
            }
        }
        
        // Handle Enter key to submit
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (typedContent.length > 0) {
                // Make input non-editable
                secureInput.disabled = true;
                secureInput.style.backgroundColor = '#e9ecef';
                
                // Show result
                showSubmittedText();
            }
        }
    });
    
    // Form submission
    form.addEventListener('submit', function(e) {
        if (typedContent.length === 0) {
            e.preventDefault();
            alert('Please type some content first');
            return false;
        }
        
        // Optional: Add loading state
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
        submitBtn.disabled = true;
    });
    
    // Show submitted text
    function showSubmittedText() {
        submittedText.textContent = typedContent;
        resultSection.style.display = 'block';
        
        // Scroll to result
        resultSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Copy to clipboard function
    window.copyToClipboard = function() {
        navigator.clipboard.writeText(typedContent).then(function() {
            alert('Text copied to clipboard!');
        }).catch(function(err) {
            console.error('Could not copy text: ', err);
            alert('Failed to copy text. Please select and copy manually.');
        });
    };
    
    // Additional security: Prevent context menu on secure input
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
        alert('Drag and drop is not allowed');
        return false;
    });
});