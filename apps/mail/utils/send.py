import resend
import base64
import traceback
from django.conf import settings


def send_email_via_smtp(email_obj, attachment_data=None):
    """
    Kirim email via Resend SDK langsung.
    attachment_data: list of dict {filename, content, content_type}
    """
    try:
        resend.api_key = settings.RESEND_API_KEY

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

        # Attachment dari memory
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

        print(f"[MAIL] Email {email_obj.id} sent OK via Resend SDK")
        return True

    except Exception as e:
        print(f"[MAIL ERROR] {str(e)}")
        print(traceback.format_exc())
        return False
