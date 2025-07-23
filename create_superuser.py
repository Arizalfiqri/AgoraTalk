#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from forum.models import User

def create_admin_user():
    # Check if admin user already exists
    if User.objects.filter(username='admin').exists():
        print("User 'admin' already exists!")
        user = User.objects.get(username='admin')
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Role: {user.role}")
        print(f"Is staff: {user.is_staff}")
        print(f"Is superuser: {user.is_superuser}")
        print(f"Is active: {user.is_active}")
        return user
    
    # Create new admin user
    user = User.objects.create_user(
        username='admin',
        email='admin@agoratalk.com',
        password='admin123',
        role='super_admin',
        is_staff=True,
        is_superuser=True,
        is_active=True,
        is_verified=True,
        employee_id='ADM001',
        department='IT'
    )
    
    print("Admin user created successfully!")
    print(f"Username: {user.username}")
    print(f"Password: admin123")
    print(f"Email: {user.email}")
    print(f"Role: {user.role}")
    print(f"Is staff: {user.is_staff}")
    print(f"Is superuser: {user.is_superuser}")
    
    return user

if __name__ == '__main__':
    create_admin_user()
