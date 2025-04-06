# projects/forms.py
from django import forms
from .models import Project, Asset, Prompt, GeneratedContent

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'})
        }

class PromptForm(forms.ModelForm):
    class Meta:
        model = Prompt
        fields = ['name', 'prompt']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'prompt': forms.Textarea(attrs={'class': 'form-control', 'rows': 5})
        }

class GeneratedContentForm(forms.ModelForm):
    class Meta:
        model = GeneratedContent
        fields = ['result']
        widgets = {
            'result': forms.Textarea(attrs={'class': 'form-control', 'rows': 10})
        }
        