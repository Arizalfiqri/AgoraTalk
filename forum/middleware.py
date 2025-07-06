# forum/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages

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
                request.session['session_key'] =  f"admin_{original_session_key}"
        
        return None