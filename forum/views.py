from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Count, Sum, Max  # Tambahkan Max import
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import Thread, Category, Comment, Vote, Bookmark, Notification
import json
from django.contrib.auth.backends import ModelBackend
from .models import User, AdminUser
from django.core.mail import send_mail
from django.conf import settings
import random
import string
from django.utils import timezone
from datetime import timedelta
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.models import Session

def test_template(request):
    return render(request, "forum/analytics.html")

class AdminUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Cek apakah ini request admin
        if request.path.startswith('/admin/'):
            # Gunakan session khusus admin
            request.session.set_test_cookie()
        
        response = self.get_response(request)
        return response

class UserAuthenticationBackend(ModelBackend):
    """Custom authentication backend untuk User biasa"""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

class AdminAuthenticationBackend(ModelBackend):
    """Custom authentication backend untuk Admin"""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Hanya untuk admin login
        if request and request.path.startswith('/admin/'):
            try:
                admin_user = AdminUser.objects.using('admin_db').get(username=username)
                if admin_user.check_password(password):
                    return admin_user
            except AdminUser.DoesNotExist:
                return None
        return None
    
    def get_user(self, user_id):
        try:
            return AdminUser.objects.using('admin_db').get(pk=user_id)
        except AdminUser.DoesNotExist:
            return None


# Forms
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    jurusan = forms.CharField(max_length=100, required=False)
    angkatan = forms.CharField(max_length=4, required=False)
    
    class Meta:
        model = User
        fields = ("username", "email", "jurusan", "angkatan", "password1", "password2")

class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ['title', 'content', 'category', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Judul thread...'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Tulis konten thread...'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'tag1, tag2, tag3...'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Tulis komentar...'}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'bio', 'jurusan', 'angkatan', 'instagram', 'linkedin', 'avatar']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'jurusan': forms.TextInput(attrs={'class': 'form-control'}),
            'angkatan': forms.TextInput(attrs={'class': 'form-control'}),
            'instagram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '@username'}),
            'linkedin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'linkedin.com/in/username'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }

# Views
def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))

def home(request):
    # Thread populer (berdasarkan views dan komentar)
    popular_threads = Thread.objects.annotate(
        comment_count=Count('comments')
    ).order_by('-views', '-comment_count')[:5]
    
    # Thread terbaru
    recent_threads = Thread.objects.select_related('author', 'category').order_by('-created_at')[:10]
    
    # Kategori dengan jumlah thread
    categories = Category.objects.filter(is_active=True).annotate(
        thread_count=Count('thread')
    ).order_by('name')
    
    # Statistik
    stats = {
        'total_threads': Thread.objects.count(),
        'total_users': User.objects.count(),
        'total_comments': Comment.objects.count(),
    }
    
    context = {
        'popular_threads': popular_threads,
        'recent_threads': recent_threads,
        'categories': categories,
        'stats': stats,
    }
    return render(request, 'forum/home.html', context)

def thread_list(request, category_slug=None):
    threads = Thread.objects.select_related('author', 'category').annotate(
        comment_count=Count('comments'),
        last_activity=Max('comments__created_at')
    )
    
    category = None
    if category_slug:
        category = get_object_or_404(Category, name__iexact=category_slug.replace('-', ' '))
        threads = threads.filter(category=category)
    
    # Sorting
    sort = request.GET.get('sort', 'recent')
    if sort == 'popular':
        threads = threads.order_by('-views', '-comment_count')
    elif sort == 'most_commented':
        threads = threads.order_by('-comment_count')
    else:  # recent
        threads = threads.order_by('-is_pinned', '-updated_at')
    
    # Process tags for each thread
    threads_list = list(threads)
    for thread in threads_list:
        if thread.tags:
            thread.tags_list = [tag.strip() for tag in thread.tags.split(',') if tag.strip()]
        else:
            thread.tags_list = []
    
    # Pagination
    paginator = Paginator(threads_list, 15)
    page_number = request.GET.get('page')
    threads = paginator.get_page(page_number)
    
    context = {
        'threads': threads,
        'category': category,
        'sort': sort,
    }
    return render(request, 'forum/thread_list.html', context)

