#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_backend.settings')
django.setup()

from api.models import Employee, Role

# Create admin role
admin_role, _ = Role.objects.get_or_create(
    id='role_admin',
    defaults={
        'name': 'Admin',
        'permissions': [p[0] for p in Role.Permission.choices]
    }
)

# Create admin user
admin_user, created = Employee.objects.get_or_create(
    phone='1234',
    defaults={
        'name': 'Admin User',
        'role': admin_role,
        'id': 'emp_admin'
    }
)

if created:
    admin_user.set_password('1234')
    admin_user.save()
    print(f'Admin user created: {admin_user.name}, PIN: 1234')
else:
    # Update existing user password
    admin_user.set_password('1234')
    admin_user.save()
    print(f'Admin user updated: {admin_user.name}, PIN: 1234')

print(f'User exists: {not created}')
