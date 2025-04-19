# projects/forms.py
from django import forms
from .models import Project, Prompt, GeneratedContent

class ProjectForm(forms.ModelForm):
    tags = forms.CharField(
        required=False, 
        widget=forms.TextInput(
            attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-main focus:border-main',
                'placeholder': 'Enter tags separated by commas'
            }
        ),
        help_text="Add tags to help group related projects (e.g., client name, campaign type)"
    )
    
    class Meta:
        model = Project
        fields = ['title', 'keywords']  # Now including keywords
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-main focus:border-main',
                'placeholder': 'Enter a descriptive name for your project, e.g., "Summer Campaign 2025"'
            }),
            'keywords': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-main focus:border-main',
                'rows': 3,
                'placeholder': 'Enter keywords separated by commas to guide AI content generation'
            })
        }

class PromptForm(forms.ModelForm):
    class Meta:
        model = Prompt
        fields = ['name', 'prompt']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-main focus:border-main'}),
            'prompt': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-main focus:border-main', 'rows': 5})
        }

class GeneratedContentForm(forms.ModelForm):
    class Meta:
        model = GeneratedContent
        fields = ['result']
        widgets = {
            'result': forms.Textarea(attrs={'class': 'form-control', 'rows': 10})
        }
        