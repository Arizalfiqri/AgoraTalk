import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from forum.models import AdminUser

# Buat admin user
admin_user = AdminUser.objects.create_user(
    username='admin',
    email='admin@gmail.com',
    password='admin123',
    employee_id='EMP001',
    department='IT',
    is_staff=True,
    is_superuser=True
)

print(f"Admin user created: {admin_user.username}")