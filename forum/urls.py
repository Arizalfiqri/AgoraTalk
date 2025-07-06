# forum/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import admin_views

urlpatterns = [
    # Halaman utama
    path('', views.home, name='home'),
    
    # Autentikasi USER BIASA
    path('register/', admin_views.register, name='register'),  # Gunakan view yang sudah diupdate
    path('ajax/send-verification-code/', views.ajax_send_verification_code, name='ajax_send_verification_code'),
    path('ajax/validate-verification-code/', views.validate_verification_code, name='validate_verification_code'),
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=None,
        redirect_authenticated_user=True,
        redirect_field_name='next'
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    
    # Autentikasi ADMIN (terpisah)
    path('admin/login/', admin_views.admin_login, name='admin_login'),
    path('admin/logout/', admin_views.admin_logout, name='admin_logout'),
    path('admin/register/', admin_views.admin_register, name='admin_register'),
    
    # Thread
    path('forum/', views.thread_list, name='thread_list'),
    path('forum/<str:category_slug>/', views.thread_list, name='thread_list_category'),
    path('thread/<int:pk>/', views.thread_detail, name='thread_detail'),
    path('thread/new/', views.create_thread, name='create_thread'),
    
    # Komentar dan interaksi
    path('comment/<int:comment_pk>/vote/', views.vote_comment, name='vote_comment'),
    path('thread/<int:pk>/', views.thread_detail, name='thread_detail'),
    path('thread/<int:thread_pk>/add_comment/', views.add_comment, name='add_comment'),
    path('thread/<int:thread_pk>/bookmark/', views.toggle_bookmark, name='toggle_bookmark'),
    
    # User
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),
    
    # Pencarian
    path('search/', views.search, name='search'),
    
    # Test
    path('test/', views.test_template, name='test_template'),
]