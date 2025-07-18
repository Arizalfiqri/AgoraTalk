# # File: config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from forum.admin import admin_site  # Import custom admin site

urlpatterns = [
    path('admin/', admin_site.urls),  # Custom admin site
    path('', include('forum.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)