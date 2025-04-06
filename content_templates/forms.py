# content_templates/forms.py
from django import forms
from .models import Template, TemplatePrompt

class TemplateForm(forms.ModelForm):
    class Meta:
        model = Template
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'})
        }

class TemplatePromptForm(forms.ModelForm):
    class Meta:
        model = TemplatePrompt
        fields = ['name', 'prompt']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'prompt': forms.Textarea(attrs={'class': 'form-control', 'rows': 5})
        }