def thread_detail(request, pk):
    thread = get_object_or_404(Thread.objects.select_related('author', 'category'), pk=pk)
    
    # Tambah view count
    thread.views += 1
    thread.save(update_fields=['views'])
    
    # Process tags
    if thread.tags:
        thread.tags_list = [tag.strip() for tag in thread.tags.split(',') if tag.strip()]
    else:
        thread.tags_list = []
    
    # Komentar dengan replies
    comments = Comment.objects.filter(thread=thread, parent=None).select_related('author').prefetch_related('replies__author')
    
    # Form komentar
    comment_form = CommentForm()
    
    # Cek bookmark status
    is_bookmarked = False
    if request.user.is_authenticated:
        is_bookmarked = Bookmark.objects.filter(user=request.user, thread=thread).exists()
    
    context = {
        'thread': thread,
        'comments': comments,
        'comment_form': comment_form,
        'is_bookmarked': is_bookmarked,
    }
    return render(request, 'forum/thread_detail.html', context)

@login_required
def create_thread(request):
    if request.method == 'POST':
        form = ThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.author = request.user
            thread.save()
            
            # Tambah poin untuk user
            request.user.points += 10
            request.user.save()
            
            messages.success(request, 'Thread berhasil dibuat!')
            return redirect('thread_detail', pk=thread.pk)
    else:
        form = ThreadForm()
    
    return render(request, 'forum/create_thread.html', {'form': form})

@login_required
@require_POST
def add_comment(request, thread_pk):
    thread = get_object_or_404(Thread, pk=thread_pk)
    
    if thread.is_locked and not request.user.is_staff:
        messages.error(request, "Thread ini sudah dikunci.")
        return redirect('thread_detail', pk=thread_pk)
    
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.thread = thread
        comment.author = request.user
        
        # Handle reply
        parent_id = request.POST.get('parent_id')
        if parent_id:
            try:
                comment.parent = get_object_or_404(Comment, pk=parent_id)
            except:
                pass  # Jika parent tidak ditemukan, jadikan komentar biasa
        
        comment.save()
        
        # Tambah poin untuk user
        request.user.points += 5
        request.user.save()
        
        # Update thread updated_at
        thread.updated_at = timezone.now()
        thread.save()
        
        messages.success(request, 'Komentar berhasil ditambahkan! Anda mendapat 5 poin.')
        
        # Redirect ke thread detail dengan anchor ke komentar baru
        return redirect('thread_detail', pk=thread_pk)
    else:
        messages.error(request, 'Gagal menambahkan komentar. Silakan coba lagi.')
    
    return redirect('thread_detail', pk=thread_pk)

@login_required
@require_POST
def vote_comment(request, comment_pk):
    comment = get_object_or_404(Comment, pk=comment_pk)
    value = int(request.POST.get('value'))  # 1 or -1
    
    if value not in [1, -1]:
        return JsonResponse({'error': 'Invalid vote value'})
    
    vote, created = Vote.objects.get_or_create(
        user=request.user, 
        comment=comment,
        defaults={'value': value}
    )
    
    if not created:
        if vote.value == value:
            # Remove vote if same value
            vote.delete()
            vote_removed = True
        else:
            # Update vote value
            vote.value = value
            vote.save()
            vote_removed = False
    else:
        vote_removed = False
    
    # Calculate new score
    score = comment.get_vote_score()
    
    return JsonResponse({
        'score': score,
        'vote_removed': vote_removed,
        'user_vote': None if vote_removed else value
    })

