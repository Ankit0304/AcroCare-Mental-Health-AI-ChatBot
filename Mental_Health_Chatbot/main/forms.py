# forms.py
from django import forms
from .models import Profile

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture']


from .models import JournalEntry

class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ['category', 'content']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Write your thoughts here...'}),
        }
