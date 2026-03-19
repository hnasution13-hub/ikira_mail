from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import traceback

def send_email_via_smtp(email_obj):
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
        print(f"[MAIL] From: {from_email}")

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

        for attachment in email_obj.attachments.all():
            try:
                attachment.file.open('rb')
                content = attachment.file.read()
                attachment.file.close()
                msg.attach(attachment.filename, content, attachment.content_type)
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
