from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q
from .models import Email, Attachment, Contact
from .forms import ComposeEmailForm, ContactForm
from .utils.send import send_email_via_smtp
import json

@login_required
def inbox(request):
    """Tampilkan inbox"""
    folder = request.GET.get('folder', 'inbox')
    search_query = request.GET.get('q', '')
    
    # Base query
    emails = Email.objects.filter(
        recipients__icontains=request.user.email,
        folder=folder
    )
    
    # Filter berdasarkan pencarian
    if search_query:
        emails = emails.filter(
            Q(subject__icontains=search_query) |
            Q(body_text__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(emails, 20)  # 20 emails per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Hitung unread
    unread_count = Email.objects.filter(
        recipients__icontains=request.user.email,
        folder='inbox',
        is_read=False
    ).count()
    
    context = {
        'page_obj': page_obj,
        'folder': folder,
        'unread_count': unread_count,
        'search_query': search_query,
    }
    return render(request, 'mail/inbox.html', context)

@login_required
def compose(request):
    """Tulis email baru"""
    if request.method == 'POST':
        form = ComposeEmailForm(request.POST, request.FILES)
        if form.is_valid():
            # Buat email object
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
            
            # Handle multiple attachments
            attachments = request.FILES.getlist('attachments')
            for f in attachments:
                Attachment.objects.create(
                    email=email,
                    file=f,
                    filename=f.name,
                    content_type=f.content_type,
                    size=f.size
                )
            
            # Kirim email via SMTP
            success = send_email_via_smtp(email)
            
            if success:
                messages.success(request, 'Email berhasil dikirim!')
            else:
                messages.warning(request, 'Email disimpan, tapi gagal dikirim. Coba lagi nanti.')
            
            return redirect('mail:inbox')
    else:
        # PRE-FILL UNTUK REPLY/FORWARD
        initial = {}  # <-- PENTING: Define initial sebagai dictionary kosong dulu
        
        reply_to_id = request.GET.get('reply_to')
        if reply_to_id:
            try:
                original = Email.objects.get(id=reply_to_id)
                initial = {
                    'subject': f"Re: {original.subject}",
                    'recipients': original.sender.email,
                    'body_text': f"\n\n\n-------- Original Message --------\nSubject: {original.subject}\nFrom: {original.sender.email}\nDate: {original.created_at}\n\n{original.body_text}"
                }
            except Email.DoesNotExist:
                pass
        
        # Bisa juga untuk forward
        forward_id = request.GET.get('forward')
        if forward_id:
            try:
                original = Email.objects.get(id=forward_id)
                initial = {
                    'subject': f"Fwd: {original.subject}",
                    'body_text': f"\n\n\n-------- Forwarded Message --------\nSubject: {original.subject}\nFrom: {original.sender.email}\nDate: {original.created_at}\n\n{original.body_text}"
                }
            except Email.DoesNotExist:
                pass
        
        form = ComposeEmailForm(initial=initial)
    
    contacts = Contact.objects.filter(user=request.user)
    context = {
        'form': form,
        'contacts': contacts,
    }
    return render(request, 'mail/compose.html', context)

@login_required
def view_email(request, email_id):
    """Lihat detail email"""
    email = get_object_or_404(Email, id=email_id)
    
    # Tandai sebagai sudah dibaca
    if not email.is_read and request.user.email in email.recipients:
        email.is_read = True
        email.save(update_fields=['is_read'])
    
    context = {
        'email': email,
    }
    return render(request, 'mail/view_email.html', context)

@login_required
def delete_email(request, email_id):
    """Pindahkan ke trash atau hapus permanen"""
    email = get_object_or_404(Email, id=email_id)
    
    if email.folder == 'trash':
        # Hapus permanen
        email.delete()
        messages.success(request, 'Email dihapus permanen.')
    else:
        # Pindahkan ke trash
        email.folder = 'trash'
        email.save(update_fields=['folder'])
        messages.success(request, 'Email dipindahkan ke trash.')
    
    return redirect('mail:inbox')

@login_required
def toggle_star(request, email_id):
    """Toggle star status"""
    email = get_object_or_404(Email, id=email_id)
    email.is_starred = not email.is_starred
    email.save(update_fields=['is_starred'])
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'starred': email.is_starred})
    
    return redirect(request.META.get('HTTP_REFERER', 'mail:inbox'))

@login_required
def contacts(request):
    """Manajemen kontak"""
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
    
    contacts_list = Contact.objects.filter(user=request.user)
    
    context = {
        'contacts': contacts_list,
        'form': form,
    }
    return render(request, 'mail/contacts.html', context)

@login_required
def delete_contact(request, contact_id):
    """Hapus kontak"""
    contact = get_object_or_404(Contact, id=contact_id, user=request.user)
    contact.delete()
    messages.success(request, 'Kontak dihapus.')
    return redirect('mail:contacts')