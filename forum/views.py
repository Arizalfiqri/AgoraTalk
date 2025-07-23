from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, authenticate, login as auth_login
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Count, Sum, Max, F
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.views import View
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from .models import Thread, Category, Comment, Vote, ThreadVote, Bookmark, Notification, User
import json
from django.contrib.auth.backends import ModelBackend
from django.core.mail import send_mail
from django.conf import settings
import random
import string
from django.utils import timezone
from datetime import timedelta
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .forms import CustomUserCreationForm, ThreadForm, CommentForm, ProfileForm

# Registration Views
def register(request):
    """Simple user registration"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def admin_register(request):
    """Admin registration - redirect to regular register for now"""
    return redirect('register')

# Helper Functions
def create_notification(user, notification_type, message, thread=None, comment=None):
    """Helper function untuk membuat notifikasi"""
    if user.is_authenticated:
        Notification.objects.create(
            user=user,
            type=notification_type,
            message=message,
            thread=thread,
            comment=comment
        )

def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))

# Middleware Classes
class AdminUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/'):
            request.session.set_test_cookie()
        
        response = self.get_response(request)
        return response

# Authentication Backends
class BaseAuthenticationBackend(ModelBackend):
    """Base authentication backend"""
    
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

# belum digunakan
class UserAuthenticationBackend(BaseAuthenticationBackend):
    """Custom authentication backend untuk User biasa"""
    pass

# Admin Authentication Backend
class AdminAuthenticationBackend(BaseAuthenticationBackend):
    """Custom authentication backend untuk Admin"""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                # For admin access, check if user has admin privileges
                if request and request.path.startswith('/admin/'):
                    if user.is_admin_user() or user.is_staff or user.is_superuser:
                        return user
                    return None
                return user
        except User.DoesNotExist:
            return None

# Base Views
class BaseForumView(TemplateView):
    """Base view untuk semua forum views"""
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        return context


# Main Views
class HomeView(BaseForumView):
    template_name = 'forum/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Thread populer
        context['popular_threads'] = Thread.objects.annotate(
            comment_count=Count('comments')
        ).order_by('-views', '-comment_count')[:5]
        
        # Thread terbaru
        context['recent_threads'] = Thread.objects.select_related(
            'author', 'category'
        ).order_by('-created_at')[:10]
        
        # Kategori dengan jumlah thread
        context['categories'] = Category.objects.filter(is_active=True).annotate(
            thread_count=Count('thread')
        ).order_by('name')
        
        # Statistik
        context['stats'] = {
            'total_threads': Thread.objects.count(),
            'total_users': User.objects.count(),
            'total_comments': Comment.objects.count(),
        }
        
        return context


class ThreadListView(ListView):
    model = Thread
    template_name = 'forum/thread_list.html'
    context_object_name = 'threads'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = Thread.objects.select_related('author', 'category').annotate(
            comment_count=Count('comments'),
            last_activity=Max('comments__created_at')
        )
        
        # Filter by category
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            category = get_object_or_404(Category, name__iexact=category_slug.replace('-', ' '))
            queryset = queryset.filter(category=category)
        
        # Sorting
        sort = self.request.GET.get('sort', 'recent')
        if sort == 'popular':
            queryset = queryset.order_by('-views', '-comment_count')
        elif sort == 'most_commented':
            queryset = queryset.order_by('-comment_count')
        else:
            queryset = queryset.order_by('-is_pinned', '-updated_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Process tags for each thread
        for thread in context['threads']:
            if thread.tags:
                thread.tags_list = [tag.strip() for tag in thread.tags.split(',') if tag.strip()]
            else:
                thread.tags_list = []
        
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            context['category'] = get_object_or_404(Category, name__iexact=category_slug.replace('-', ' '))
        
        context['sort'] = self.request.GET.get('sort', 'recent')
        
        # Get most active threads (terpisah dari filter utama)
        # Thread teraktif berdasarkan kombinasi likes, comments, dan views
        active_threads = Thread.objects.select_related('author', 'category').annotate(
            comment_count=Count('comments'),
            likes_count=Count('votes', filter=Q(votes__value=1))
        ).order_by('-likes_count', '-comment_count', '-views', '-created_at')[:5]
        
        # Process tags for active threads
        for thread in active_threads:
            if thread.tags:
                thread.tags_list = [tag.strip() for tag in thread.tags.split(',') if tag.strip()]
            else:
                thread.tags_list = []
        
        context['active_threads'] = active_threads
        return context


class ThreadDetailView(DetailView):
    model = Thread
    template_name = 'forum/thread_detail.html'
    context_object_name = 'thread'
    
    def get_object(self):
        thread = super().get_object()
        # Increment view count
        thread.views += 1
        thread.save(update_fields=['views'])
        return thread
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thread = self.get_object()
        
        # Process tags
        if thread.tags:
            thread.tags_list = [tag.strip() for tag in thread.tags.split(',') if tag.strip()]
        else:
            thread.tags_list = []
        
        # Comments with replies
        comments = Comment.objects.filter(
            thread=thread, parent=None
        ).select_related('author').prefetch_related('replies__author')
        
        # Add user vote info to each comment
        if self.request.user.is_authenticated:
            for comment in comments:
                comment.user_has_voted = Vote.objects.filter(
                    user=self.request.user, comment=comment, value=1
                ).exists()
                # Also check replies
                for reply in comment.replies.all():
                    reply.user_has_voted = Vote.objects.filter(
                        user=self.request.user, comment=reply, value=1
                    ).exists()
        
        context['comments'] = comments
        
        # Comment form
        context['comment_form'] = CommentForm()
        
        # Bookmark status
        context['is_bookmarked'] = False
        if self.request.user.is_authenticated:
            context['is_bookmarked'] = Bookmark.objects.filter(
                user=self.request.user, thread=thread
            ).exists()
        
        # Thread voting data
        context['likes_count'] = thread.get_likes_count()
        context['dislikes_count'] = thread.get_dislikes_count()
        context['vote_score'] = thread.get_vote_score()
        
        # User's vote on this thread
        context['user_vote'] = None
        if self.request.user.is_authenticated:
            try:
                user_thread_vote = ThreadVote.objects.get(user=self.request.user, thread=thread)
                context['user_vote'] = user_thread_vote.value
            except ThreadVote.DoesNotExist:
                pass
        
        return context


class CreateThreadView(LoginRequiredMixin, CreateView):
    model = Thread
    form_class = ThreadForm
    template_name = 'forum/create_thread.html'
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        
        # Add points
        self.request.user.points += 10
        self.request.user.save()
        
        messages.success(self.request, 'Thread berhasil dibuat!')
        return response
    
    def get_success_url(self):
        return reverse_lazy('thread_detail', kwargs={'pk': self.object.pk})


class ProfileDetailView(DetailView):
    model = User
    template_name = 'forum/profile_detail.html'
    context_object_name = 'profile_user'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # User threads
        user_threads = Thread.objects.filter(author=user).select_related('category').annotate(
            comment_count=Count('comments')
        ).order_by('-created_at')
        
        # User comments
        context['user_comments'] = Comment.objects.filter(
            author=user
        ).select_related('thread').order_by('-created_at')[:10]
        
        # Statistics
        context['stats'] = {
            'total_threads': Thread.objects.filter(author=user).count(),
            'total_comments': Comment.objects.filter(author=user).count(),
            'total_votes_received': Vote.objects.filter(
                comment__author=user
            ).aggregate(Sum('value'))['value__sum'] or 0,
            'join_date': user.date_joined,
            'last_activity': user.last_login,
        }
        
        # Pagination
        paginator = Paginator(user_threads, 10)
        page_number = self.request.GET.get('page')
        context['threads'] = paginator.get_page(page_number)
        
        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'forum/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # User content
        context['user_threads'] = Thread.objects.filter(
            author=user
        ).order_by('-created_at')[:5]
        
        context['user_comments'] = Comment.objects.filter(
            author=user
        ).select_related('thread').order_by('-created_at')[:5]
        
        context['bookmarked_threads'] = Thread.objects.filter(
            bookmarks__user=user
        ).order_by('-bookmarks__created_at')[:5]
        
        # Notifications
        context['notifications'] = Notification.objects.filter(
            user=user, is_read=False
        ).order_by('-created_at')[:10]
        
        # Statistics
        context['stats'] = {
            'total_threads': Thread.objects.filter(author=user).count(),
            'total_comments': Comment.objects.filter(author=user).count(),
            'total_thread_votes_received': ThreadVote.objects.filter(
                thread__author=user
            ).aggregate(Sum('value'))['value__sum'] or 0,
            'bookmarks_count': Bookmark.objects.filter(user=user).count(),
        }
        
        return context


class EditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = 'forum/edit_profile.html'
    success_url = reverse_lazy('dashboard')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Profil berhasil diperbarui!')
        return super().form_valid(form)


class SearchView(ListView):
    model = Thread
    template_name = 'forum/search.html'
    context_object_name = 'threads'
    paginate_by = 10
    
    def get_queryset(self):
        query = self.request.GET.get('q', '')
        category_filter = self.request.GET.get('category', '')
        sort = self.request.GET.get('sort', 'recent')
        
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
        
        return threads
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['category_filter'] = self.request.GET.get('category', '')
        context['sort'] = self.request.GET.get('sort', 'recent')
        context['categories'] = Category.objects.filter(is_active=True)
        return context

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        verification_code = self.request.POST.get('verification_code')

        if not verification_code:
            form.add_error(None, 'Kode verifikasi diperlukan.')
            return self.form_invalid(form)
    
        # Validate verification code
        session_key = f'verification_code_{email}'
        if session_key not in self.request.session:
            form.add_error(None, 'Kode verifikasi tidak ditemukan. Silakan kirim ulang kode.')
            return self.form_invalid(form)
    
        verification_data = self.request.session[session_key]
        expires = timezone.datetime.fromisoformat(verification_data['expires'])
    
        if timezone.now() > expires:
            form.add_error(None, 'Kode verifikasi telah kadaluarsa. Silakan kirim ulang kode.')
            del self.request.session[session_key]
            return self.form_invalid(form)
    
        if verification_code != verification_data['code']:
            form.add_error(None, 'Kode verifikasi salah. Mohon periksa kembali.')  # Changed this line
            return self.form_invalid(form)
    
        # Delete session after successful verification
        del self.request.session[session_key]
    
        # Save user
        response = super().form_valid(form)
        self.object.is_active = True
        self.object.save()
    
        # Auto login
        new_user = authenticate(
            request=self.request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password1']
        )
        if new_user:
            auth_login(self.request, new_user)
            messages.success(self.request, 'Registrasi berhasil! Selamat datang di forum.')
    
        return response

# AJAX and API Views
class BaseAjaxView(View):
    """Base view for AJAX requests"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Invalid request'})
        return super().dispatch(request, *args, **kwargs)



