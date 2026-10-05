from django import forms
from .models import Profile


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar', 'name', 'username', 'bio']
        widgets = {
            'avatar': forms.FileInput(attrs={
                'id': 'id_avatar',
                'accept': 'image/*',
            }),
            'name': forms.TextInput(attrs={
                'class': 'md-input',
                'placeholder': 'e.g. Alex Morgan',
            }),
            'username': forms.TextInput(attrs={
                'class': 'md-input',
                'placeholder': 'alex_m',
            }),
            'bio': forms.Textarea(attrs={
                'class': 'md-input md-textarea',
                'placeholder': 'Write a brief status or bio...',
                'rows': 3,
            }),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            raise forms.ValidationError("Username cannot be empty.")
        if ' ' in username:
            raise forms.ValidationError("Username cannot contain spaces.")
        return username