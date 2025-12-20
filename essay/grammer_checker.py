import re

class GrammarChecker:
    def __init__(self):
        """Initialize grammar and spelling tools with error handling."""
        self.tool = None
        self.spell_checker = None
        self._initialized = False
        
    def _lazy_init(self):
        """Lazy initialization - only initialize when first used."""
        if self._initialized:
            return
        
        self._initialized = True
        
        # Try to initialize language_tool_python
        try:
            import language_tool_python
            self.tool = language_tool_python.LanguageTool('en-US')
        except ImportError:
            print("Warning: language_tool_python not installed. Grammar checking will be limited.")
        except Exception as e:
            print(f"Warning: Could not initialize language_tool_python: {e}")
        
        # Try to initialize SpellChecker
        try:
            from spellchecker import SpellChecker
            self.spell_checker = SpellChecker()
        except ImportError:
            print("Warning: pyspellchecker not installed. Spelling checking will be limited.")
        except Exception as e:
            print(f"Warning: Could not initialize SpellChecker: {e}")
    
    def check_essay(self, text):
        """Check grammar and spelling in an essay text."""
        # Initialize tools on first use
        self._lazy_init()
        
        # Handle empty or very short text
        if not text or not isinstance(text, str):
            return self._get_default_result()
        
        text = text.strip()
        if len(text) < 10:
            return self._get_default_result()
        
        # Initialize result variables
        grammar_issues = 0
        spelling_issues = 0
        suggestions = []
        misspelled = set()
        
        # --- Grammar Checking ---
        if self.tool:
            try:
                grammar_matches = self.tool.check(text)
                grammar_issues = len(grammar_matches)
                
                # Build suggestions from grammar matches
                for match in grammar_matches[:5]:
                    try:
                        suggestions.append({
                            'message': match.message,
                            'replacements': match.replacements[:3] if match.replacements else [],
                            'context': text[max(0, match.offset - 20):min(len(text), match.offset + match.errorLength + 20)]
                        })
                    except Exception as e:
                        print(f"Error processing grammar match: {e}")
                        continue
            except Exception as e:
                print(f"Error during grammar checking: {e}")
                grammar_issues = 0
        
        # --- Spelling Checking ---
        if self.spell_checker:
            try:
                # Extract words (letters only)
                words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
                total_words = len(words)
                
                if total_words > 0:
                    misspelled = self.spell_checker.unknown(words)
                    spelling_issues = len(misspelled)
                else:
                    spelling_issues = 0
            except Exception as e:
                print(f"Error during spelling checking: {e}")
                spelling_issues = 0
        
        # --- Calculate Scores ---
        grammar_score = max(0, min(100, 100 - (grammar_issues * 3)))
        spelling_score = max(0, min(100, 100 - (spelling_issues * 2)))
        overall_score = round((grammar_score * 0.6) + (spelling_score * 0.4), 2)
        
        # --- Return Result ---
        return {
            'grammar_issues': grammar_issues,
            'spelling_issues': spelling_issues,
            'grammar_score': grammar_score,
            'spelling_score': spelling_score,
            'score': overall_score,
            'suggestions': suggestions,
            'misspelled_words': list(misspelled)[:10] if misspelled else []
        }
    
    def _get_default_result(self):
        """Return default result for short or invalid text."""
        return {
            'grammar_issues': 0,
            'spelling_issues': 0,
            'grammar_score': 100,
            'spelling_score': 100,
            'score': 100,
            'suggestions': [],
            'misspelled_words': []
        }
    
    def get_grammar_tips(self):
        """Return grammar improvement tips."""
        return [
            "Use active voice instead of passive voice.",
            "Avoid run-on sentences; keep sentences concise.",
            "Check subject-verb agreement.",
            "Use proper punctuation, especially commas.",
            "Vary your sentence structure for better flow.",
            "Avoid using too many adverbs; use stronger verbs instead.",
            "Ensure pronoun references are clear.",
            "Use parallel structure in lists and comparisons.",
            "Read your essay aloud to catch awkward phrasing.",
            "Use transition words to connect ideas smoothly."
        ]
    
    def is_available(self):
        """Check if grammar and spelling tools are available."""
        self._lazy_init()
        return self.tool is not None or self.spell_checker is not None

# Create a global instance (but don't initialize tools yet)
grammar_checker = GrammarChecker()