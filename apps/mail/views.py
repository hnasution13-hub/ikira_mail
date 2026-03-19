from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
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
    """Context yang dibutuhkan base.html di semua halaman"""
    return {
        'unread_count': Email.objects.filter(
            recipients__icontains=user.email,
            folder='inbox',
            is_read=False
        ).count()
    }

@login_required
def inbox(request):
    folder = request.GET.get('folder', 'inbox')
    search_query = request.GET.get('q', '')

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
        'folder_tabs': FOLDER_TABS,
    })
    return render(request, 'mail/inbox.html', ctx)

@login_required
def compose(request):
    if request.method == 'POST':
        print(f"[COMPOSE] POST keys: {list(request.POST.keys())}")
        try:
            form = ComposeEmailForm(request.POST, request.FILES)
            if not form.is_valid():
                print(f"[COMPOSE] Form errors: {form.errors}")
                messages.error(request, f'Form tidak valid: {form.errors}')
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
                if not isinstance(attachments, list):
                    attachments = [attachments]
                for f in attachments:
                    if f:
                        Attachment.objects.create(
                            email=email,
                            file=f,
                            filename=f.name,
                            content_type=f.content_type,
                            size=f.size
                        )

                success = send_email_via_smtp(email)

                is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                if is_ajax:
                    if success:
                        return JsonResponse({'status': 'ok', 'redirect': '/'})
                    else:
                        return JsonResponse({'status': 'error', 'message': 'Email disimpan tapi gagal dikirim.'})

                if success:
                    messages.success(request, 'Email berhasil dikirim!')
                else:
                    messages.warning(request, 'Email disimpan, tapi gagal dikirim. Coba lagi nanti.')

                return redirect('mail:inbox')

        except Exception as e:
            print(f"[COMPOSE ERROR] {str(e)}")
            print(traceback.format_exc())
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
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
