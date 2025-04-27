# prompt_generator/forms.py
from django import forms
from .models import GeneratedPrompt, GeneratorTemplate

class PromptGeneratorForm(forms.Form):
    template = forms.ModelChoiceField(
        queryset=GeneratorTemplate.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-main focus:border-main'})
    )
    
    # Dynamically add fields based on template parameters in the view
    
class SaveGeneratedPromptForm(forms.ModelForm):
    class Meta:
        model = GeneratedPrompt
        fields = ['name', 'prompt_text']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-main focus:border-main'}),
            'prompt_text': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-main focus:border-main', 'rows': 10, 'readonly': True})
        }