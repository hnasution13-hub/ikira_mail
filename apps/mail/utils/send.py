from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import traceback


def send_email_via_smtp(email_obj, attachment_data=None):
    """
    Kirim email via Django email backend.
    attachment_data: list of dict {filename, content, content_type} dari memory
    """
    try:
        to_list = email_obj.get_recipient_list()
        cc_list = [cc.strip() for cc in email_obj.cc.split(',')] if email_obj.cc else []
        bcc_list = [bcc.strip() for bcc in email_obj.bcc.split(',')] if email_obj.bcc else []

        if not to_list:
            print(f"[MAIL ERROR] No recipients")
            return False

        from_email = settings.DEFAULT_FROM_EMAIL
        print(f"[MAIL] Sending {email_obj.id} -> {to_list}")
        print(f"[MAIL] Backend: {settings.EMAIL_BACKEND}")

        msg = EmailMultiAlternatives(
            subject=email_obj.subject,
            body=email_obj.body_text,
            from_email=from_email,
            to=to_list,
            cc=cc_list,
            bcc=bcc_list,
            reply_to=[email_obj.sender.email],
        )

        if email_obj.body_html:
            msg.attach_alternative(email_obj.body_html, "text/html")

        # Attach dari memory (prioritas) atau dari storage
        if attachment_data:
            for att in attachment_data:
                msg.attach(att['filename'], att['content'], att['content_type'])
                print(f"[MAIL] Attached from memory: {att['filename']}")
        else:
            # Fallback: baca dari storage
            for attachment in email_obj.attachments.all():
                try:
                    with attachment.file.storage.open(attachment.file.name, 'rb') as f:
                        content = f.read()
                    msg.attach(attachment.filename, content, attachment.content_type)
                    print(f"[MAIL] Attached from storage: {attachment.filename}")
                except Exception as att_err:
                    print(f"[MAIL] Skip attachment {attachment.filename}: {att_err}")

        msg.send()

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
