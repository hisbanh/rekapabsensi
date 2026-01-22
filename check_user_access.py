#!/usr/bin/env python
"""
Script untuk memeriksa akses user ke halaman absensi ustadz
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sipa_yaumi.settings')
django.setup()

from django.contrib.auth.models import User
from attendance.models import Teacher

def check_user_access():
    print("=" * 60)
    print("PEMERIKSAAN AKSES USER KE HALAMAN ABSENSI USTADZ")
    print("=" * 60)
    print()
    
    # Ambil semua user
    users = User.objects.all()
    
    if not users.exists():
        print("❌ Tidak ada user di database!")
        return
    
    print(f"Total user: {users.count()}\n")
    
    for user in users:
        print(f"👤 Username: {user.username}")
        print(f"   Nama: {user.get_full_name() or '-'}")
        print(f"   Email: {user.email or '-'}")
        print(f"   Is Staff: {'✅ Ya' if user.is_staff else '❌ Tidak'}")
        print(f"   Is Superuser: {'✅ Ya' if user.is_superuser else '❌ Tidak'}")
        
        # Cek apakah user terhubung dengan Teacher
        try:
            teacher = Teacher.objects.get(user=user)
            print(f"   Profil Ustadz: ✅ Terhubung ({teacher.full_name})")
        except Teacher.DoesNotExist:
            print(f"   Profil Ustadz: ❌ Tidak terhubung")
        
        # Cek akses ke menu
        can_access = user.is_staff or user.is_superuser
        print(f"   Akses Menu Ustadz: {'✅ BISA' if can_access else '❌ TIDAK BISA'}")
        print()
    
    print("=" * 60)
    print("REKOMENDASI:")
    print("=" * 60)
    
    # Cari user yang tidak punya akses
    no_access_users = users.filter(is_staff=False, is_superuser=False)
    
    if no_access_users.exists():
        print("\n⚠️  User berikut TIDAK BISA mengakses menu Absensi Ustadz:")
        for user in no_access_users:
            print(f"   - {user.username}")
        
        print("\n💡 Solusi: Jalankan perintah berikut untuk memberikan akses:")
        print("\n   python manage.py shell")
        print("   >>> from django.contrib.auth.models import User")
        for user in no_access_users:
            print(f"   >>> user = User.objects.get(username='{user.username}')")
            print(f"   >>> user.is_staff = True")
            print(f"   >>> user.save()")
            print()
    else:
        print("\n✅ Semua user sudah memiliki akses ke menu Absensi Ustadz!")
    
    # Cek data ustadz
    print("\n" + "=" * 60)
    print("DATA USTADZ:")
    print("=" * 60)
    
    teachers = Teacher.objects.filter(is_active=True)
    print(f"\nTotal Ustadz Aktif: {teachers.count()}")
    
    if teachers.exists():
        print("\nDaftar Ustadz:")
        for teacher in teachers[:10]:  # Tampilkan 10 pertama
            user_status = "✅ Terhubung" if teacher.user else "❌ Tidak terhubung"
            print(f"   - {teacher.full_name} (NIP: {teacher.nip}) - User: {user_status}")
        
        if teachers.count() > 10:
            print(f"   ... dan {teachers.count() - 10} ustadz lainnya")
    else:
        print("\n⚠️  Belum ada data ustadz di database!")
        print("💡 Jalankan: python manage.py populate_teacher_data")

if __name__ == '__main__':
    check_user_access()
