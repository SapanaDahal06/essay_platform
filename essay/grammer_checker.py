# essay/utils/grammar_checker.py
import language_tool_python
import re

class AutoGrammarChecker:
    def __init__(self):
        self.tool = language_tool_python.LanguageTool('en-US')
    
    def check_essay(self, text):
        """Check grammar and spelling automatically"""
        if not text:
            return {'error': 'No text provided'}
        
        # Run grammar check
        matches = self.tool.check(text)
        
        # Categorize issues
        issues = {
            'grammar': [],
            'spelling': [],
            'punctuation': [],
            'style': []
        }
        
        for match in matches:
            issue = {
                'message': match.message,
                'suggestion': match.replacements[0] if match.replacements else '',
                'offset': match.offset,
                'length': match.errorLength,
                'context': match.context
            }
            
            # Categorize by rule type
            rule_id = match.ruleId.lower()
            if 'spell' in rule_id:
                issues['spelling'].append(issue)
            elif 'grammar' in rule_id or 'morphology' in rule_id:
                issues['grammar'].append(issue)
            elif 'punctuation' in rule_id:
                issues['punctuation'].append(issue)
            else:
                issues['style'].append(issue)
        
        # Calculate score (100 - 10*issues per 100 words)
        words = len(text.split())
        total_issues = len(matches)
        
        if words == 0:
            score = 100
        else:
            issues_per_100_words = (total_issues / words) * 100
            score = max(0, 100 - (issues_per_100_words * 2))
        
        return {
            'score': round(score, 1),
            'total_issues': total_issues,
            'issues': issues,
            'summary': {
                'grammar': len(issues['grammar']),
                'spelling': len(issues['spelling']),
                'punctuation': len(issues['punctuation']),
                'style': len(issues['style'])
            }
        }

# Create singleton instance
grammar_checker = AutoGrammarChecker()