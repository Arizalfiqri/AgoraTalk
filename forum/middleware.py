# forum/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class AdminUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Jika ini adalah request admin
        if request.path.startswith('/admin/'):
            # Cek apakah user adalah admin
            if 'admin_user_id' in request.session:
                from .models import AdminUser
                try:
                    admin_user = AdminUser.objects.using('admin_db').get(
                        id=request.session['admin_user_id']
                    )
                    request.admin_user = admin_user
                    request.user = admin_user  # Set sebagai user untuk admin interface
                except AdminUser.DoesNotExist:
                    # Session tidak valid, hapus
                    if 'admin_user_id' in request.session:
                        del request.session['admin_user_id']
                    if 'is_admin_user' in request.session:
                        del request.session['is_admin_user']
                    request.admin_user = None
            else:
                request.admin_user = None
                
            # Redirect ke admin login jika tidak ada admin user dan bukan halaman login
            if not request.admin_user and not request.path.endswith('/login/'):
                return HttpResponseRedirect(reverse('admin_login'))
        
        # Untuk request non-admin, pastikan tidak ada session admin yang tercampur
        elif not request.path.startswith('/admin/'):
            # Jika user biasa mencoba akses dengan session admin, bersihkan
            if request.session.get('is_admin_user', False):
                # Jangan hapus session admin jika user sedang navigasi normal
                # Hanya bersihkan jika benar-benar konflik
                pass
        
        return None

class SessionSeparationMiddleware(MiddlewareMixin):
    """Middleware untuk memisahkan session admin dan user biasa"""
    
    def process_request(self, request):
        # Tambahkan prefix untuk session admin
        if request.path.startswith('/admin/'):
            # Gunakan session key yang berbeda untuk admin
            original_session_key = request.session.session_key
            if original_session_key:
                request.session['session_key'] = f"admin_{original_session_key}"
        
        return None

class UserActivityMiddleware(MiddlewareMixin):
    """
    Middleware untuk melacak aktivitas user terakhir kali
    """
    
    def process_request(self, request):
        # Hanya update untuk user yang sudah login dan bukan admin request
        if (request.user.is_authenticated and 
            not request.path.startswith('/admin/') and
            not request.path.startswith('/static/') and
            not request.path.startswith('/media/')):
            
            # Cek apakah user adalah User model kita
            if hasattr(request.user, 'last_activity'):
                # Update last_activity setiap 5 menit untuk mengurangi database hits
                now = timezone.now()
                if (not hasattr(request.user, 'last_activity') or 
                    not request.user.last_activity or
                    (now - request.user.last_activity).total_seconds() > 300):  # 5 menit
                    
                    # Update last_activity tanpa memicu signal
                    User.objects.filter(pk=request.user.pk).update(
                        last_activity=now
                    )
        
        return None