class AddCommentView(LoginRequiredMixin, View):
    
    @method_decorator(require_POST)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request, thread_pk):
        thread = get_object_or_404(Thread, pk=thread_pk)
        
        if thread.is_locked and not request.user.is_admin_user():
            messages.error(request, "Thread ini sudah dikunci.")
            return redirect('thread_detail', pk=thread_pk)
        
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.thread = thread
            comment.author = request.user
            
            # Handle reply - Fix the parent comment assignment
            parent_id = request.POST.get('parent_id')
            if parent_id:
                try:
                    parent_id = int(parent_id)  # Validate parent_id is integer
                    # Make sure we get the parent comment properly
                    parent_comment = Comment.objects.get(pk=parent_id, thread=thread)
                    comment.parent = parent_comment
                except (ValueError, Comment.DoesNotExist):
                    # If parent comment doesn't exist or parent_id is invalid, ignore the reply
                    pass
            
            # Save the comment first
            comment.save()
            
            # Handle notifications after comment is saved
            if parent_id and comment.parent:
                # Send notification for reply
                if comment.parent.author != request.user:
                    create_notification(
                        user=comment.parent.author,
                        notification_type='reply',
                        message=f'{request.user.username} membalas komentar Anda di thread "{thread.title}"',
                        thread=thread,
                        comment=comment
                    )
            else:
                # Send notification to thread author
                if thread.author != request.user:
                    create_notification(
                        user=thread.author,
                        notification_type='reply',
                        message=f'{request.user.username} berkomentar di thread Anda "{thread.title}"',
                        thread=thread,
                        comment=comment
                    )
            
            # Add points
            request.user.points += 5
            request.user.save()
            
            # Update thread
            thread.updated_at = timezone.now()
            thread.save()
            
            messages.success(request, 'Komentar berhasil ditambahkan! Anda mendapat 5 poin.')
        else:
            messages.error(request, 'Gagal menambahkan komentar. Silakan coba lagi.')
        
        return redirect('thread_detail', pk=thread_pk)


