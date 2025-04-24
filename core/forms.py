# core/forms.py (create or modify)

from django import forms
from .models import ContactMessage, Tag

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

class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['first_name', 'subject', 'message']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-main focus:border-main',
                'placeholder': 'Your first name'
            }),
            'subject': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-main focus:border-main'
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-main focus:border-main',
                'rows': 5,
                'placeholder': 'Your message here...'
            }),
        }