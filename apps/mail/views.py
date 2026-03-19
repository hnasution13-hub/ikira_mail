from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Email, Attachment, Contact
from .forms import ComposeEmailForm, ContactForm
from .utils.send import send_email_via_smtp
import traceback

FOLDER_TABS = [
    ('inbox', 'Inbox'),
    ('sent', 'Terkirim'),
    ('drafts', 'Draft'),
    ('trash', 'Trash'),
]

def base_context(user):
    return {
        'unread_count': Email.objects.filter(
            recipients__icontains=user.email,
            folder='inbox',
            is_read=False
        ).count(),
        'folder_tabs': FOLDER_TABS,
    }

@login_required
def inbox(request):
    folder = request.GET.get('folder', 'inbox')
    search_query = request.GET.get('q', '')

    # Sent folder: filter by sender. Semua folder lain: filter by recipients
    if folder == 'sent':
        emails = Email.objects.filter(
            sender=request.user,
            folder=folder
        )
    else:
        emails = Email.objects.filter(
            recipients__icontains=request.user.email,
            folder=folder
        )
    if search_query:
        emails = emails.filter(
            Q(subject__icontains=search_query) |
            Q(body_text__icontains=search_query)
        )

    paginator = Paginator(emails, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    ctx = base_context(request.user)
    ctx.update({
        'page_obj': page_obj,
        'folder': folder,
        'search_query': search_query,
    })
    return render(request, 'mail/inbox.html', ctx)

@login_required
def compose(request):
    if request.method == 'POST':
        # Treat semua POST ke compose sebagai AJAX - selalu return JSON
        is_ajax = True
        try:
            form = ComposeEmailForm(request.POST, request.FILES)
            if not form.is_valid():
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': str(form.errors), 'type': 'ValidationError'}, status=400)
                for field, errors in form.errors.items():
                    messages.error(request, f"{field}: {', '.join(errors)}")
                form = ComposeEmailForm(initial=request.POST)
            else:
                email = Email.objects.create(
                    sender=request.user,
                    recipients=form.cleaned_data['recipients'],
                    cc=form.cleaned_data.get('cc', ''),
                    bcc=form.cleaned_data.get('bcc', ''),
                    subject=form.cleaned_data['subject'],
                    body_text=form.cleaned_data['body_text'],
                    body_html=form.cleaned_data.get('body_html', ''),
                    folder='outbox'
                )

                attachments = form.cleaned_data.get('attachments') or []
                for f in attachments:
                    if f and hasattr(f, 'name'):
                        try:
                            Attachment.objects.create(
                                email=email,
                                file=f,
                                filename=f.name,
                                content_type=f.content_type,
                                size=f.size
                            )
                        except Exception as att_err:
                            print(f"[COMPOSE] Error attachment {f.name}: {att_err}")

                success = send_email_via_smtp(email)

                if is_ajax:
                    if success:
                        return JsonResponse({'status': 'ok', 'redirect': '/'})
                    else:
                        return JsonResponse({'status': 'error', 'message': 'Email disimpan tapi gagal dikirim.', 'type': 'SMTPError'})

                if success:
                    messages.success(request, 'Email berhasil dikirim!')
                else:
                    messages.warning(request, 'Email disimpan, tapi gagal dikirim. Coba lagi nanti.')
                return redirect('mail:inbox')

        except Exception as e:
            tb = traceback.format_exc()
            print(f"[COMPOSE ERROR] {str(e)}")
            print(tb)
            if is_ajax:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e),
                    'type': type(e).__name__,
                    'traceback': tb
                }, status=500)
            messages.error(request, f'Error: {str(e)}')

    else:
        initial = {}
        reply_to_id = request.GET.get('reply_to')
        if reply_to_id:
            try:
                original = Email.objects.get(id=reply_to_id)
                initial = {
                    'subject': f"Re: {original.subject}",
                    'recipients': original.sender.email,
                    'body_text': f"\n\n\n-------- Original Message --------\nFrom: {original.sender.email}\nDate: {original.created_at}\n\n{original.body_text}"
                }
            except Email.DoesNotExist:
                pass

        forward_id = request.GET.get('forward')
        if forward_id:
            try:
                original = Email.objects.get(id=forward_id)
                initial = {
                    'subject': f"Fwd: {original.subject}",
                    'body_text': f"\n\n\n-------- Forwarded Message --------\nFrom: {original.sender.email}\nDate: {original.created_at}\n\n{original.body_text}"
                }
            except Email.DoesNotExist:
                pass

        to_email = request.GET.get('to')
        if to_email:
            initial['recipients'] = to_email

        form = ComposeEmailForm(initial=initial)

    ctx = base_context(request.user)
    ctx.update({
        'form': form,
        'contacts': Contact.objects.filter(user=request.user),
    })
    return render(request, 'mail/compose.html', ctx)