class VoteCommentView(LoginRequiredMixin, View):
    
    @method_decorator(require_POST)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request, comment_pk):
        comment = get_object_or_404(Comment, pk=comment_pk)
        
        # Hanya menerima like (value=1)
        vote, created = Vote.objects.get_or_create(
            user=request.user, 
            comment=comment,
            defaults={'value': 1}
        )
        
        vote_removed = False
        
        if not created:
            # Jika sudah ada vote, hapus (unlike)
            vote.delete()
            vote_removed = True
        
        # Send notification hanya jika like (bukan unlike)
        if not vote_removed and comment.author != request.user:
            create_notification(
                user=comment.author,
                notification_type='vote',
                message=f'{request.user.username} menyukai komentar Anda di thread "{comment.thread.title}"',
                thread=comment.thread,
                comment=comment
            )
        
        likes_count = comment.get_likes_count()
        
        return JsonResponse({
            'likes': likes_count,
            'vote_removed': vote_removed,
            'user_vote': None if vote_removed else 1
        })


class VoteThreadView(LoginRequiredMixin, View):
    
    @method_decorator(require_POST)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request, pk):
        thread = get_object_or_404(Thread, pk=pk)
        value = int(request.POST.get('value'))
        
        if value not in [1, -1]:
            return JsonResponse({'error': 'Invalid vote value'})
        
        vote, created = ThreadVote.objects.get_or_create(
            user=request.user, 
            thread=thread,
            defaults={'value': value}
        )
        
        vote_removed = False
        
        if not created:
            if vote.value == value:
                vote.delete()
                vote_removed = True
            else:
                vote.value = value
                vote.save()
        
        # Send notification
        if not vote_removed and thread.author != request.user:
            vote_type = "like" if value == 1 else "dislike"
            create_notification(
                user=thread.author,
                notification_type='vote',
                message=f'{request.user.username} memberikan {vote_type} pada thread Anda "{thread.title}"',
                thread=thread
            )
        
        likes_count = thread.get_likes_count()
        dislikes_count = thread.get_dislikes_count()
        
        return JsonResponse({
            'likes': likes_count,
            'dislikes': dislikes_count,
            'vote_removed': vote_removed,
            'user_vote': None if vote_removed else value
        })


