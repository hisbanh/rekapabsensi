#!/usr/bin/env python
"""
Script untuk memberikan akses staff ke semua user ustadz
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sipa_yaumi.settings')
django.setup()

from django.contrib.auth.models import User
from attendance.models import Teacher

def give_teacher_access():
    print("=" * 60)
    print("MEMBERIKAN AKSES STAFF KE USER USTADZ")
    print("=" * 60)
    print()
    
    # Ambil semua teacher yang punya user
    teachers = Teacher.objects.filter(user__isnull=False, is_active=True)
    
    if not teachers.exists():
        print("❌ Tidak ada ustadz dengan user account!")
        return
    
    print(f"Total ustadz dengan user account: {teachers.count()}\n")
    
    updated_count = 0
    already_staff_count = 0
    
    for teacher in teachers:
        user = teacher.user
        
        if user.is_staff:
            print(f"✓ {teacher.full_name} ({user.username}) - Sudah staff")
            already_staff_count += 1
        else:
            user.is_staff = True
            user.save()
            print(f"✅ {teacher.full_name} ({user.username}) - Diberi akses staff")
            updated_count += 1
    
    print()
    print("=" * 60)
    print("HASIL:")
    print("=" * 60)
    print(f"✅ User yang diberi akses: {updated_count}")
    print(f"✓ User yang sudah punya akses: {already_staff_count}")
    print(f"📊 Total: {updated_count + already_staff_count}")
    print()
    print("🎉 Selesai! Semua ustadz sekarang bisa mengakses menu Absensi Ustadz")
    print()
    print("💡 Silakan login ulang untuk melihat perubahan")

if __name__ == '__main__':
    give_teacher_access()
