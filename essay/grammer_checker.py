import re

def check_grammar(text):
    """
    Basic grammar checker (simplified)
    You can enhance this later with LanguageTool or Grammarly API
    """
    if not text:
        return []
    
    issues = []
    
    # Check for lowercase 'i' as subject
    if re.search(r'\bi\s+', text):
        issues.append({
            'message': 'Use capital "I" when referring to yourself',
            'suggestion': 'I'
        })
    
    # Check for double spaces
    if '  ' in text:
        issues.append({
            'message': 'Avoid double spaces',
            'suggestion': 'Use single space'
        })
    
    # Check sentence capitalization
    sentences = re.split(r'[.!?]', text)
    for i, sentence in enumerate(sentences):
        sentence = sentence.strip()
        if sentence and not sentence[0].isupper():
            issues.append({
                'message': f'Sentence should start with capital letter',
                'suggestion': sentence.capitalize() if sentence else ''
            })
    
    # Check for common mistakes
    common_mistakes = [
        (r'\byou\s+are\b', "you are", "you're"),
        (r'\bi\s+am\b', "I am", "I'm"),
        (r'\bthey\s+are\b', "they are", "they're"),
        (r'\bwe\s+are\b', "we are", "we're"),
    ]
    
    for pattern, message, suggestion in common_mistakes:
        if re.search(pattern, text, re.IGNORECASE):
            issues.append({
                'message': f'Consider contraction: {message} -> {suggestion}',
                'suggestion': suggestion
            })
    
    return issues