class ToggleBookmarkView(LoginRequiredMixin, View):
    
    def post(self, request, pk):
        thread = get_object_or_404(Thread, pk=pk)
        bookmark, created = Bookmark.objects.get_or_create(user=request.user, thread=thread)
        
        if not created:
            bookmark.delete()
            bookmarked = False
        else:
            bookmarked = True
        
        if request.headers.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return JsonResponse({'bookmarked': bookmarked})
        
        return redirect('thread_detail', pk=pk)


class SendVerificationCodeView(BaseAjaxView):
    
    @method_decorator(require_POST)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        email = request.POST.get('email')
        
        if not email:
            return JsonResponse({'error': 'Email diperlukan'})
        
        # Validate email
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({'error': 'Format email tidak valid'})
        
        # Check if email exists
        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email sudah terdaftar'})
        
        # Check cooldown
        cooldown_key = f'verification_cooldown_{email}'
        if cooldown_key in request.session:
            cooldown_data = request.session[cooldown_key]
            cooldown_expires = timezone.datetime.fromisoformat(cooldown_data['expires'])
            if timezone.now() < cooldown_expires:
                remaining_seconds = int((cooldown_expires - timezone.now()).total_seconds())
                return JsonResponse({
                    'error': f'Silakan tunggu {remaining_seconds} detik sebelum mengirim ulang kode.'
                })
        
        # Generate and store code
        code = generate_verification_code()
        request.session[f'verification_code_{email}'] = {
            'code': code,
            'expires': (timezone.now() + timedelta(minutes=10)).isoformat()
        }
        
        # Set cooldown
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


