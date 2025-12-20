from django import forms
from .models import Essay, Comment, Language

class EssayForm(forms.ModelForm):
    writing_mode = forms.ChoiceField(
        choices=[('normal', 'Normal'), ('paragraph', 'Paragraph by Paragraph')],
        widget=forms.RadioSelect,
        initial='normal'
    )
    max_paragraphs = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=5,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    primary_language = forms.ModelChoiceField(
        queryset=Language.objects.filter(is_active=True),
        empty_label="Select Language",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Essay
        fields = ['title', 'content', 'category', 'status', 'writing_mode', 'max_paragraphs', 'primary_language']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Essay Title',
                'id': 'essay-title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 10, 
                'placeholder': 'Write your essay here...',
                'id': 'essay-content'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].initial = 'draft'

class ParagraphForm(forms.Form):
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control paragraph-editor',
            'rows': 8,
            'placeholder': 'Write your paragraph here...'
        })
    )
    language = forms.ModelChoiceField(
        queryset=Language.objects.filter(is_active=True),
        empty_label="Select Language",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Add a comment...'
            }),
        }