# forum/urls.py - Fixed
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Halaman utama
    path('', views.home, name='home'),
    
    # Autentikasi USER BIASA
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True,
        redirect_field_name='next'
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('ajax/send-verification-code/', views.ajax_send_verification_code, name='ajax_send_verification_code'),
    path('ajax/validate-verification-code/', views.validate_verification_code, name='validate_verification_code'),
    
    # Autentikasi ADMIN - Custom register untuk admin
    path('admin-register/', views.admin_register, name='admin_register'),
    
    # Thread
    path('forum/', views.thread_list, name='thread_list'),
    path('forum/<str:category_slug>/', views.thread_list, name='thread_list_category'),
    path('thread/<int:pk>/', views.thread_detail, name='thread_detail'),
    path('thread/new/', views.create_thread, name='create_thread'),
    path('thread/<int:pk>/edit/', views.edit_thread, name='edit_thread'),
    path('thread/<int:pk>/delete/', views.delete_thread, name='delete_thread'),
    path('thread/<int:pk>/vote/', views.vote_thread, name='vote_thread'),
    
    # Komentar dan interaksi
    path('comment/<int:comment_pk>/vote/', views.vote_comment, name='vote_comment'),
    path('comment/<int:comment_pk>/delete/', views.delete_comment, name='delete_comment'),
    path('thread/<int:thread_pk>/add_comment/', views.add_comment, name='add_comment'),
    path('thread/<int:pk>/bookmark/', views.toggle_bookmark, name='toggle_bookmark'),
    
    # User
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<str:username>/', views.profile_detail, name='profile_detail'),
    path('notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),
    
    # Pencarian
    path('search/', views.search, name='search'),
    
    # Test
    path('test/', views.test_template, name='test_template'),
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
]