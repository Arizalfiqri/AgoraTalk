from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('mahasiswa', _('Mahasiswa')),
        ('admin', _('Admin')), 
        ('super_admin', _('Super Admin')),  # Tambahkan role baru
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
    
    # Tambahan field untuk admin
    employee_id = models.CharField(max_length=20, blank=True, verbose_name=_("Employee ID"))
    department = models.CharField(max_length=100, blank=True, verbose_name=_("Department"))
    
    # Field untuk tracking aktivitas user
    last_activity = models.DateTimeField(null=True, blank=True, verbose_name=_("Aktivitas Terakhir"))
    
    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        app_label = 'forum'
    
    def __str__(self):
        return self.username
    
    def is_admin_user(self):
        """Cek apakah user adalah admin"""
        return self.role in ['admin', 'super_admin']
    
    def is_super_admin(self):
        """Cek apakah user adalah super admin"""
        return self.role == 'super_admin'
    
    def is_online(self):
        """Cek apakah user sedang online (aktif dalam 5 menit terakhir)"""
        if self.last_activity:
            from django.utils import timezone
            return (timezone.now() - self.last_activity).total_seconds() < 300  # 5 menit
        return False
    
    def get_online_status(self):
        """Mendapatkan status online user"""
        if self.is_online():
            return "Online"
        elif self.last_activity:
            from django.utils.timesince import timesince
            from django.utils import timezone
            return f"Terakhir aktif {timesince(self.last_activity, timezone.now())} yang lalu"
        elif self.last_login:
            from django.utils.timesince import timesince
            from django.utils import timezone
            return f"Terakhir login {timesince(self.last_login, timezone.now())} yang lalu"
        else:
            return "Belum pernah login"
    
    def get_badge(self):
        """Mendapatkan badge berdasarkan poin"""
        if self.points >= 1000:
            return {'name': 'Glory', 'class': 'badge-warning'}
        elif self.points >= 500:
            return {'name': 'Mythic', 'class': 'badge-info'}
        elif self.points >= 100:
            return {'name': 'Legend', 'class': 'badge-success'}
        else:
            return {'name': 'Master', 'class': 'badge-secondary'}
    
    def get_badge_progress(self):
        """Mendapatkan informasi progress badge"""
        current_points = self.points
        
        if current_points >= 1000:
            return {
                'current_badge': 'Glory',
                'next_badge': None,
                'points_needed': 0,
                'progress_percentage': 100,
                'is_max_level': True
            }
        elif current_points >= 500:
            return {
                'current_badge': 'Mythic',
                'next_badge': 'Glory',
                'points_needed': 1000 - current_points,
                'progress_percentage': round((current_points - 500) / (1000 - 500) * 100, 1),
                'is_max_level': False
            }
        elif current_points >= 100:
            return {
                'current_badge': 'Legend',
                'next_badge': 'Mythic',
                'points_needed': 500 - current_points,
                'progress_percentage': round((current_points - 100) / (500 - 100) * 100, 1),
                'is_max_level': False
            }
        else:
            return {
                'current_badge': 'Master',
                'next_badge': 'Legend',
                'points_needed': 100 - current_points,
                'progress_percentage': round(current_points / 100 * 100, 1),
                'is_max_level': False
            }
    
    def get_all_badge_requirements(self):
        """Mendapatkan semua requirement badge"""
        return [
            {'name': 'Master', 'min_points': 0, 'class': 'badge-secondary', 'icon': 'fas fa-user'},
            {'name': 'Legend', 'min_points': 100, 'class': 'badge-success', 'icon': 'fas fa-star'},
            {'name': 'Mythic', 'min_points': 500, 'class': 'badge-info', 'icon': 'fas fa-crown'},
            {'name': 'Glory', 'min_points': 1000, 'class': 'badge-warning', 'icon': 'fas fa-trophy'}
        ]
    
    def get_thread_count(self):
        """Mendapatkan jumlah thread yang dibuat user"""
        return self.threads.count()
    
    def get_comment_count(self):
        """Mendapatkan jumlah komentar yang dibuat user"""
        return self.comments.count()

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
    image = models.ImageField(upload_to='thread_images/', null=True, blank=True, verbose_name=_("Gambar"))
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
    
    def get_vote_score(self):
        """Mendapatkan total score vote untuk thread"""
        return self.votes.aggregate(
            score=models.Sum('value')
        )['score'] or 0
    
    def get_likes_count(self):
        """Mendapatkan jumlah like thread"""
        return self.votes.filter(value=1).count()
    
    def get_dislikes_count(self):
        """Mendapatkan jumlah dislike thread"""
        return self.votes.filter(value=-1).count()
    
    def tags_list(self):
        """Mendapatkan list tags yang telah dipisahkan"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []

# Komentar (termasuk reply)
class Comment(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='comments', verbose_name=_("Thread"))
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='comments', verbose_name=_("Penulis"))
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
        author_name = self.author.username if self.author else "Pengguna Terhapus"
        return f"{author_name} - {self.content[:30]}"
    
    def get_vote_score(self):
        return self.votes.aggregate(
            score=models.Sum('value')
        )['score'] or 0
    
    def get_likes_count(self):
        """Mendapatkan jumlah like pada komentar (hanya vote dengan value=1)"""
        return self.votes.filter(value=1).count()
    
    def get_replies_count(self):
        return self.replies.count()
    
    def user_has_voted(self, user):
        """Cek apakah user sudah vote komentar ini"""
        if user.is_authenticated:
            return self.votes.filter(user=user).exists()
        return False

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

# Vote untuk Thread
class ThreadVote(models.Model):
    VOTE_TYPE = (
        (1, _('Like')),
        (-1, _('Dislike')),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("Pengguna"))
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='votes', verbose_name=_("Thread"))
    value = models.SmallIntegerField(choices=VOTE_TYPE, verbose_name=_("Nilai Suara"))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Suara Thread")
        verbose_name_plural = _("Suara Thread")
        unique_together = ('user', 'thread')
    
    def __str__(self):
        return f"{self.user.username} voted {self.value} on thread {self.thread.title}"

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