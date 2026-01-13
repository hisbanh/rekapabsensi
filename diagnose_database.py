#!/usr/bin/env python
"""
Script untuk diagnosis lengkap database dan migrasi
"""
import os
import django
import sqlite3

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sipa_yaumi.settings')
django.setup()

from django.core.management import call_command
from django.db import connection
from attendance.models import AcademicLevel, Classroom, Student

def check_database_file():
    """Cek apakah file database ada dan bisa diakses"""
    print("=== DATABASE FILE CHECK ===")
    
    db_path = 'db.sqlite3'
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"✅ Database file exists: {db_path} ({size} bytes)")
        
        # Cek apakah bisa dibuka
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"📊 Tables found: {len(tables)}")
            for table in tables[:10]:  # Show first 10 tables
                print(f"   - {table[0]}")
            conn.close()
        except Exception as e:
            print(f"❌ Error accessing database: {e}")
    else:
        print(f"❌ Database file not found: {db_path}")

def check_migrations():
    """Cek status migrasi"""
    print("\n=== MIGRATION STATUS ===")
    
    try:
        # Cek migrasi yang sudah dijalankan
        from django.db.migrations.executor import MigrationExecutor
        executor = MigrationExecutor(connection)
        
        # Get migration plan
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        
        if plan:
            print("❌ Pending migrations found:")
            for migration, backwards in plan:
                print(f"   - {migration}")
        else:
            print("✅ All migrations are up to date")
            
        # Show applied migrations
        applied = executor.loader.applied_migrations
        print(f"📋 Applied migrations: {len(applied)}")
        
    except Exception as e:
        print(f"❌ Error checking migrations: {e}")

def check_tables():
    """Cek apakah tabel model ada"""
    print("\n=== TABLE STRUCTURE CHECK ===")
    
    models_to_check = [
        ('attendance_academiclevel', AcademicLevel),
        ('attendance_classroom', Classroom),
        ('attendance_student', Student),
    ]
    
    with connection.cursor() as cursor:
        for table_name, model_class in models_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"✅ {table_name}: {count} records")
                
                # Cek struktur tabel
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                print(f"   Columns: {len(columns)}")
                
            except Exception as e:
                print(f"❌ {table_name}: Error - {e}")

def check_model_data():
    """Cek data di model"""
    print("\n=== MODEL DATA CHECK ===")
    
    try:
        academic_levels = AcademicLevel.objects.count()
        classrooms = Classroom.objects.count()
        students = Student.objects.count()
        
        print(f"📚 Academic Levels: {academic_levels}")
        print(f"🏫 Classrooms: {classrooms}")
        print(f"👥 Students: {students}")
        
        if academic_levels == 0:
            print("⚠️  No Academic Levels found - this might be the issue!")
        if classrooms == 0:
            print("⚠️  No Classrooms found - this might be the issue!")
            
    except Exception as e:
        print(f"❌ Error accessing models: {e}")

def run_migration_fix():
    """Jalankan perbaikan migrasi"""
    print("\n=== RUNNING MIGRATION FIX ===")
    
    try:
        print("🔄 Running migrations...")
        call_command('migrate', verbosity=2)
        print("✅ Migrations completed")
        
        # Cek lagi setelah migrasi
        check_model_data()
        
    except Exception as e:
        print(f"❌ Migration error: {e}")

if __name__ == "__main__":
    print("🔍 DATABASE DIAGNOSIS")
    print("=" * 50)
    
    check_database_file()
    check_migrations()
    check_tables()
    check_model_data()
    
    # Jika ada masalah, coba fix
    print("\n" + "=" * 50)
    response = input("Run migration fix? (y/n): ")
    if response.lower() == 'y':
        run_migration_fix()
    
    print("\n✅ Diagnosis completed!")