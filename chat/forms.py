from django import forms

class MessageForm(forms.Form):
    content = forms.CharField(
        max_length=1000,
        widget=forms.TextInput(attrs={'placeholder': 'Type a message... (max 1000)', 'maxlength': 1000, 'autocomplete': 'off'}),
        strip=True,
    )
    def clean_content(self):
        c = self.cleaned_data['content'].strip()
        if not c:
            raise forms.ValidationError("Message cannot be empty!")
        if len(c) > 1000:
            raise forms.ValidationError("Max 1000 chars!")
        return c
