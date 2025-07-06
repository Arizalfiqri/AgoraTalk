# admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, AdminUser, Category, Thread, Comment, Vote, Bookmark, Notification, Report
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta
from django.urls import path
from django.contrib.admin import SimpleListFilter
from django.http import HttpResponseRedirect
from django.contrib import messages

class CustomAdminSite(AdminSite):
    site_header = 'Portal Forum Mahasiswa Admin'
    site_title = 'Forum Admin'
    index_title = 'Dashboard Analytics'
    login_template = 'admin/login.html'
    
    def login(self, request, extra_context=None):
        """Override login untuk menggunakan AdminUser"""
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            try:
                admin_user = AdminUser.objects.using('admin_db').get(username=username)
                if admin_user.check_password(password):
                    # Set session admin
                    request.session['admin_user_id'] = admin_user.id
                    request.session['is_admin_user'] = True
                    return HttpResponseRedirect(request.GET.get('next', '/admin/'))
                else:
                    messages.error(request, 'Username atau password salah.')
            except AdminUser.DoesNotExist:
                messages.error(request, 'Admin tidak ditemukan.')
        
        return super().login(request, extra_context)
    
    def logout(self, request, extra_context=None):
        """Override logout untuk menghapus session admin"""
        if 'admin_user_id' in request.session:
            del request.session['admin_user_id']
        if 'is_admin_user' in request.session:
            del request.session['is_admin_user']
        
        return super().logout(request, extra_context)
    
    def has_permission(self, request):
        """Cek permission khusus admin"""
        return request.session.get('is_admin_user', False)

# Ganti admin site default
admin_site = CustomAdminSite(name='forum_admin')

@admin.register(AdminUser, site=admin_site)
class AdminUserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'employee_id', 'department', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'department')
    fieldsets = BaseUserAdmin.fieldsets + (
        (_('Admin Info'), {
            'fields': ('employee_id', 'department')
        }),
    )
    
    def get_queryset(self, request):
        # Gunakan admin database
        return super().get_queryset(request).using('admin_db')
    
    def save_model(self, request, obj, form, change):
        # Simpan ke admin database
        obj.save(using='admin_db')
    
    def delete_model(self, request, obj):
        # Hapus dari admin database
        obj.delete(using='admin_db')

# Register User biasa (untuk admin lihat data pengguna)
@admin.register(User, site=admin_site)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'points', 'thread_count', 'comment_count', 'is_verified', 'is_active')
    list_filter = ('role', 'is_verified', 'is_active', 'angkatan', 'jurusan')
    actions = ['verify_users', 'add_points', 'reset_points']
    
    # Readonly untuk admin - tidak bisa edit user biasa
    readonly_fields = ('username', 'email', 'date_joined', 'last_login')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        (_('Info Tambahan'), {
            'fields': ('bio', 'avatar', 'role', 'jurusan', 'angkatan', 'instagram', 'linkedin', 'points', 'is_verified')
        }),
    )
    
    def get_queryset(self, request):
        # Gunakan database default untuk melihat data pengguna
        return User.objects.using('default').annotate(
            thread_count=Count('threads'),
            comment_count=Count('comments')
        )
    
    def thread_count(self, obj):
        """Menampilkan jumlah thread yang dibuat user"""
        return obj.get_thread_count()
    thread_count.short_description = 'Jumlah Thread'
    
    def comment_count(self, obj):
        """Menampilkan jumlah komentar yang dibuat user"""
        return obj.get_comment_count()
    comment_count.short_description = 'Jumlah Komentar'
    
    def has_add_permission(self, request):
        # Admin tidak bisa menambah user biasa
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Admin tidak bisa hapus user biasa, hanya nonaktifkan
        return False
    
    def verify_users(self, request, queryset):
        """Action untuk verifikasi user"""
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} user berhasil diverifikasi.')
    verify_users.short_description = "Verifikasi user terpilih"
    
    def add_points(self, request, queryset):
        """Action untuk menambah poin user"""
        for user in queryset:
            user.points += 50
            user.save()
        self.message_user(request, f'{queryset.count()} user mendapat tambahan 50 poin.')
    add_points.short_description = "Tambah 50 poin"
    
    def reset_points(self, request, queryset):
        """Action untuk reset poin user"""
        updated = queryset.update(points=0)
        self.message_user(request, f'{updated} user berhasil direset poinnya.')
    reset_points.short_description = "Reset poin menjadi 0"

