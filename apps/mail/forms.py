from django import forms
from .models import Contact
from .widgets import MultipleFileInput  # Import widget custom

class ComposeEmailForm(forms.Form):
    recipients = forms.CharField(
        label='Kepada',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@domain.com, email2@domain.com'
        })
    )
    cc = forms.CharField(
        label='CC',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'cc@domain.com (opsional)'
        })
    )
    bcc = forms.CharField(
        label='BCC',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'bcc@domain.com (opsional)'
        })
    )
    subject = forms.CharField(
        label='Subjek',
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Subjek email'
        })
    )
    body_text = forms.CharField(
        label='Pesan',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 15,
            'placeholder': 'Tulis pesan Anda di sini...'
        })
    )
    body_html = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    # PERBAIKAN DISINI - Gunakan MultipleFileInput
    attachments = forms.FileField(
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
        })
    )
    
    def clean_recipients(self):
        recipients = self.cleaned_data['recipients']
        return recipients

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['email', 'name', 'company', 'phone', 'notes']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }