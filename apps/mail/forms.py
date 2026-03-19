from django import forms
from .models import Contact


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class ComposeEmailForm(forms.Form):
    recipients = forms.CharField(label='Kepada')
    cc = forms.CharField(label='CC', required=False)
    bcc = forms.CharField(label='BCC', required=False)
    subject = forms.CharField(label='Subjek', max_length=255)
    body_text = forms.CharField(label='Pesan', widget=forms.Textarea())
    body_html = forms.CharField(required=False, widget=forms.HiddenInput())
    attachments = MultipleFileField(required=False)

    def clean_recipients(self):
        return self.cleaned_data['recipients']


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['email', 'name', 'company', 'phone', 'notes']