# Custom filter untuk role
class RoleFilter(SimpleListFilter):
    title = 'Role User'
    parameter_name = 'user_role'
    
    def lookups(self, request, model_admin):
        return User.ROLE_CHOICES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(author__role=self.value())
        return queryset

# Inline classes (HARUS DIDEFINISIKAN SEBELUM digunakan)
class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ('author', 'content', 'created_at')
    readonly_fields = ('created_at',)
    raw_id_fields = ('author',)


@admin.register(Category, site=admin_site)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active', 'thread_count', 'created_at')
    search_fields = ('name',)
    list_filter = ('is_active', 'created_at')
    list_editable = ('is_active',)
    
    def thread_count(self, obj):
        return obj.get_thread_count()
    thread_count.short_description = 'Jumlah Thread'

@admin.register(Thread, site=admin_site)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'views', 'comment_count', 'is_pinned', 'is_locked', 'created_at')
    list_filter = ('category', 'is_pinned', 'is_locked', 'created_at', RoleFilter)
    search_fields = ('title', 'content', 'author__username', 'tags')
    list_editable = ('is_pinned', 'is_locked')
    actions = ['pin_threads', 'unpin_threads', 'lock_threads', 'unlock_threads']
    inlines = [CommentInline]
    raw_id_fields = ('author', 'category')
    
    def comment_count(self, obj):
        return obj.comments.count()
    comment_count.short_description = 'Komentar'
    
    def pin_threads(self, request, queryset):
        updated = queryset.update(is_pinned=True)
        self.message_user(request, f'{updated} thread berhasil disematkan.')
    pin_threads.short_description = "Sematkan thread terpilih"
    
    def unpin_threads(self, request, queryset):
        updated = queryset.update(is_pinned=False)
        self.message_user(request, f'{updated} thread berhasil dihapus dari sematan.')
    unpin_threads.short_description = "Hapus sematan thread"
    
    def lock_threads(self, request, queryset):
        updated = queryset.update(is_locked=True)
        self.message_user(request, f'{updated} thread berhasil dikunci.')
    lock_threads.short_description = "Kunci thread terpilih"
    
    def unlock_threads(self, request, queryset):
        updated = queryset.update(is_locked=False)
        self.message_user(request, f'{updated} thread berhasil dibuka.')
    unlock_threads.short_description = "Buka kunci thread"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            comment_count=Count('comments'),
            vote_count=Count('comments__votes')
        )

@admin.register(Comment, site=admin_site)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('short_content', 'author', 'thread', 'parent', 'vote_score', 'created_at')
    search_fields = ('content', 'author__username', 'thread__title')
    list_filter = ('created_at', 'is_edited')
    raw_id_fields = ('author', 'thread', 'parent')

    def short_content(self, obj):
        return obj.content[:40] + '...' if len(obj.content) > 40 else obj.content
    short_content.short_description = _("Isi Singkat")
    
    def vote_score(self, obj):
        return obj.get_vote_score()
    vote_score.short_description = 'Skor Vote'

@admin.register(Vote, site=admin_site)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'comment', 'value', 'created_at')
    list_filter = ('value', 'created_at')
    search_fields = ('user__username', 'comment__content')
    raw_id_fields = ('user', 'comment')

@admin.register(Bookmark, site=admin_site)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'thread', 'created_at')
    search_fields = ('user__username', 'thread__title')
    raw_id_fields = ('user', 'thread')

@admin.register(Notification, site=admin_site)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'message', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('user__username', 'message')
    actions = ['mark_as_read']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notifikasi ditandai sudah dibaca.')
    mark_as_read.short_description = "Tandai sebagai sudah dibaca"

@admin.register(Report, site=admin_site)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'report_type', 'target_content', 'is_resolved', 'created_at')
    list_filter = ('report_type', 'is_resolved', 'created_at')
    actions = ['mark_resolved']
    
    def target_content(self, obj):
        if obj.thread:
            return f"Thread: {obj.thread.title[:30]}"
        elif obj.comment:
            return f"Comment: {obj.comment.content[:30]}"
        return "Unknown"
    target_content.short_description = 'Target'
    
    def mark_resolved(self, request, queryset):
        queryset.update(is_resolved=True, resolved_by=request.user, resolved_at=timezone.now())
        self.message_user(request, f'{queryset.count()} laporan telah ditandai selesai.')
    mark_resolved.short_description = "Tandai sebagai selesai"