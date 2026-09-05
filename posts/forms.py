"""
posts/forms.py - Post create + Comment forms
Hinglish: Text form, images view me handle karenge.
"""
from django import forms
from .models import Post, Comment


class PostCreateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('content',)
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'maxlength': 500,
                'placeholder': 'What\'s on your mind? (max 500 chars)...'
            }),
        }

    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        if not content:
            raise forms.ValidationError("Content cannot be empty!")
        if len(content) > 500:
            raise forms.ValidationError("Max 500 characters!")
        return content


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('content',)
        widgets = {
            'content': forms.TextInput(attrs={
                'placeholder': 'Add a comment... (max 200 chars)',
                'maxlength': 200,
            }),
        }

    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        if not content:
            raise forms.ValidationError("Comment cannot be empty!")
        if len(content) > 200:
            raise forms.ValidationError("Max 200 characters!")
        return content
