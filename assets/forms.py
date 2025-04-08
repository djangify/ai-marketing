from django import forms
from .models import Asset

class AssetUploadForm(forms.ModelForm):
    files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    
    class Meta:
        model = Asset
        fields = ['files']
        