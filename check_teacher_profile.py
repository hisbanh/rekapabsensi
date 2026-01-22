#!/usr/bin/env python
"""
Script to check and diagnose teacher profile issues
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sipa_yaumi.settings')
django.setup()

from django.contrib.auth.models import User
from attendance.models import Teacher

def check_teacher_profiles():
    """Check all users and their teacher profiles"""
    print("=" * 60)
    print("CHECKING TEACHER PROFILES")
    print("=" * 60)
    
    # Get all users
    users = User.objects.all()
    print(f"\nTotal users: {users.count()}")
    
    # Check each user
    for user in users:
        print(f"\n{'='*60}")
        print(f"User: {user.username} (ID: {user.id})")
        print(f"  - Full Name: {user.get_full_name() or 'N/A'}")
        print(f"  - Email: {user.email or 'N/A'}")
        print(f"  - Is Staff: {user.is_staff}")
        print(f"  - Is Superuser: {user.is_superuser}")
        
        # Check if user has teacher profile
        has_profile = hasattr(user, 'teacher_profile')
        print(f"  - Has teacher_profile attribute: {has_profile}")
        
        if has_profile:
            try:
                teacher = user.teacher_profile
                print(f"  - Teacher Profile: {teacher.full_name} (NIP: {teacher.nip})")
                print(f"  - Teacher Active: {teacher.is_active}")
                print(f"  - Employment Status: {teacher.get_employment_status_display()}")
            except Exception as e:
                print(f"  - ERROR accessing teacher_profile: {str(e)}")
        else:
            print(f"  - No teacher profile linked")
            
            # Check if there's a teacher with matching email or name
            if user.email:
                matching_teachers = Teacher.objects.filter(email=user.email)
                if matching_teachers.exists():
                    print(f"  - Found {matching_teachers.count()} teacher(s) with matching email:")
                    for t in matching_teachers:
                        print(f"    * {t.full_name} (NIP: {t.nip}) - User: {t.user}")
    
    print(f"\n{'='*60}")
    print("TEACHER RECORDS WITHOUT USER LINK")
    print(f"{'='*60}")
    
    # Find teachers without user link
    teachers_without_user = Teacher.objects.filter(user__isnull=True, is_active=True)
    print(f"\nTotal active teachers without user link: {teachers_without_user.count()}")
    
    for teacher in teachers_without_user:
        print(f"\n  - {teacher.full_name} (NIP: {teacher.nip})")
        print(f"    Email: {teacher.email or 'N/A'}")
        print(f"    Employment Status: {teacher.get_employment_status_display()}")
        
        # Check if there's a user with matching email
        if teacher.email:
            matching_users = User.objects.filter(email=teacher.email)
            if matching_users.exists():
                print(f"    FOUND MATCHING USER(S):")
                for u in matching_users:
                    print(f"      * Username: {u.username} (ID: {u.id})")
                    print(f"        Has teacher_profile: {hasattr(u, 'teacher_profile')}")

def link_teacher_to_user():
    """Interactive function to link teacher to user"""
    print("\n" + "=" * 60)
    print("LINK TEACHER TO USER")
    print("=" * 60)
    
    # Show users without teacher profile
    users_without_profile = []
    for user in User.objects.all():
        if not hasattr(user, 'teacher_profile'):
            users_without_profile.append(user)
    
    if not users_without_profile:
        print("\nAll users already have teacher profiles!")
        return
    
    print(f"\nUsers without teacher profile: {len(users_without_profile)}")
    for i, user in enumerate(users_without_profile, 1):
        print(f"{i}. {user.username} - {user.get_full_name() or 'N/A'} ({user.email or 'No email'})")
    
    # Show teachers without user link
    teachers_without_user = Teacher.objects.filter(user__isnull=True, is_active=True)
    print(f"\nTeachers without user link: {teachers_without_user.count()}")
    for i, teacher in enumerate(teachers_without_user, 1):
        print(f"{i}. {teacher.full_name} (NIP: {teacher.nip}) - {teacher.email or 'No email'}")
    
    print("\n" + "=" * 60)
    print("To link a teacher to a user, run:")
    print("python link_teacher_user.py <username> <teacher_nip>")
    print("=" * 60)

if __name__ == '__main__':
    check_teacher_profiles()
    link_teacher_to_user()
