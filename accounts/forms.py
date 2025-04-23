# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Profile


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text="Business Address only"
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        help_texts = {
            'username': 'Choose carefully, this cannot be changed later!'
        }
        
    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()
        
        # Blacklist of common free email providers
        blacklisted_domains = [
            'gmail.com', 'googlemail.com',
            'hotmail.com', 'hotmail.co.uk', 'hotmail.fr', 'hotmail.it',
            'live.com', 'live.co.uk',
            'yahoo.com', 'yahoo.co.uk', 'yahoo.fr',
            'outlook.com',
            'aol.com',
            'protonmail.com',
            'icloud.com',
            'mail.com',
            'inbox.com',
            'zoho.com',
            'yandex.com',
            'gmx.com',
        ]
        
        # Extract domain from email
        domain = email.split('@')[-1]
        
        # Check if domain is blacklisted
        if domain in blacklisted_domains:
            raise forms.ValidationError(
                "Please use your company email address. "
                "Free email providers (like Gmail, Hotmail, Yahoo) are not allowed for registration."
            )
        
        return email
 
    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-main focus:border-main'
            })
    
    def save(self, commit=True):
        user = super(SignUpForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Create profile for user
            Profile.objects.create(user=user)
        return user

class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-main focus:border-main'
            })

# accounts/forms.py
class ProfileUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = Profile
        fields = ['bio']
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 4, 
                'placeholder': 'Tell us a little about yourself (optional)'
            })
        }
        
    def __init__(self, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50'
            })
        
        # Special handling for the bio textarea
        if 'bio' in self.fields:
            self.fields['bio'].widget.attrs.update({
                'class': 'flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                'rows': 4
            })
                
    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            # Update the user's email
            user = profile.user
            user.email = self.cleaned_data['email']
            user.save()
            profile.save()
        return profile

def clean_email(self):
    email = self.cleaned_data.get('email', '').lower()
    
    # Blacklist of common free email providers
    blacklisted_domains = [
        'gmail.com', 'googlemail.com',
        'hotmail.com', 'hotmail.co.uk', 'hotmail.fr', 'hotmail.it',
        'live.com', 'live.co.uk',
        'yahoo.com', 'yahoo.co.uk', 'yahoo.fr',
        'outlook.com',
        'aol.com',
        'protonmail.com',
        'icloud.com',
        'mail.com',
        'inbox.com',
        'zoho.com',
        'yandex.com',
        'gmx.com',
    ]
    
    # Extract domain from email
    domain = email.split('@')[-1]
    
    # Check if domain is blacklisted
    if domain in blacklisted_domains:
        raise forms.ValidationError(
            "Please use your company email address. "
            "Free email providers (like Gmail, Hotmail, Yahoo) are not allowed for registration."
        )
    
    return email
