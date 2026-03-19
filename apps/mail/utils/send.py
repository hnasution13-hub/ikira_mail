import resend
import traceback
from django.conf import settings


def send_email_via_smtp(email_obj, attachment_data=None):
    try:
        # Ambil API key dari ANYMAIL dict atau env langsung
        api_key = settings.ANYMAIL.get('RESEND_API_KEY', '')
        if not api_key:
            from decouple import config
            api_key = config('RESEND_API_KEY', default='')

        if not api_key:
            print(f"[MAIL ERROR] RESEND_API_KEY tidak ditemukan")
            return False

        resend.api_key = api_key

        to_list = email_obj.get_recipient_list()
        if not to_list:
            print(f"[MAIL ERROR] No recipients")
            return False

        from_email = settings.DEFAULT_FROM_EMAIL
        print(f"[MAIL] Sending {email_obj.id} -> {to_list}")

        params = {
            "from": from_email,
            "to": to_list,
            "subject": email_obj.subject,
            "text": email_obj.body_text,
            "reply_to": [email_obj.sender.email],
        }

        if email_obj.cc:
            params["cc"] = [cc.strip() for cc in email_obj.cc.split(',') if cc.strip()]

        if email_obj.bcc:
            params["bcc"] = [bcc.strip() for bcc in email_obj.bcc.split(',') if bcc.strip()]

        if email_obj.body_html:
            params["html"] = email_obj.body_html

        if attachment_data:
            params["attachments"] = [
                {
                    "filename": att["filename"],
                    "content": list(att["content"]),
                }
                for att in attachment_data
            ]
            print(f"[MAIL] Attaching {len(attachment_data)} files")

        resend.Emails.send(params)

        from django.utils import timezone
        email_obj.folder = 'sent'
        email_obj.sent_at = timezone.now()
        email_obj.save(update_fields=['folder', 'sent_at'])

        print(f"[MAIL] Email {email_obj.id} sent OK")
        return True

    except Exception as e:
        print(f"[MAIL ERROR] {str(e)}")
        print(traceback.format_exc())
        return False
