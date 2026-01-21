"""
Management command to populate database with teacher data
Creates sample subjects, teachers, and schedules for testing

Usage:
    python manage.py populate_teacher_data              # Populate data
    python manage.py populate_teacher_data --reset      # Reset and repopulate

What this command creates:
    - 15 Subjects across 4 categories:
        * AGAMA (Religious): Aqidah, Fiqih, Al-Quran, Hadits, Bahasa Arab
        * UMUM (General): Matematika, Fisika, Kimia, Biologi, Bahasa Indonesia, 
                         Bahasa Inggris, Sejarah
        * KETERAMPILAN (Skills): Teknologi Informasi, Seni Budaya
        * EKSTRAKURIKULER (Extracurricular): Olahraga
    
    - 25 Teachers with:
        * Complete profiles (NIP, name, email, phone)
        * Employment dates (1-5 years ago)
        * Subject assignments (1-3 subjects per teacher)
        * Homeroom teacher assignments (10 teachers)
    
    - ~100 Weekly Schedules with:
        * 3-5 teaching slots per teacher per week
        * Automatic conflict detection (teacher and classroom)
        * Distribution across Monday-Friday
        * JP slots: 1-2, 3-4, 5-6, 7-8

Features:
    - Realistic Indonesian teacher names
    - Automatic scheduling conflict avoidance
    - Balanced subject distribution
    - Homeroom teacher assignments to classrooms
    - Transaction-based data creation (all-or-nothing)

Example Output:
    Subjects: 15 created, 15 total
    Teachers: 25 created, 25 total
    Schedules: 102 created, 47 conflicts avoided
    Successfully populated database with teacher data!
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.models import User
from attendance.models import Subject, Teacher, TeacherSchedule, Classroom, AcademicLevel
import random
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Populate database with sample teacher data (subjects, teachers, schedules)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all teacher data before populating',
        )

    def handle(self, *args, **options):
        """Main command handler"""
        
        if options['reset']:
            self.stdout.write(self.style.WARNING('Resetting all teacher data...'))
            TeacherSchedule.objects.all().delete()
            Teacher.objects.all().delete()
            Subject.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Teacher data reset complete'))
        
        with transaction.atomic():
            # Create subjects
            subjects = self.create_subjects()
            
            # Create teachers
            teachers = self.create_teachers(subjects)
            
            # Generate schedules
            self.create_schedules(teachers)
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated database with teacher data!')
        )

    def create_subjects(self):
        """Create sample subjects"""
        
        subjects_data = [
            # Religious subjects (AGAMA)
            {'code': 'AQD', 'name': 'Aqidah', 'category': 'AGAMA', 'description': 'Studi tentang keyakinan Islam'},
            {'code': 'FQH', 'name': 'Fiqih', 'category': 'AGAMA', 'description': 'Hukum Islam dan praktiknya'},
            {'code': 'QRN', 'name': 'Al-Quran', 'category': 'AGAMA', 'description': 'Membaca dan memahami Al-Quran'},
            {'code': 'HDT', 'name': 'Hadits', 'category': 'AGAMA', 'description': 'Studi hadits Nabi Muhammad SAW'},
            {'code': 'ARB', 'name': 'Bahasa Arab', 'category': 'AGAMA', 'description': 'Bahasa Arab dan tata bahasanya'},
            
            # General subjects (UMUM)
            {'code': 'MTK', 'name': 'Matematika', 'category': 'UMUM', 'description': 'Ilmu hitung dan logika'},
            {'code': 'FIS', 'name': 'Fisika', 'category': 'UMUM', 'description': 'Ilmu alam tentang materi dan energi'},
            {'code': 'KIM', 'name': 'Kimia', 'category': 'UMUM', 'description': 'Ilmu tentang zat dan perubahannya'},
            {'code': 'BIO', 'name': 'Biologi', 'category': 'UMUM', 'description': 'Ilmu tentang makhluk hidup'},
            {'code': 'IND', 'name': 'Bahasa Indonesia', 'category': 'UMUM', 'description': 'Bahasa dan sastra Indonesia'},
            {'code': 'ENG', 'name': 'Bahasa Inggris', 'category': 'UMUM', 'description': 'Bahasa Inggris dan komunikasi'},
            {'code': 'SEJ', 'name': 'Sejarah', 'category': 'UMUM', 'description': 'Sejarah Indonesia dan dunia'},
            
            # Skills (KETERAMPILAN)
            {'code': 'TIK', 'name': 'Teknologi Informasi', 'category': 'KETERAMPILAN', 'description': 'Komputer dan teknologi'},
            {'code': 'SEN', 'name': 'Seni Budaya', 'category': 'KETERAMPILAN', 'description': 'Seni dan budaya Indonesia'},
            
            # Extracurricular (EKSTRAKURIKULER)
            {'code': 'OLR', 'name': 'Olahraga', 'category': 'EKSTRAKURIKULER', 'description': 'Pendidikan jasmani dan kesehatan'},
        ]
        
        created_subjects = []
        created_count = 0
        
        for subject_data in subjects_data:
            subject, created = Subject.objects.get_or_create(
                code=subject_data['code'],
                defaults=subject_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(f"Created subject: {subject}")
            else:
                self.stdout.write(f"Subject already exists: {subject}")
            
            created_subjects.append(subject)
        
        self.stdout.write(
            self.style.SUCCESS(f'Subjects: {created_count} created, {len(created_subjects)} total')
        )
        
        return created_subjects

    def create_teachers(self, subjects):
        """Create sample teachers with subject assignments"""
        
        # Indonesian teacher names
        teachers_data = [
            {'nip': 'UST001', 'name': 'Ahmad Yusuf', 'email': 'ahmad.yusuf@yaumi.sch.id', 'phone': '081234567801'},
            {'nip': 'UST002', 'name': 'Muhammad Hasan', 'email': 'muhammad.hasan@yaumi.sch.id', 'phone': '081234567802'},
            {'nip': 'UST003', 'name': 'Abdullah Rahman', 'email': 'abdullah.rahman@yaumi.sch.id', 'phone': '081234567803'},
            {'nip': 'UST004', 'name': 'Ibrahim Khalil', 'email': 'ibrahim.khalil@yaumi.sch.id', 'phone': '081234567804'},
            {'nip': 'UST005', 'name': 'Umar Faruq', 'email': 'umar.faruq@yaumi.sch.id', 'phone': '081234567805'},
            {'nip': 'UST006', 'name': 'Ali Imran', 'email': 'ali.imran@yaumi.sch.id', 'phone': '081234567806'},
            {'nip': 'UST007', 'name': 'Hamzah Malik', 'email': 'hamzah.malik@yaumi.sch.id', 'phone': '081234567807'},
            {'nip': 'UST008', 'name': 'Zaid Abdullah', 'email': 'zaid.abdullah@yaumi.sch.id', 'phone': '081234567808'},
            {'nip': 'UST009', 'name': 'Bilal Hasan', 'email': 'bilal.hasan@yaumi.sch.id', 'phone': '081234567809'},
            {'nip': 'UST010', 'name': 'Salman Farisi', 'email': 'salman.farisi@yaumi.sch.id', 'phone': '081234567810'},
            {'nip': 'UST011', 'name': 'Khalid Walid', 'email': 'khalid.walid@yaumi.sch.id', 'phone': '081234567811'},
            {'nip': 'UST012', 'name': 'Usman Affan', 'email': 'usman.affan@yaumi.sch.id', 'phone': '081234567812'},
            {'nip': 'UST013', 'name': 'Faisal Hakim', 'email': 'faisal.hakim@yaumi.sch.id', 'phone': '081234567813'},
            {'nip': 'UST014', 'name': 'Ridwan Kamil', 'email': 'ridwan.kamil@yaumi.sch.id', 'phone': '081234567814'},
            {'nip': 'UST015', 'name': 'Hadi Wijaya', 'email': 'hadi.wijaya@yaumi.sch.id', 'phone': '081234567815'},
            {'nip': 'UST016', 'name': 'Fahmi Basir', 'email': 'fahmi.basir@yaumi.sch.id', 'phone': '081234567816'},
            {'nip': 'UST017', 'name': 'Nasir Udin', 'email': 'nasir.udin@yaumi.sch.id', 'phone': '081234567817'},
            {'nip': 'UST018', 'name': 'Aziz Mansur', 'email': 'aziz.mansur@yaumi.sch.id', 'phone': '081234567818'},
            {'nip': 'UST019', 'name': 'Harun Rasyid', 'email': 'harun.rasyid@yaumi.sch.id', 'phone': '081234567819'},
            {'nip': 'UST020', 'name': 'Ismail Hanif', 'email': 'ismail.hanif@yaumi.sch.id', 'phone': '081234567820'},
            {'nip': 'UST021', 'name': 'Yusuf Qadir', 'email': 'yusuf.qadir@yaumi.sch.id', 'phone': '081234567821'},
            {'nip': 'UST022', 'name': 'Zakariya Amin', 'email': 'zakariya.amin@yaumi.sch.id', 'phone': '081234567822'},
            {'nip': 'UST023', 'name': 'Musa Ibrahim', 'email': 'musa.ibrahim@yaumi.sch.id', 'phone': '081234567823'},
            {'nip': 'UST024', 'name': 'Idris Syarif', 'email': 'idris.syarif@yaumi.sch.id', 'phone': '081234567824'},
            {'nip': 'UST025', 'name': 'Ilyas Hakim', 'email': 'ilyas.hakim@yaumi.sch.id', 'phone': '081234567825'},
        ]
        
        created_teachers = []
        created_count = 0
        
        # Get some classrooms for homeroom assignments
        classrooms = list(Classroom.objects.filter(is_active=True)[:10])
        
        for idx, teacher_data in enumerate(teachers_data):
            # Set employment date (between 1-5 years ago)
            years_ago = random.randint(1, 5)
            employment_date = date.today() - timedelta(days=years_ago * 365)
            
            teacher, created = Teacher.objects.get_or_create(
                nip=teacher_data['nip'],
                defaults={
                    'full_name': teacher_data['name'],
                    'email': teacher_data['email'],
                    'phone': teacher_data['phone'],
                    'employment_date': employment_date,
                    'employment_status': 'ACTIVE',
                    'is_active': True,
                }
            )
            
            if created:
                created_count += 1
                
                # Assign 1-3 subjects to each teacher
                num_subjects = random.randint(1, 3)
                teacher_subjects = random.sample(subjects, num_subjects)
                teacher.subjects.set(teacher_subjects)
                
                # Assign some teachers as homeroom teachers
                if idx < len(classrooms):
                    teacher.is_homeroom_teacher = True
                    teacher.homeroom_class = classrooms[idx]
                    teacher.save()
                
                subject_names = ", ".join([s.name for s in teacher_subjects])
                homeroom_info = f" (Wali Kelas {teacher.homeroom_class})" if teacher.is_homeroom_teacher else ""
                self.stdout.write(f"Created teacher: {teacher.full_name} - {subject_names}{homeroom_info}")
            else:
                self.stdout.write(f"Teacher already exists: {teacher.full_name}")
            
            created_teachers.append(teacher)
        
        self.stdout.write(
            self.style.SUCCESS(f'Teachers: {created_count} created, {len(created_teachers)} total')
        )
        
        return created_teachers

    def create_schedules(self, teachers):
        """Generate weekly schedules for all teachers"""
        
        # Get all active classrooms
        classrooms = list(Classroom.objects.filter(is_active=True))
        
        if not classrooms:
            self.stdout.write(
                self.style.WARNING('No classrooms found. Please create classrooms first.')
            )
            return
        
        created_count = 0
        conflict_count = 0
        
        # Effective date is today
        effective_date = date.today()
        
        # Days of the week (0=Monday to 4=Friday, skip weekend)
        school_days = [0, 1, 2, 3, 4]  # Monday to Friday
        
        # JP slots available per day
        jp_slots = [
            (1, 2),   # JP 1-2
            (3, 4),   # JP 3-4
            (5, 6),   # JP 5-6
            (7, 8),   # JP 7-8
        ]
        
        # Track which slots are taken for each classroom on each day
        # Format: {(classroom_id, day, jp_start, jp_end): teacher}
        classroom_schedule = {}
        
        # Track which slots are taken for each teacher on each day
        # Format: {(teacher_id, day, jp_start, jp_end): classroom}
        teacher_schedule = {}
        
        for teacher in teachers:
            # Get subjects this teacher can teach
            teacher_subjects = list(teacher.subjects.all())
            
            if not teacher_subjects:
                continue
            
            # Each teacher gets 3-5 teaching slots per week
            num_slots = random.randint(3, 5)
            slots_assigned = 0
            attempts = 0
            max_attempts = 50  # Prevent infinite loop
            
            while slots_assigned < num_slots and attempts < max_attempts:
                attempts += 1
                
                # Pick a random day and JP slot
                day = random.choice(school_days)
                jp_start, jp_end = random.choice(jp_slots)
                
                # Pick a random classroom
                classroom = random.choice(classrooms)
                
                # Pick a random subject from teacher's subjects
                subject = random.choice(teacher_subjects)
                
                # Check if this slot is already taken for the classroom
                classroom_key = (classroom.id, day, jp_start, jp_end)
                if classroom_key in classroom_schedule:
                    conflict_count += 1
                    continue
                
                # Check if this slot is already taken for the teacher
                teacher_key = (teacher.id, day, jp_start, jp_end)
                if teacher_key in teacher_schedule:
                    conflict_count += 1
                    continue
                
                # Create the schedule
                try:
                    schedule = TeacherSchedule.objects.create(
                        teacher=teacher,
                        subject=subject,
                        classroom=classroom,
                        day_of_week=day,
                        jp_start=jp_start,
                        jp_end=jp_end,
                        effective_date=effective_date,
                        is_active=True,
                    )
                    
                    # Mark this slot as taken
                    classroom_schedule[classroom_key] = teacher
                    teacher_schedule[teacher_key] = classroom
                    
                    created_count += 1
                    slots_assigned += 1
                    
                    day_name = dict(TeacherSchedule.DAY_CHOICES).get(day, 'Unknown')
                    self.stdout.write(
                        f"  Created schedule: {teacher.full_name} - {subject.name} - "
                        f"{classroom.name} - {day_name} JP{jp_start}-{jp_end}"
                    )
                
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"  Error creating schedule: {str(e)}")
                    )
                    conflict_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Schedules: {created_count} created, {conflict_count} conflicts avoided'
            )
        )