@login_required
def toggle_bookmark(request, thread_pk):
    thread = get_object_or_404(Thread, pk=thread_pk)
    bookmark, created = Bookmark.objects.get_or_create(user=request.user, thread=thread)
    
    if not created:
        bookmark.delete()
        bookmarked = False
    else:
        bookmarked = True
    
    if request.headers.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        return JsonResponse({'bookmarked': bookmarked})
    
    return redirect('thread_detail', pk=thread_pk)

def search(request):
    query = request.GET.get('q', '')
    category_filter = request.GET.get('category', '')
    sort = request.GET.get('sort', 'recent')
    
    threads = Thread.objects.select_related('author', 'category')
    
    if query:
        threads = threads.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query) |
            Q(author__username__icontains=query) |
            Q(tags__icontains=query)
        )
    
    if category_filter:
        threads = threads.filter(category__name=category_filter)
    
    # Sorting
    if sort == 'popular':
        threads = threads.order_by('-views')
    elif sort == 'most_commented':
        threads = threads.annotate(comment_count=Count('comments')).order_by('-comment_count')
    else:
        threads = threads.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(threads, 10)
    page_number = request.GET.get('page')
    threads = paginator.get_page(page_number)
    
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'threads': threads,
        'query': query,
        'category_filter': category_filter,
        'sort': sort,
        'categories': categories,
    }
    return render(request, 'forum/search.html', context)

@login_required
def dashboard(request):
    user = request.user
    
    # User stats
    user_threads = Thread.objects.filter(author=user).order_by('-created_at')[:5]
    user_comments = Comment.objects.filter(author=user).select_related('thread').order_by('-created_at')[:5]
    bookmarked_threads = Thread.objects.filter(bookmarks__user=user).order_by('-bookmarks__created_at')[:5]
    
    # Notifications
    notifications = Notification.objects.filter(user=user, is_read=False).order_by('-created_at')[:10]
    
    stats = {
        'total_threads': Thread.objects.filter(author=user).count(),
        'total_comments': Comment.objects.filter(author=user).count(),
        'total_votes_received': Vote.objects.filter(comment__author=user).aggregate(Sum('value'))['value__sum'] or 0,
        'bookmarks_count': Bookmark.objects.filter(user=user).count(),
    }
    
    context = {
        'user_threads': user_threads,
        'user_comments': user_comments,
        'bookmarked_threads': bookmarked_threads,
        'notifications': notifications,
        'stats': stats,
    }
    return render(request, 'forum/home.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil berhasil diperbarui!')
            return redirect('dashboard')
    else:
        form = ProfileForm(instance=request.user)
    
    return render(request, 'forum/edit_profile.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Cek apakah ini registrasi admin (bisa berdasarkan parameter atau form field)
            is_admin = request.POST.get('is_admin', False)
            
            if is_admin:
                # Registrasi admin (harus ada validasi khusus)
                if not request.user.is_superuser:
                    messages.error(request, 'Anda tidak memiliki akses untuk membuat admin.')
                    return render(request, 'registration/register.html', {'form': form})
                
                # Buat AdminUser
                admin_user = AdminUser.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password1'],
                    employee_id=request.POST.get('employee_id', ''),
                    department=request.POST.get('department', ''),
                    is_staff=True
                )
                admin_user.save(using='admin_db')
                messages.success(request, 'Admin berhasil dibuat!')
                return redirect('admin:index')
            else:
                # Registrasi user biasa (kode existing)
                # ... kode verifikasi email existing ...
                user = form.save()
                user.is_active = True
                user.save(using='default')
                
                # Auto login untuk user biasa
                new_user = authenticate(
                    request=request,
                    username=form.cleaned_data['username'],
                    password=form.cleaned_data['password1']
                )
                if new_user:
                    auth_login(request, new_user)
                    return redirect('dashboard')

