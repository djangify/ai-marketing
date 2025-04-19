# core/forms.py (create or modify)

from django import forms
from .models import Tag

class TagForm(forms.Form):
    tags = forms.CharField(
        required=False, 
        widget=forms.TextInput(
            attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-main focus:border-main',
                'placeholder': 'Enter tags separated by commas'
            }
        ),
        help_text="Add tags to help organize content (e.g., social, email, blog)"
    )