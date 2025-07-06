# admin_views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST
from django import forms
from .models import AdminUser, User
from django.contrib.auth.forms import UserCreationForm

class AdminRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Konfirmasi Password', widget=forms.PasswordInput)
    
    class Meta:
        model = AdminUser
        fields = ['username', 'email', 'employee_id', 'department']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Password tidak cocok")
        return password2
    
    def save(self, commit=True):
        admin_user = super().save(commit=False)
        admin_user.set_password(self.cleaned_data["password1"])
        admin_user.is_staff = True
        admin_user.is_superuser = True
        if commit:
            admin_user.save(using='admin_db')
        return admin_user

def admin_register(request):
    """View untuk registrasi admin - hanya bisa diakses oleh superuser"""
    # Cek apakah user sudah login sebagai admin
    if not request.session.get('is_admin_user', False):
        return HttpResponseForbidden("Akses ditolak. Hanya admin yang bisa mendaftar admin baru.")
    
    if request.method == 'POST':
        form = AdminRegistrationForm(request.POST)
        if form.is_valid():
            try:
                admin_user = form.save()
                messages.success(request, f'Admin {admin_user.username} berhasil dibuat!')
                return redirect('admin:index')
            except Exception as e:
                messages.error(request, f'Gagal membuat admin: {str(e)}')
    else:
        form = AdminRegistrationForm()
    
    return render(request, 'admin/register_admin.html', {'form': form})

def admin_login(request):
    """View untuk login admin"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            # Cari admin user
            admin_user = AdminUser.objects.using('admin_db').get(username=username)
            if admin_user.check_password(password):
                # Set session admin
                request.session['admin_user_id'] = admin_user.id
                request.session['is_admin_user'] = True
                request.session['admin_username'] = admin_user.username
                
                messages.success(request, f'Selamat datang, {admin_user.username}!')
                return redirect('admin:index')
            else:
                messages.error(request, 'Username atau password salah.')
        except AdminUser.DoesNotExist:
            messages.error(request, 'Admin tidak ditemukan.')
    
    return render(request, 'admin/login.html')

def admin_logout(request):
    """View untuk logout admin"""
    # Hapus session admin
    admin_username = request.session.get('admin_username', 'Admin')
    
    if 'admin_user_id' in request.session:
        del request.session['admin_user_id']
    if 'is_admin_user' in request.session:
        del request.session['is_admin_user']
    if 'admin_username' in request.session:
        del request.session['admin_username']
    
    messages.success(request, f'Sampai jumpa, {admin_username}!')
    return redirect('admin_login')

# Update view register untuk user biasa
def register(request):
    """View untuk registrasi user biasa"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Pastikan ini bukan registrasi admin
            user = form.save(commit=False)
            user.is_active = True
            user.role = 'mahasiswa'  # Set role default
            user.save(using='default')  # Simpan ke database default
            
            # Auto login untuk user biasa
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            
            # Authenticate dengan backend user biasa
            authenticated_user = authenticate(
                request=request,
                username=username,
                password=password,
                backend='forum.views.UserAuthenticationBackend'
            )
            
            if authenticated_user:
                auth_login(request, authenticated_user)
                messages.success(request, 'Registrasi berhasil! Selamat datang!')
                return redirect('dashboard')
            else:
                messages.success(request, 'Registrasi berhasil! Silakan login.')
                return redirect('login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    jurusan = forms.CharField(max_length=100, required=False)
    angkatan = forms.CharField(max_length=4, required=False)
    
    class Meta:
        model = User
        fields = ("username", "email", "jurusan", "angkatan", "password1", "password2")
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.jurusan = self.cleaned_data["jurusan"]
        user.angkatan = self.cleaned_data["angkatan"]
        user.role = 'mahasiswa'
        if commit:
            user.save(using='default')
        return user