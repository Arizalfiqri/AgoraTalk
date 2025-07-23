# admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Category, Thread, Comment, Vote, Bookmark, Notification, Report
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils.html import format_html
from django.http import HttpResponse
from django import forms
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.utils.timesince import timesince
import csv

# Complete working admin configuration

class UserAdminForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(),
        help_text="Masukkan password untuk user baru",
        required=False,
        label="Password"
    )
    
    class Meta:
        model = User
        fields = '__all__'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data['password']:
            user.password = make_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class UserAdmin(admin.ModelAdmin):
    form = UserAdminForm
    
    # All fields in one group
    fields = (
        'username', 'password', 'first_name', 'last_name', 'email', 'bio', 'avatar',
        'role', 'points', 'is_verified', 'jurusan', 'angkatan', 
        'employee_id', 'department', 'instagram', 'linkedin',
        'is_active', 'is_staff', 'is_superuser'
    )
    
    # Updated list_display with new fields
    list_display = (
        'username', 'email', 'role', 'points', 'is_verified', 
        'is_active', 'last_online_display', 'account_created_display'
    )
    list_filter = ('role', 'is_verified', 'is_active', 'jurusan', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_editable = ('is_verified', 'points')
    readonly_fields = ('last_login', 'date_joined', 'last_online_display', 'account_created_display')
    
    def last_online_display(self, obj):
        """Menampilkan kapan user terakhir online"""
        # Prioritaskan last_activity jika ada
        if hasattr(obj, 'last_activity') and obj.last_activity:
            time_diff = timesince(obj.last_activity, timezone.now())
            status_color = '#28a745' if obj.is_online() else '#6c757d'
            status_text = 'Online' if obj.is_online() else f'{time_diff} yang lalu'
            
            return format_html(
                '<span style="color: {};" title="Aktivitas: {}">{}</span>',
                status_color,
                obj.last_activity.strftime('%d %B %Y, %H:%M'),
                status_text
            )
        elif obj.last_login:
            time_diff = timesince(obj.last_login, timezone.now())
            return format_html(
                '<span style="color: #6c757d;" title="Login: {}">{} yang lalu</span>',
                obj.last_login.strftime('%d %B %Y, %H:%M'),
                time_diff
            )
        else:
            return format_html('<span style="color: #999;">Belum pernah login</span>')
    
    last_online_display.short_description = _('Terakhir Online')
    last_online_display.admin_order_field = 'last_activity'
    
    def account_created_display(self, obj):
        """Menampilkan kapan akun dibuat"""
        if obj.date_joined:
            time_diff = timesince(obj.date_joined, timezone.now())
            return format_html(
                '<span title="{}">{} yang lalu</span>',
                obj.date_joined.strftime('%d %B %Y, %H:%M'),
                time_diff
            )
        else:
            return format_html('<span style="color: #999;">Tidak diketahui</span>')
    
    account_created_display.short_description = _('Akun Dibuat Pada')
    account_created_display.admin_order_field = 'date_joined'
    
    def get_form(self, request, obj=None, **kwargs):
        """Custom form untuk add/change user"""
        form = super().get_form(request, obj, **kwargs)
        if obj:  # Jika editing user yang sudah ada
            form.base_fields['password'].help_text = "Kosongkan jika tidak ingin mengubah password"
            form.base_fields['password'].required = False
        else:  # Jika menambah user baru
            form.base_fields['password'].help_text = "Masukkan password untuk user baru"
            form.base_fields['password'].required = True
        return form
    
    def get_readonly_fields(self, request, obj=None):
        """Menambahkan readonly fields berdasarkan kondisi"""
        readonly_fields = list(super().get_readonly_fields(request, obj))
        
        if obj:  # Jika editing existing user
            # Tambahkan field yang tidak boleh diedit untuk existing user
            readonly_fields.extend(['last_online_display', 'account_created_display'])
        
        return readonly_fields
    
    # Custom actions
    actions = ['verify_users', 'add_points', 'reset_points', 'export_users_csv']
    
    def verify_users(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} user berhasil diverifikasi.', messages.SUCCESS)
    verify_users.short_description = "Verifikasi user terpilih"
    
    def add_points(self, request, queryset):
        for user in queryset:
            user.points += 50
            user.save()
        self.message_user(request, f'{queryset.count()} user mendapat tambahan 50 poin.', messages.SUCCESS)
    add_points.short_description = "Tambah 50 poin"
    
    def reset_points(self, request, queryset):
        updated = queryset.update(points=0)
        self.message_user(request, f'{updated} user berhasil direset poinnya.', messages.SUCCESS)
    reset_points.short_description = "Reset poin menjadi 0"
    
    def export_users_csv(self, request, queryset):
        """Export selected users to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Username', 'Email', 'Role', 'Points', 'Verified', 
            'Last Login', 'Date Joined', 'Jurusan', 'Angkatan'
        ])
        
        for user in queryset:
            writer.writerow([
                user.username,
                user.email,
                user.get_role_display(),
                user.points,
                'Ya' if user.is_verified else 'Tidak',
                user.last_login.strftime('%d/%m/%Y %H:%M') if user.last_login else 'Belum pernah login',
                user.date_joined.strftime('%d/%m/%Y %H:%M') if user.date_joined else 'Tidak diketahui',
                user.jurusan,
                user.angkatan
            ])
        
        return response
    
    export_users_csv.short_description = "Export user terpilih ke CSV"

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active', 'thread_count_display', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('is_active', 'created_at')
    list_editable = ('is_active',)
    
    def thread_count_display(self, obj):
        """Menampilkan jumlah thread dalam kategori"""
        count = obj.get_thread_count()
        return format_html('<strong>{}</strong> thread', count)
    
    thread_count_display.short_description = _('Jumlah Thread')

class ThreadAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'author', 'category', 'views', 'comment_count_display',
        'is_pinned', 'is_locked', 'created_at'
    )
    list_filter = ('category', 'is_pinned', 'is_locked', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    list_editable = ('is_pinned', 'is_locked')
    list_per_page = 20
    
    def comment_count_display(self, obj):
        """Menampilkan jumlah komentar"""
        count = obj.get_comment_count()
        return format_html('<span class="badge">{}</span>', count)
    
    comment_count_display.short_description = _('Komentar')

class CommentAdmin(admin.ModelAdmin):
    list_display = ('short_content', 'author', 'thread', 'vote_score_display', 'created_at')
    search_fields = ('content', 'author__username', 'thread__title')
    list_filter = ('created_at', 'is_edited')
    list_per_page = 25

    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = "Content"
    
    def vote_score_display(self, obj):
        """Menampilkan score vote"""
        score = obj.get_vote_score()
        color = 'green' if score > 0 else 'red' if score < 0 else 'gray'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, score
        )
    vote_score_display.short_description = _('Vote Score')

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'short_message', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('user__username', 'message')
    list_per_page = 25
    
    def short_message(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    short_message.short_description = "Message"

class ReportAdmin(admin.ModelAdmin):
    list_display = (
        'reporter', 'report_type', 'target_display', 'is_resolved', 
        'resolved_by', 'created_at'
    )
    list_filter = ('report_type', 'is_resolved', 'created_at')
    search_fields = ('reporter__username', 'description')
    list_per_page = 20
    
    def target_display(self, obj):
        """Menampilkan target laporan (thread atau comment)"""
        if obj.thread:
            return format_html('Thread: <strong>{}</strong>', obj.thread.title[:30])
        elif obj.comment:
            return format_html('Comment: <strong>{}</strong>', obj.comment.content[:30])
        return '-'
    
    target_display.short_description = _('Target')

class VoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'comment', 'value', 'created_at')
    list_filter = ('value', 'created_at')
    search_fields = ('user__username', 'comment__content')

class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'thread', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'thread__title')

# Configure admin site
admin.site.site_header = "AgoraTalk Admin Panel"
admin.site.site_title = "AgoraTalk"
admin.site.index_title = "Welcome to AgoraTalk Administration"

# Register models
admin.site.register(User, UserAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Thread, ThreadAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Vote, VoteAdmin)
admin.site.register(Bookmark, BookmarkAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(Report, ReportAdmin)