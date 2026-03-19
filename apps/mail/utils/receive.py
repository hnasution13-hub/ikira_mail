"""
Utility functions untuk membaca email via IMAP
"""
import imaplib
import email
from email.utils import parsedate_to_datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.mail.models import Email, Attachment
import logging
import tempfile
import os
from datetime import datetime

User = get_user_model()
logger = logging.getLogger(__name__)

class IMAPMailReader:
    """
    Class untuk membaca email dari server IMAP
    """
    def __init__(self, email_address, password, server=None, port=None):
        self.email_address = email_address
        self.password = password
        self.server = server or settings.IMAP_SERVER
        self.port = port or settings.IMAP_PORT
        self.connection = None
    
    def connect(self):
        """Connect ke IMAP server"""
        try:
            self.connection = imaplib.IMAP4_SSL(self.server, self.port)
            self.connection.login(self.email_address, self.password)
            return True
        except Exception as e:
            logger.error(f"IMAP connection failed: {str(e)}")
            return False
    
    def disconnect(self):
        """Tutup koneksi IMAP"""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
            except:
                pass
    
    def fetch_emails(self, folder='INBOX', limit=50):
        """
        Ambil email dari folder tertentu
        """
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            # Pilih folder
            self.connection.select(folder)
            
            # Cari semua email
            _, data = self.connection.search(None, 'ALL')
            mail_ids = data[0].split()
            
            # Ambil email terbaru sesuai limit
            emails = []
            for mail_id in mail_ids[-limit:]:
                _, msg_data = self.connection.fetch(mail_id, '(RFC822)')
                msg = email.message_from_bytes(msg_data[0][1])
                
                email_data = self.parse_email_message(msg)
                emails.append(email_data)
            
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching emails: {str(e)}")
            return []
    
    def parse_email_message(self, msg):
        """
        Parse email message menjadi dictionary
        """
        # Header
        subject = msg.get('Subject', '')
        from_addr = msg.get('From', '')
        to_addr = msg.get('To', '')
        date_str = msg.get('Date', '')
        
        # Parse date
        try:
            date = parsedate_to_datetime(date_str)
        except:
            date = datetime.now()
        
        # Body dan attachments
        body_text = ''
        body_html = ''
        attachments = []
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))
                
                if content_type == 'text/plain' and 'attachment' not in content_disposition:
                    body_text += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                elif content_type == 'text/html' and 'attachment' not in content_disposition:
                    body_html += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                elif 'attachment' in content_disposition:
                    # Handle attachment
                    filename = part.get_filename()
                    if filename:
                        # Simpan ke temporary file
                        with tempfile.NamedTemporaryFile(delete=False) as tmp:
                            tmp.write(part.get_payload(decode=True))
                            attachments.append({
                                'filename': filename,
                                'path': tmp.name,
                                'size': os.path.getsize(tmp.name)
                            })
        else:
            # Single part email
            body_text = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        return {
            'subject': subject,
            'from': from_addr,
            'to': to_addr,
            'date': date,
            'body_text': body_text,
            'body_html': body_html,
            'attachments': attachments
        }
    
    def save_email_to_db(self, email_data, user):
        """
        Simpan email ke database
        """
        try:
            # Ekstrak sender email
            import re
            sender_email = re.findall(r'<(.+?)>', email_data['from'])
            if not sender_email:
                sender_email = [email_data['from']]
            
            # Buat email object
            email_obj = Email.objects.create(
                sender=user,  # Ini perlu disesuaikan - ideally cari user berdasarkan sender email
                recipients=email_data['to'],
                subject=email_data['subject'],
                body_text=email_data['body_text'],
                body_html=email_data['body_html'],
                folder='inbox',
                created_at=email_data['date']
            )
            
            # Simpan attachments
            for att in email_data['attachments']:
                attachment = Attachment(
                    email=email_obj,
                    filename=att['filename'],
                    size=att['size']
                )
                # Copy file ke media storage
                with open(att['path'], 'rb') as f:
                    attachment.file.save(att['filename'], f)
                attachment.save()
                
                # Hapus temporary file
                os.unlink(att['path'])
            
            return email_obj
            
        except Exception as e:
            logger.error(f"Error saving email to DB: {str(e)}")
            return None