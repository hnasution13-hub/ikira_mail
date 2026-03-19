"""
Utility functions untuk mengirim email via Django email backend
"""
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from apps.mail.models import Email
import logging

logger = logging.getLogger(__name__)


def send_email_via_smtp(email_obj):
    """
    Kirim email menggunakan Django's email backend (Mailtrap/SMTP).
    Compatible dengan Cloudinary storage (tidak pakai .path).
    """
    try:
        to_list = email_obj.get_recipient_list()
        cc_list = [cc.strip() for cc in email_obj.cc.split(',')] if email_obj.cc else []
        bcc_list = [bcc.strip() for bcc in email_obj.bcc.split(',')] if email_obj.bcc else []

        msg = EmailMultiAlternatives(
            subject=email_obj.subject,
            body=email_obj.body_text,
            from_email=email_obj.sender.email,
            to=to_list,
            cc=cc_list,
            bcc=bcc_list,
        )

        if email_obj.body_html:
            msg.attach_alternative(email_obj.body_html, "text/html")

        # Attach files - support local dan Cloudinary storage
        for attachment in email_obj.attachments.all():
            try:
                # Coba baca via .read() - works untuk local & Cloudinary
                attachment.file.open('rb')
                content = attachment.file.read()
                attachment.file.close()
                msg.attach(attachment.filename, content, attachment.content_type)
            except Exception as att_err:
                logger.warning(f"Skip attachment {attachment.filename}: {att_err}")

        msg.send()

        # Update status ke sent
        from django.utils import timezone
        email_obj.folder = 'sent'
        email_obj.sent_at = timezone.now()
        email_obj.save(update_fields=['folder', 'sent_at'])

        logger.info(f"Email sent successfully: {email_obj.id}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email {email_obj.id}: {str(e)}")
        return False
