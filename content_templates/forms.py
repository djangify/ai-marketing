# content_templates/forms.py - Update
from django import forms
from .models import Template, TemplatePrompt

class TemplateForm(forms.ModelForm):
    tags = forms.CharField(
        required=False, 
        widget=forms.TextInput(
            attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-main focus:border-main',
                'placeholder': 'Enter tags separated by commas'
            }
        ),
        help_text="Add tags to help group related templates (e.g., social media, email, blog)"
    )
    
    class Meta:
        model = Template
        fields = ['title', 'description', 'keywords']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-main focus:border-main'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-main focus:border-main',
                'rows': 3,
                'placeholder': 'Describe what this template is for'
            }),
            'keywords': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-main focus:border-main',
                'rows': 3,
                'placeholder': 'Enter keywords separated by commas to guide AI content generation'
            })
        }

class TemplatePromptForm(forms.ModelForm):
    class Meta:
        model = TemplatePrompt
        fields = ['name', 'prompt']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-main focus:border-main'}),
            'prompt': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-main focus:border-main', 'rows': 5})
        }