class ValidateVerificationCodeView(BaseAjaxView):
    
    @method_decorator(require_POST)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        email = request.POST.get('email')
        code = request.POST.get('code')
        
        if not email or not code:
            return JsonResponse({'error': 'Email dan kode diperlukan'})
        
        # Check verification code
        session_key = f'verification_code_{email}'
        if session_key not in request.session:
            return JsonResponse({'error': 'Kode verifikasi tidak ditemukan. Silakan kirim ulang kode.'})
        
        verification_data = request.session[session_key]
        expires = timezone.datetime.fromisoformat(verification_data['expires'])
        
        if timezone.now() > expires:
            del request.session[session_key]
            return JsonResponse({'error': 'Kode verifikasi telah kadaluarsa. Silakan kirim ulang kode.'})
        
        if code != verification_data['code']:
            return JsonResponse({'error': 'Kode verifikasi salah. Mohon periksa kembali.'})
        
        return JsonResponse({'success': True, 'message': 'Kode verifikasi valid'})


class GetNotificationsView(LoginRequiredMixin, View):
    
    def get(self, request):
        notifications = Notification.objects.filter(
            user=request.user, is_read=False
        ).order_by('-created_at')[:10]
        
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'type': notification.type,
                'message': notification.message,
                'created_at': notification.created_at.strftime('%d %b %Y %H:%M'),
                'thread_url': notification.thread.get_absolute_url() if notification.thread else None,
                'thread_title': notification.thread.title if notification.thread else None,
            })
        
        return JsonResponse({
            'notifications': notifications_data,
            'count': len(notifications_data)
        })


class MarkNotificationsReadView(LoginRequiredMixin, View):
    
    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'success': True})


class MarkNotificationReadView(LoginRequiredMixin, View):
    
    @method_decorator(require_POST)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request, notification_id):
        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.is_read = True
            notification.save()
            return JsonResponse({'success': True})
        except Notification.DoesNotExist:
            return JsonResponse({'error': 'Notification not found'})


class DeleteCommentView(LoginRequiredMixin, View):
    
    @method_decorator(require_POST)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request, comment_pk):
        comment = get_object_or_404(Comment, pk=comment_pk)
        thread = comment.thread
        
        # Check if user owns the comment or is admin
        if comment.author != request.user and not request.user.is_admin_user():
            messages.error(request, 'Anda tidak memiliki izin untuk menghapus komentar ini.')
            return redirect('thread_detail', pk=thread.pk)
        
        # If comment has replies, don't delete but anonymize
        if comment.replies.exists():
            comment.content = "[Komentar telah dihapus oleh pengguna]"
            comment.author = None  # Remove author reference
            comment.save()
            messages.success(request, 'Komentar berhasil dihapus. Balasan tetap dipertahankan.')
        else:
            # If no replies, completely delete the comment
            comment.delete()
            messages.success(request, 'Komentar berhasil dihapus.')
        
        # Update thread last activity
        thread.updated_at = timezone.now()
        thread.save()
        
        return redirect('thread_detail', pk=thread.pk)


class DeleteThreadView(LoginRequiredMixin, View):
    
    @method_decorator(require_POST)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request, pk):
        thread = get_object_or_404(Thread, pk=pk)
        
        # Check if user owns the thread or is admin
        if thread.author != request.user and not request.user.is_admin_user():
            messages.error(request, 'Anda tidak memiliki izin untuk menghapus thread ini.')
            return redirect('thread_detail', pk=pk)
        
        # Delete related notifications
        Notification.objects.filter(thread=thread).delete()
        
        # Delete related bookmarks
        Bookmark.objects.filter(thread=thread).delete()
        
        # Delete the thread (comments will be deleted via CASCADE)
        thread_title = thread.title
        thread.delete()
        
        messages.success(request, f'Thread "{thread_title}" berhasil dihapus.')
        return redirect('thread_list')


