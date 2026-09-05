"""
accounts/forms.py - Signup + Profile Edit forms
Hinglish: Form = HTML form ka Python version, validation yahan hota hai.
"""
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils.text import slugify
from .models import Profile


class SignupForm(UserCreationForm):
    """
    UserCreationForm already password1/password2 deta hai, hum email + username add karenge.
    """
    email = forms.EmailField(required=True, help_text="Email (verification nahi chahiye MVP me)")
    # Profile wala username (slugified) - User.username se alag dikhane ke liye
    # Par hum User.username ko bhi same slugified value denge taaki sync rahe
    bio = forms.CharField(
        required=False,
        max_length=150,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Bio max 150 chars...'}),
        help_text="Max 150 characters"
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_username(self):
        username = self.cleaned_data['username']
        slug = slugify(username)
        if len(slug) > 30:
            raise forms.ValidationError("Username max 30 chars after slugify!")
        if len(slug) < 3:
            raise forms.ValidationError("Username min 3 chars!")
        if User.objects.filter(username__iexact=slug).exists():
            raise forms.ValidationError("Username already taken!")
        if Profile.objects.filter(username__iexact=slug).exists():
            raise forms.ValidationError("Username already taken in profiles!")
        return slug  # slugified save hoga

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email already registered!")
        return email

    def save(self, commit=True):
        # User banao, fir Profile banao
        user = super().save(commit=False)
        user.username = self.cleaned_data['username']  # slugified
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Profile create - bio ke saath
            Profile.objects.create(
                user=user,
                username=user.username,  # same as User.username, slugified
                bio=self.cleaned_data.get('bio', '')
            )
        return user


class ProfileEditForm(forms.ModelForm):
    """
    Profile edit - username, bio, avatar
    """
    class Meta:
        model = Profile
        fields = ('username', 'bio', 'avatar')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'maxlength': 150}),
            'username': forms.TextInput(attrs={'maxlength': 30}),
        }
        help_texts = {
            'username': 'Unique, 30 chars, slugified automatically',
            'bio': 'Max 150 chars',
        }

    def clean_username(self):
        username = slugify(self.cleaned_data['username'])
        # Khud ka profile chod ke check karo
        qs = Profile.objects.filter(username__iexact=username).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Username already taken!")
        if len(username) < 3:
            raise forms.ValidationError("Username min 3 chars!")
        return username

    def clean_bio(self):
        bio = self.cleaned_data['bio']
        if len(bio) > 150:
            raise forms.ValidationError("Bio max 150 chars!")
        return bio
