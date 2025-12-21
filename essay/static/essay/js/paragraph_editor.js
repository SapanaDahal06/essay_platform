// Create this file
document.addEventListener('DOMContentLoaded', function() {
    let currentParagraph = 0;
    const totalParagraphs = 5;
    let editMode = false;
    
    // Initialize TinyMCE editors
    tinymce.init({
        selector: '.paragraph-content',
        height: 300,
        menubar: false,
        plugins: 'autoresize lists link image table help wordcount',
        toolbar: 'undo redo | blocks | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | removeformat | help',
        content_style: 'body { font-family:Helvetica,Arial,sans-serif; font-size:14px }',
        setup: function(editor) {
            editor.on('change', function() {
                checkGrammar(editor.id.replace('editor-', ''));
            });
        }
    });
    
    // Grammar check function
    function checkGrammar(paragraphIndex) {
        const editor = tinymce.get(`editor-${paragraphIndex}`);
        if (!editor) return;
        
        const content = editor.getContent({format: 'text'});
        
        // Call your Django backend for grammar check
        fetch('/essay/check-grammar/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                text: content,
                paragraph_index: paragraphIndex
            })
        })
        .then(response => response.json())
        .then(data => {
            displayGrammarIssues(paragraphIndex, data.issues);
        });
    }
    
    // Display grammar issues
    function displayGrammarIssues(paraIndex, issues) {
        const container = document.getElementById(`grammar-${paraIndex}`);
        container.innerHTML = '';
        
        if (issues && issues.length > 0) {
            container.innerHTML = `<div class="alert alert-warning p-2">
                <small><strong>Grammar Suggestions:</strong> ${issues.length} issue(s) found</small>
                <ul class="mb-0">
                    ${issues.map(issue => `<li>${issue.message}</li>`).join('')}
                </ul>
            </div>`;
        }
    }
    
    // Paragraph navigation
    document.getElementById('next-btn').addEventListener('click', function() {
        if (currentParagraph < totalParagraphs - 1) {
            // Save current paragraph
            saveParagraph(currentParagraph);
            
            // Lock current paragraph
            lockParagraph(currentParagraph);
            
            // Move to next
            currentParagraph++;
            updateUI();
        }
    });
    
    document.getElementById('prev-btn').addEventListener('click', function() {
        if (currentParagraph > 0) {
            currentParagraph--;
            updateUI();
        }
    });
    
    // Lock paragraph function
    function lockParagraph(index) {
        const editor = tinymce.get(`editor-${index}`);
        if (editor) {
            editor.setMode('readonly');
        }
        
        const card = document.querySelector(`[data-index="${index}"]`);
        if (card) {
            const lockBadge = card.querySelector('.lock-indicator');
            lockBadge.textContent = 'Locked';
            lockBadge.className = 'lock-indicator badge bg-success';
        }
    }
    
    // Unlock paragraph (for edit mode)
    function unlockParagraph(index) {
        const editor = tinymce.get(`editor-${index}`);
        if (editor) {
            editor.setMode('design');
        }
        
        const card = document.querySelector(`[data-index="${index}"]`);
        if (card) {
            const lockBadge = card.querySelector('.lock-indicator');
            lockBadge.textContent = 'Editable';
            lockBadge.className = 'lock-indicator badge bg-warning';
        }
    }
    
    // Save paragraph to backend
    function saveParagraph(index) {
        const editor = tinymce.get(`editor-${index}`);
        if (!editor) return;
        
        const content = editor.getContent();
        
        fetch('/essay/save-paragraph/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                essay_id: {{ essay.id }},
                content: content,
                paragraph_index: index
            })
        });
    }
    
    // Update UI state
    function updateUI() {
        // Update current paragraph indicator
        document.getElementById('current-para').textContent = currentParagraph + 1;
        
        // Update progress bar
        const progress = ((currentParagraph + 1) / totalParagraphs) * 100;
        document.getElementById('progress-bar').style.width = `${progress}%`;
        
        // Enable/disable navigation buttons
        document.getElementById('prev-btn').disabled = currentParagraph === 0;
        document.getElementById('next-btn').disabled = currentParagraph === totalParagraphs - 1;
        
        // Enable/disable editors based on edit mode
        for (let i = 0; i < totalParagraphs; i++) {
            if (editMode) {
                unlockParagraph(i);
            } else {
                if (i > currentParagraph) {
                    // Disable future paragraphs
                    const editor = tinymce.get(`editor-${i}`);
                    if (editor) editor.setMode('readonly');
                } else if (i < currentParagraph) {
                    // Keep past paragraphs locked (unless edit mode)
                    if (!editMode) lockParagraph(i);
                }
            }
        }
    }
    
    // Action buttons
    document.getElementById('save-draft').addEventListener('click', function() {
        // Save all paragraphs
        for (let i = 0; i <= currentParagraph; i++) {
            saveParagraph(i);
        }
        
        // Update essay status to draft
        fetch('/essay/update-status/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                essay_id: {{ essay.id }},
                status: 'draft'
            })
        })
        .then(() => {
            alert('Draft saved successfully!');
        });
    });
    
    document.getElementById('edit-mode').addEventListener('click', function() {
        editMode = !editMode;
        const btn = document.getElementById('edit-mode');
        
        if (editMode) {
            btn.textContent = 'Exit Edit Mode';
            btn.className = 'btn btn-warning';
            // Unlock all paragraphs
            for (let i = 0; i < totalParagraphs; i++) {
                unlockParagraph(i);
            }
        } else {
            btn.textContent = 'Edit Mode';
            btn.className = 'btn btn-outline-warning';
            // Re-lock appropriate paragraphs
            updateUI();
        }
    });
    
    document.getElementById('final-submit').addEventListener('click', function() {
        if (confirm('Are you sure you want to submit? You cannot edit after submission.')) {
            // Save all paragraphs
            for (let i = 0; i <= currentParagraph; i++) {
                saveParagraph(i);
            }
            
            // Submit essay
            fetch('/essay/final-submit/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    essay_id: {{ essay.id }}
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Essay submitted successfully! PDF has been generated.');
                    window.location.href = data.redirect_url;
                }
            });
        }
    });
    
    // Utility function to get CSRF token
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
    
    // Initialize
    updateUI();
});