# Function-based views yang tetap diperlukan
def test_template(request):
    return render(request, "forum/analytics.html")


@login_required
def edit_thread(request, pk):
    thread = get_object_or_404(Thread, pk=pk)
    
    # Cek apakah user adalah pemilik thread atau admin
    if request.user != thread.author and not request.user.is_admin_user():
        messages.error(request, 'Anda tidak memiliki izin untuk mengedit thread ini.')
        return redirect('thread_detail', pk=pk)
    
    if request.method == 'POST':
        # Handle form submission
        title = request.POST.get('title')
        content = request.POST.get('content')
        tags = request.POST.get('tags', '')
        remove_image = request.POST.get('remove_image')
        new_image = request.FILES.get('image')
        
        # Validasi input
        if not title or not content:
            messages.error(request, 'Judul dan konten tidak boleh kosong.')
            return redirect('thread_detail', pk=pk)
        
        # Update thread
        thread.title = title
        thread.content = content
        thread.tags = tags
        
        # Handle image
        if remove_image:
            if thread.image:
                thread.image.delete()
                thread.image = None
        
        if new_image:
            if thread.image:
                thread.image.delete()
            thread.image = new_image
        
        thread.save()
        
        messages.success(request, 'Thread berhasil diperbarui!')
        return redirect('thread_detail', pk=pk)
    
    # GET request - show edit form (this is handled by the modal in template)
    return redirect('thread_detail', pk=pk)

@login_required
def delete_thread(request, pk):
    thread = get_object_or_404(Thread, pk=pk)
    
    # Cek apakah user adalah pemilik thread atau admin
    if request.user != thread.author and not request.user.is_admin_user:
        messages.error(request, 'Anda tidak memiliki izin untuk menghapus thread ini.')
        return redirect('thread_detail', pk=pk)
    
    if request.method == 'POST':
        category = thread.category
        thread.delete()
        messages.success(request, 'Thread berhasil dihapus.')
        
        # Redirect ke category atau thread list
        if category:
            return redirect('thread_list_category', category_slug=category.name.lower().replace(' ', '-'))
        else:
            return redirect('thread_list')
    
    return redirect('thread_detail', pk=pk)

@login_required
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    thread = comment.thread
    
    # Cek apakah user adalah pemilik komentar atau admin
    if request.user != comment.author and not request.user.is_admin_user:
        messages.error(request, 'Anda tidak memiliki izin untuk menghapus komentar ini.')
        return redirect('thread_detail', pk=thread.pk)
    
    if request.method == 'POST':
        comment.delete()
        messages.success(request, 'Komentar berhasil dihapus.')
    
    return redirect('thread_detail', pk=thread.pk)

# Alias untuk backward compatibility
home = HomeView.as_view()
thread_list = ThreadListView.as_view()
thread_detail = ThreadDetailView.as_view()
create_thread = CreateThreadView.as_view()
profile_detail = ProfileDetailView.as_view()
dashboard = DashboardView.as_view()
edit_profile = EditProfileView.as_view()
search = SearchView.as_view()
register = RegisterView.as_view()
add_comment = AddCommentView.as_view()
vote_comment = VoteCommentView.as_view()
vote_thread = VoteThreadView.as_view()
toggle_bookmark = ToggleBookmarkView.as_view()
delete_comment = DeleteCommentView.as_view()
delete_thread = DeleteThreadView.as_view()
send_verification_code = SendVerificationCodeView.as_view()
ajax_send_verification_code = SendVerificationCodeView.as_view()
validate_verification_code = ValidateVerificationCodeView.as_view()
get_notifications = GetNotificationsView.as_view()
mark_notifications_read = MarkNotificationsReadView.as_view()
mark_notification_read = MarkNotificationReadView.as_view()