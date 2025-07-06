from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import timezone

# Custom User dengan fitur tambahan
class User(AbstractUser):
    ROLE_CHOICES = [
        ('mahasiswa', _('Mahasiswa')),
        ('admin', _('Admin')), 
    ]
    
    bio = models.TextField(verbose_name=_("Bio"), blank=True, max_length=500)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name=_("Avatar"))
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='mahasiswa', verbose_name=_("Role"))
    jurusan = models.CharField(max_length=100, blank=True, verbose_name=_("Jurusan"))
    angkatan = models.CharField(max_length=4, blank=True, verbose_name=_("Angkatan"))
    instagram = models.CharField(max_length=100, blank=True, verbose_name=_("Instagram"))
    linkedin = models.CharField(max_length=100, blank=True, verbose_name=_("LinkedIn"))
    points = models.IntegerField(default=0, verbose_name=_("Poin"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Terverifikasi"))
    
    # Fix related_name conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to.'),
        related_name='forum_user_set',
        related_query_name='forum_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='forum_user_set',
        related_query_name='forum_user',
    )
    
    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        # Gunakan database pengguna
        app_label = 'forum'
    
    def __str__(self):
        return self.username
    
    def get_badge(self):
        """Mendapatkan badge berdasarkan poin"""
        if self.points >= 1000:
            return {'name': 'Expert', 'class': 'badge-warning'}
        elif self.points >= 500:
            return {'name': 'Advanced', 'class': 'badge-info'}
        elif self.points >= 100:
            return {'name': 'Active', 'class': 'badge-success'}
        else:
            return {'name': 'Newbie', 'class': 'badge-secondary'}
    
    def get_thread_count(self):
        """Mendapatkan jumlah thread yang dibuat user"""
        return self.threads.count()
    
    def get_comment_count(self):
        """Mendapatkan jumlah komentar yang dibuat user"""
        return self.comments.count()
        
class AdminUser(AbstractUser):
    """Model Admin User terpisah"""
    employee_id = models.CharField(max_length=20, unique=True, verbose_name=_("Employee ID"))
    department = models.CharField(max_length=100, blank=True, verbose_name=_("Department"))
    
    # Fix related_name conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to.'),
        related_name='admin_user_set',
        related_query_name='admin_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='admin_user_set',
        related_query_name='admin_user',
    )
    
    def get_session_auth_hash(self):
        """Override untuk memisahkan session admin"""
        return f"admin_{super().get_session_auth_hash()}"
    
    class Meta:
        verbose_name = _("Admin User")
        verbose_name_plural = _("Admin Users")
        app_label = 'forum'
        db_table = 'forum_adminuser'
    
    def __str__(self):
        return f"Admin: {self.username}"

# Kategori Forum
class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Nama Kategori"))
    description = models.TextField(verbose_name=_("Deskripsi"), blank=True)
    icon = models.CharField(max_length=50, blank=True, verbose_name=_("Icon Class"))
    color = models.CharField(max_length=7, default='#007bff', verbose_name=_("Warna"))
    is_active = models.BooleanField(default=True, verbose_name=_("Aktif"))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Kategori")
        verbose_name_plural = _("Kategori")
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_thread_count(self):
        return self.thread_set.count()

# Thread / Topik Diskusi
class Thread(models.Model):
    title = models.CharField(max_length=255, verbose_name=_("Judul"))
    content = models.TextField(verbose_name=_("Isi"))
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='threads', verbose_name=_("Penulis"))
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name=_("Kategori"))
    tags = models.CharField(max_length=200, blank=True, verbose_name=_("Tags"))
    is_pinned = models.BooleanField(default=False, verbose_name=_("Disematkan"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Dikunci"))
    views = models.PositiveIntegerField(default=0, verbose_name=_("Dilihat"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Waktu Dibuat"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Terakhir Diperbarui"))
    
    class Meta:
        verbose_name = _("Thread")
        verbose_name_plural = _("Thread")
        ordering = ['-is_pinned', '-updated_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('thread_detail', kwargs={'pk': self.pk})
    
    def get_comment_count(self):
        return self.comments.count()
    
    def get_last_activity(self):
        last_comment = self.comments.order_by('-created_at').first()
        return last_comment.created_at if last_comment else self.created_at

# Komentar (termasuk reply)
class Comment(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='comments', verbose_name=_("Thread"))
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments', verbose_name=_("Penulis"))
    content = models.TextField(verbose_name=_("Isi Komentar"))
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies', verbose_name=_("Balasan ke"))
    is_edited = models.BooleanField(default=False, verbose_name=_("Diedit"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Waktu Dibuat"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Terakhir Diperbarui"))
    
    class Meta:
        verbose_name = _("Komentar")
        verbose_name_plural = _("Komentar")
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.author.username} - {self.content[:30]}"
    
    def get_vote_score(self):
        return self.votes.aggregate(
            score=models.Sum('value')
        )['score'] or 0
    
    def get_replies_count(self):
        return self.replies.count()

# Vote (upvote/downvote komentar)
class Vote(models.Model):
    VOTE_TYPE = (
        (1, _('Upvote')),
        (-1, _('Downvote')),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("Pengguna"))
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='votes', verbose_name=_("Komentar"))
    value = models.SmallIntegerField(choices=VOTE_TYPE, verbose_name=_("Nilai Suara"))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Suara")
        verbose_name_plural = _("Suara")
        unique_together = ('user', 'comment')
    
    def __str__(self):
        return f"{self.user.username} voted {self.value} on comment {self.comment.id}"

# Bookmark Thread
class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'thread')
    
    def __str__(self):
        return f"{self.user.username} bookmarked {self.thread.title}"

# Notifikasi
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('reply', _('Balasan')),
        ('mention', _('Sebutan')),
        ('vote', _('Vote')),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.CharField(max_length=255)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"
    
class Report(models.Model):
    REPORT_TYPES = [
        ('spam', _('Spam')),
        ('inappropriate', _('Konten Tidak Pantas')),
        ('harassment', _('Pelecehan')),
        ('other', _('Lainnya')),
    ]
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_resolved')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)