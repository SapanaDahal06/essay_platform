# essay/grammar_checker.py
import re

class GrammarChecker:
    """Grammar and spelling checker for essays"""
    
    def check_essay(self, essay):
        """Check grammar and spelling in essay"""
        content = essay.content
        if not content:
            return None
        
        results = {
            'grammar_errors': [],
            'spelling_errors': [],
            'readability_score': 0,
            'overall_score': 0
        }
        
        # 1. Check grammar
        grammar_errors = self._check_grammar(content)
        results['grammar_errors'] = grammar_errors
        
        # 2. Check spelling
        spelling_errors = self._check_spelling(content)
        results['spelling_errors'] = spelling_errors
        
        # 3. Calculate readability
        readability = self._calculate_readability(content)
        results['readability_score'] = readability
        
        # 4. Calculate overall score
        total_errors = len(grammar_errors) + len(spelling_errors)
        word_count = len(content.split())
        
        if word_count > 0:
            error_density = total_errors / word_count * 100
            base_score = max(0, 100 - (error_density * 10))
        else:
            base_score = 0
            
        # Adjust with readability
        overall_score = (base_score * 0.7) + (readability * 0.3)
        results['overall_score'] = min(100, overall_score)
        
        return results
    
    def _check_grammar(self, text):
        """Check grammar in text"""
        errors = []
        
        # Common grammar mistakes
        common_errors = {
            'their': ["they're", "there"],
            'your': ["you're"],
            'its': ["it's"],
            'then': ["than"],
            'affect': ["effect"],
            'accept': ["except"],
            'complement': ["compliment"],
            'loose': ["lose"],
            'principle': ["principal"],
            'stationary': ["stationery"]
        }
        
        # Split into sentences
        sentences = text.split('. ')
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
                
            words = sentence.split()
            
            # Check for common errors
            for j, word in enumerate(words):
                cleaned_word = ''.join(c for c in word if c.isalpha()).lower()
                if cleaned_word in common_errors:
                    errors.append({
                        'sentence': i + 1,
                        'word': word,
                        'suggestions': common_errors[cleaned_word],
                        'rule': f'Common confusion: {cleaned_word} vs {common_errors[cleaned_word][0]}'
                    })
            
            # Check for sentence fragments
            if len(words) < 3:
                errors.append({
                    'sentence': i + 1,
                    'issue': 'Possible sentence fragment',
                    'suggestion': 'Consider expanding this thought into a complete sentence'
                })
            
            # Check for run-on sentences
            if len(words) > 50:
                errors.append({
                    'sentence': i + 1,
                    'issue': 'Long sentence - might be a run-on',
                    'suggestion': 'Consider breaking into shorter sentences'
                })
        
        return errors
    
    def _check_spelling(self, text):
        """Check spelling in text"""
        errors = []
        
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
            'occassion': ['occasion'],
            'truely': ['truly'],
            'alot': ['a lot'],
            'untill': ['until'],
            'pronounciation': ['pronunciation'],
            'dissappear': ['disappear']
        }
        
        words = text.split()
        for i, word in enumerate(words):
            cleaned_word = ''.join(c for c in word if c.isalpha()).lower()
            if cleaned_word in common_misspellings:
                errors.append({
                    'position': i,
                    'word': word,
                    'suggestions': common_misspellings[cleaned_word],
                    'context': ' '.join(words[max(0, i-2):min(len(words), i+3)])
                })
        
        return errors
    
    def _calculate_readability(self, text):
        """Calculate Flesch Reading Ease score"""
        sentences = len([s for s in text.split('.') if s.strip()])
        words = len(text.split())
        syllables = self._count_syllables(text)
        
        if sentences == 0 or words == 0:
            return 50  # Default score
        
        # Flesch Reading Ease formula
        score = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
        return max(0, min(100, score))
    
    def _count_syllables(self, text):
        """Approximate syllable count"""
        vowels = 'aeiouy'
        count = 0
        words = text.lower().split()
        
        for word in words:
            if not word:
                continue
                
            word = ''.join(c for c in word if c.isalpha())
            if not word:
                continue
                
            if word[0] in vowels:
                count += 1
                
            for i in range(1, len(word)):
                if word[i] in vowels and word[i-1] not in vowels:
                    count += 1
                    
            if word.endswith('e'):
                count -= 1
                
            if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
                count += 1
                
            if count == 0:
                count += 1
                
        return count
    
    def get_highlighted_text(self, text, grammar_errors, spelling_errors):
        """Generate HTML with highlighted errors"""
        if not text:
            return ""
        
        content = text
        
        # Grammar errors
        for error in grammar_errors:
            word = error.get('word', '')
            suggestion = error.get('suggestion', '')
            if word and suggestion:
                highlighted = f'<span class="grammar-error" title="Grammar: {suggestion}">{word}</span>'
                content = content.replace(word, highlighted, 1)
        
        # Spelling errors
        for error in spelling_errors:
            word = error.get('word', '')
            suggestions = error.get('suggestions', [])
            if word and suggestions:
                suggestion_text = "Suggestions: " + ", ".join(suggestions[:3])
                highlighted = f'<span class="spelling-error" title="{suggestion_text}">{word}</span>'
                content = content.replace(word, highlighted, 1)
        
        return content