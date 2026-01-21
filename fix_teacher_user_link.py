#!/usr/bin/env python
"""
Script to link existing teachers with user accounts
Run with: python fix_teacher_user_link.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sipa_yaumi.settings')
django.setup()

from django.contrib.auth.models import User
from attendance.models import Teacher

def link_teachers_to_users():
    """Create user accounts for teachers without users"""
    print("=" * 60)
    print("Linking Teachers to User Accounts")
    print("=" * 60)
    
    # Get teachers without user accounts
    teachers_without_users = Teacher.objects.filter(user__isnull=True, is_active=True)
    
    print(f"\nFound {teachers_without_users.count()} teachers without user accounts")
    
    if teachers_without_users.count() == 0:
        print("All teachers already have user accounts!")
        return
    
    created_count = 0
    error_count = 0
    
    for teacher in teachers_without_users:
        try:
            # Generate username from NIP
            username = f"teacher_{teacher.nip}"
            
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                print(f"✗ Username {username} already exists for {teacher.full_name}")
                error_count += 1
                continue
            
            # Create user account
            user = User.objects.create_user(
                username=username,
                email=teacher.email if teacher.email else f"{username}@example.com",
                password='password123',  # Default password
                first_name=teacher.full_name.split()[0] if teacher.full_name else '',
                last_name=' '.join(teacher.full_name.split()[1:]) if len(teacher.full_name.split()) > 1 else '',
                is_staff=False,
                is_active=True
            )
            
            # Link user to teacher
            teacher.user = user
            teacher.save()
            
            print(f"✓ Created user '{username}' for {teacher.full_name}")
            created_count += 1
            
        except Exception as e:
            print(f"✗ Error creating user for {teacher.full_name}: {str(e)}")
            error_count += 1
    
    print("\n" + "=" * 60)
    print(f"Summary:")
    print(f"  Created: {created_count} user accounts")
    print(f"  Errors: {error_count}")
    print("=" * 60)
    
    if created_count > 0:
        print("\n⚠️  IMPORTANT:")
        print("  Default password for all created users: password123")
        print("  Please ask teachers to change their password after first login")
        print("\n  Login format:")
        print("  Username: teacher_<NIP>")
        print("  Password: password123")

if __name__ == '__main__':
    link_teachers_to_users()