@require_POST
def send_verification_code(request):
    email = request.POST.get('email')
    
    if not email:
        return JsonResponse({'error': 'Email is required'})
    
    # Validasi format email
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({'error': 'Invalid email format'})
    
    # Check if email already exists
    if User.objects.filter(email=email).exists():
        return JsonResponse({'error': 'Email sudah terdaftar'})
    
    # Generate verification code
    code = generate_verification_code()
    
    # Store in session with expiration
    request.session[f'verification_code_{email}'] = {
        'code': code,
        'expires': (timezone.now() + timedelta(minutes=10)).isoformat()
    }
    
    # Send email
    try:
        send_mail(
            'Kode Verifikasi AgoraTalk',
            f'Kode verifikasi Anda adalah: {code}\n\nKode ini berlaku selama 10 menit.',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        return JsonResponse({'success': True, 'message': 'Kode verifikasi berhasil dikirim'})
    except Exception as e:
        return JsonResponse({'error': 'Gagal mengirim email. Silakan coba lagi.'})
    
    # Tambahkan view untuk AJAX request dari frontend
@require_POST
def ajax_send_verification_code(request):
    """
    AJAX endpoint untuk mengirim kode verifikasi
    Digunakan oleh JavaScript di frontend
    """
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'})
    
    email = request.POST.get('email')
    
    if not email:
        return JsonResponse({'error': 'Email diperlukan'})
    
    # Validasi format email
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({'error': 'Format email tidak valid'})
    
    # Check if email already exists
    if User.objects.filter(email=email).exists():
        return JsonResponse({'error': 'Email sudah terdaftar'})
    
    # Check cooldown (prevent spam)
    cooldown_key = f'verification_cooldown_{email}'
    if cooldown_key in request.session:
        cooldown_data = request.session[cooldown_key]
        cooldown_expires = timezone.datetime.fromisoformat(cooldown_data['expires'])
        if timezone.now() < cooldown_expires:
            remaining_seconds = int((cooldown_expires - timezone.now()).total_seconds())
            return JsonResponse({
                'error': f'Silakan tunggu {remaining_seconds} detik sebelum mengirim ulang kode.'
            })
    
    # Generate verification code
    code = generate_verification_code()
    
    # Store in session with expiration
    request.session[f'verification_code_{email}'] = {
        'code': code,
        'expires': (timezone.now() + timedelta(minutes=10)).isoformat()
    }
    
    # Set cooldown (60 seconds)
    request.session[cooldown_key] = {
        'expires': (timezone.now() + timedelta(seconds=60)).isoformat()
    }
    
    # Send email
    try:
        send_mail(
            'Kode Verifikasi AgoraTalk',
            f'Kode verifikasi Anda adalah: {code}\n\nKode ini berlaku selama 10 menit.\n\nJika Anda tidak meminta kode ini, abaikan email ini.',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        return JsonResponse({
            'success': True, 
            'message': 'Kode verifikasi berhasil dikirim ke email Anda'
        })
    except Exception as e:
        return JsonResponse({'error': 'Gagal mengirim email. Silakan coba lagi.'})

# Tambahkan view untuk validasi kode verifikasi (opsional - untuk real-time validation)
@require_POST
def validate_verification_code(request):
    """
    AJAX endpoint untuk validasi kode verifikasi secara real-time
    """
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'})
    
    email = request.POST.get('email')
    code = request.POST.get('code')
    
    if not email or not code:
        return JsonResponse({'error': 'Email dan kode diperlukan'})
    
    # Check verification code
    session_key = f'verification_code_{email}'
    if session_key not in request.session:
        return JsonResponse({'error': 'Kode verifikasi tidak ditemukan'})
    
    verification_data = request.session[session_key]
    
    # Check if code is expired
    expires = timezone.datetime.fromisoformat(verification_data['expires'])
    if timezone.now() > expires:
        del request.session[session_key]
        return JsonResponse({'error': 'Kode verifikasi telah kadaluarsa'})
    
    # Validate verification code
    if code != verification_data['code']:
        return JsonResponse({'error': 'Kode verifikasi tidak valid'})
    
    return JsonResponse({'success': True, 'message': 'Kode verifikasi valid'})

@login_required
def mark_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})