@login_required
def view_email(request, email_id):
    email = get_object_or_404(Email, id=email_id)
    if not email.is_read and request.user.email in email.recipients:
        email.is_read = True
        email.save(update_fields=['is_read'])
    ctx = base_context(request.user)
    ctx['email'] = email
    return render(request, 'mail/view_email.html', ctx)

@login_required
def delete_email(request, email_id):
    email = get_object_or_404(Email, id=email_id)
    if email.folder == 'trash':
        email.delete()
        messages.success(request, 'Email dihapus permanen.')
    else:
        email.folder = 'trash'
        email.save(update_fields=['folder'])
        messages.success(request, 'Email dipindahkan ke trash.')
    return redirect('mail:inbox')

@login_required
def toggle_star(request, email_id):
    email = get_object_or_404(Email, id=email_id)
    email.is_starred = not email.is_starred
    email.save(update_fields=['is_starred'])
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'starred': email.is_starred})
    return redirect(request.META.get('HTTP_REFERER', 'mail:inbox'))

@login_required
def contacts(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.user = request.user
            contact.save()
            messages.success(request, 'Kontak berhasil ditambahkan.')
            return redirect('mail:contacts')
    else:
        form = ContactForm()

    ctx = base_context(request.user)
    ctx.update({
        'contacts': Contact.objects.filter(user=request.user),
        'form': form,
    })
    return render(request, 'mail/contacts.html', ctx)

@login_required
def delete_contact(request, contact_id):
    contact = get_object_or_404(Contact, id=contact_id, user=request.user)
    contact.delete()
    messages.success(request, 'Kontak dihapus.')
    return redirect('mail:contacts')

@login_required
def debug_connection(request):
    """Debug view - test SMTP connection. Hapus setelah testing."""
    import smtplib
    import socket
    from django.conf import settings
    from django.core.mail import send_mail

    results = {}

    results['settings'] = {
        'EMAIL_BACKEND': settings.EMAIL_BACKEND,
        'EMAIL_HOST': getattr(settings, 'EMAIL_HOST', 'NOT SET'),
        'EMAIL_PORT': getattr(settings, 'EMAIL_PORT', 'NOT SET'),
        'EMAIL_USE_TLS': getattr(settings, 'EMAIL_USE_TLS', 'NOT SET'),
        'EMAIL_HOST_USER': getattr(settings, 'EMAIL_HOST_USER', 'NOT SET'),
        'EMAIL_HOST_PASSWORD': '***SET***' if getattr(settings, 'EMAIL_HOST_PASSWORD', '') else 'NOT SET',
        'DEFAULT_FROM_EMAIL': settings.DEFAULT_FROM_EMAIL,
    }

    try:
        host = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
        ip = socket.gethostbyname(host)
        results['dns'] = {'status': 'OK', 'host': host, 'ip': ip}
    except Exception as e:
        results['dns'] = {'status': 'FAILED', 'error': str(e)}

    try:
        host = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
        port = getattr(settings, 'EMAIL_PORT', 587)
        sock = socket.create_connection((host, port), timeout=10)
        sock.close()
        results['tcp'] = {'status': 'OK', 'host': host, 'port': port}
    except Exception as e:
        results['tcp'] = {'status': 'FAILED', 'error': str(e)}

    try:
        host = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
        port = getattr(settings, 'EMAIL_PORT', 587)
        user = getattr(settings, 'EMAIL_HOST_USER', '')
        password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        smtp = smtplib.SMTP(host, port, timeout=10)
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(user, password)
        smtp.quit()
        results['smtp_login'] = {'status': 'OK', 'user': user}
    except Exception as e:
        results['smtp_login'] = {'status': 'FAILED', 'error': str(e)}

    try:
        send_mail(
            subject='[DEBUG] Test i-kira Mail',
            message='Test koneksi dari debug_connection.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
            fail_silently=False,
        )
        results['send_test'] = {'status': 'OK', 'sent_to': request.user.email}
    except Exception as e:
        results['send_test'] = {'status': 'FAILED', 'error': str(e), 'traceback': traceback.format_exc()}

    html = '<html><body style="font-family:monospace;background:#111;color:#eee;padding:2rem;">'
    html += '<h2 style="color:#e63329;">Debug Connection</h2>'
    for section, data in results.items():
        color = '#4ade80' if data.get('status') == 'OK' else '#ff7070'
        html += f'<h3 style="color:{color};margin-top:1.5rem;">{section.upper()} — {data.get("status","")}</h3>'
        html += '<pre style="background:#1c1c1c;padding:1rem;border-radius:8px;white-space:pre-wrap;">'
        for k, v in data.items():
            html += f'{k}: {v}\n'
        html += '</pre>'
    html += '</body></html>'
    return HttpResponse(html)
