from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Email',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recipients', models.TextField(help_text='Email recipients, separated by commas')),
                ('cc', models.TextField(blank=True, help_text='CC recipients')),
                ('bcc', models.TextField(blank=True, help_text='BCC recipients')),
                ('subject', models.CharField(max_length=255)),
                ('body_text', models.TextField(blank=True)),
                ('body_html', models.TextField(blank=True)),
                ('folder', models.CharField(choices=[('inbox', 'Inbox'), ('sent', 'Sent'), ('drafts', 'Drafts'), ('trash', 'Trash'), ('spam', 'Spam'), ('archive', 'Archive'), ('outbox', 'Outbox')], default='inbox', max_length=20)),
                ('is_read', models.BooleanField(default=False)),
                ('is_starred', models.BooleanField(default=False)),
                ('is_important', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('message_id', models.CharField(blank=True, max_length=255)),
                ('thread_id', models.CharField(blank=True, max_length=255)),
                ('in_reply_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='replies', to='mail.email')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_emails', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='attachments/%Y/%m/%d/')),
                ('filename', models.CharField(max_length=255)),
                ('content_type', models.CharField(max_length=100)),
                ('size', models.IntegerField(help_text='File size in bytes')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('email', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='mail.email')),
            ],
        ),
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField()),
                ('name', models.CharField(max_length=255)),
                ('company', models.CharField(blank=True, max_length=255)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contacts', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='EmailFolder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mail.emailfolder')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='custom_folders', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.AddIndex(
            model_name='email',
            index=models.Index(fields=['recipients'], name='mail_email_recipie_idx'),
        ),
        migrations.AddIndex(
            model_name='email',
            index=models.Index(fields=['sender', 'folder'], name='mail_email_sender_idx'),
        ),
        migrations.AddIndex(
            model_name='email',
            index=models.Index(fields=['thread_id'], name='mail_email_thread_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='contact',
            unique_together={('user', 'email')},
        ),
        migrations.AlterUniqueTogether(
            name='emailfolder',
            unique_together={('user', 'name')},
        ),
    ]
