# Generated migration for populating students data
from django.db import migrations
from django.utils import timezone


def populate_academic_levels(apps, schema_editor):
    """Populate academic levels"""
    AcademicLevel = apps.get_model('attendance', 'AcademicLevel')
    
    academic_levels = [
        {
            'code': 'SMP',
            'name': 'Sekolah Menengah Pertama',
            'level_type': 'SMP',
            'description': 'Tingkat pendidikan menengah pertama (kelas 7-9)',
            'min_grade': 7,
            'max_grade': 9,
        },
        {
            'code': 'SMA',
            'name': 'Sekolah Menengah Atas',
            'level_type': 'SMA',
            'description': 'Tingkat pendidikan menengah atas (kelas 10-12)',
            'min_grade': 10,
            'max_grade': 12,
        }
    ]
    
    for level_data in academic_levels:
        AcademicLevel.objects.get_or_create(
            code=level_data['code'],
            defaults=level_data
        )


def populate_classrooms(apps, schema_editor):
    """Populate classrooms"""
    AcademicLevel = apps.get_model('attendance', 'AcademicLevel')
    Classroom = apps.get_model('attendance', 'Classroom')
    
    # Get academic levels
    try:
        smp = AcademicLevel.objects.get(code='SMP')
        sma = AcademicLevel.objects.get(code='SMA')
    except AcademicLevel.DoesNotExist:
        return  # Skip if academic levels don't exist
    
    # Define classrooms
    classrooms_data = [
        # SMP Classrooms (grades 7-9)
        {'academic_level': smp, 'grade': 7, 'section': 'A', 'capacity': 35},
        {'academic_level': smp, 'grade': 7, 'section': 'B', 'capacity': 35},
        {'academic_level': smp, 'grade': 8, 'section': 'A', 'capacity': 30},
        {'academic_level': smp, 'grade': 8, 'section': 'B', 'capacity': 30},
        {'academic_level': smp, 'grade': 9, 'section': 'A', 'capacity': 30},
        {'academic_level': smp, 'grade': 9, 'section': 'B', 'capacity': 30},
        
        # SMA Classrooms (grades 10-12)
        {'academic_level': sma, 'grade': 10, 'section': 'A', 'capacity': 30},
        {'academic_level': sma, 'grade': 10, 'section': 'B', 'capacity': 30},
        {'academic_level': sma, 'grade': 11, 'section': '', 'capacity': 35},
        {'academic_level': sma, 'grade': 12, 'section': '', 'capacity': 35},
    ]
    
    for classroom_data in classrooms_data:
        classroom_data['academic_year'] = '2024/2025'
        
        Classroom.objects.get_or_create(
            academic_level=classroom_data['academic_level'],
            grade=classroom_data['grade'],
            section=classroom_data['section'],
            academic_year=classroom_data['academic_year'],
            defaults=classroom_data
        )


def populate_students(apps, schema_editor):
    """Populate students data"""
    Student = apps.get_model('attendance', 'Student')
    Classroom = apps.get_model('attendance', 'Classroom')
    
    # Sample students data (first 50 students for migration)
    students_data = [
        # Class 7-A (first 10 students)
        {'id': '7A01', 'nisn': '', 'name': 'Abdullah Muhammad Sadat', 'class': '7-A'},
        {'id': '7A02', 'nisn': '', 'name': 'Abdurrahman Sumardi', 'class': '7-A'},
        {'id': '7A03', 'nisn': '', 'name': 'Abidz Alvaro Bastian', 'class': '7-A'},
        {'id': '7A04', 'nisn': '', 'name': 'Ahmad Fahrezzi Fahri Nursya', 'class': '7-A'},
        {'id': '7A05', 'nisn': '', 'name': 'Alfino Mueen Alfarizqy', 'class': '7-A'},
        {'id': '7A06', 'nisn': '', 'name': 'Andi Zaa Axelle Akbar', 'class': '7-A'},
        {'id': '7A07', 'nisn': '', 'name': 'Azzam Mujahid', 'class': '7-A'},
        {'id': '7A08', 'nisn': '', 'name': 'Danish Zaidan Al - Fahrezi', 'class': '7-A'},
        {'id': '7A09', 'nisn': '', 'name': 'Deigo Omar Tamaya', 'class': '7-A'},
        {'id': '7A10', 'nisn': '', 'name': 'Faiz Az Zahran Aulia', 'class': '7-A'},
        
        # Class 8-A (first 10 students)
        {'id': '8A01', 'nisn': '0224010003', 'name': 'Abid Naqqi Alhakim', 'class': '8-A'},
        {'id': '8A02', 'nisn': '0224010004', 'name': 'Achmad Milan Hadiwidjaya', 'class': '8-A'},
        {'id': '8A03', 'nisn': '0224010005', 'name': 'Ahmad Mirza Aufa Rais', 'class': '8-A'},
        {'id': '8A04', 'nisn': '0224010006', 'name': 'Ali Hasan', 'class': '8-A'},
        {'id': '8A05', 'nisn': '0224010010', 'name': 'Andira Shafi Azmi', 'class': '8-A'},
        {'id': '8A06', 'nisn': '0224010015', 'name': 'Duta Hibban Ahssidiq', 'class': '8-A'},
        {'id': '8A07', 'nisn': '0224010017', 'name': 'Faiz Abdurrahman', 'class': '8-A'},
        {'id': '8A08', 'nisn': '0224010018', 'name': 'Faran Zaka Jahabidz', 'class': '8-A'},
        {'id': '8A09', 'nisn': '0224010019', 'name': 'Faras Atha Purna An-Naqi', 'class': '8-A'},
        {'id': '8A10', 'nisn': '0224010022', 'name': 'Galih Ibrahim Priyono', 'class': '8-A'},
        
        # Class 9-A (first 10 students)
        {'id': '9A01', 'nisn': '0223010001', 'name': 'Abdul Malik Al Atsary', 'class': '9-A'},
        {'id': '9A02', 'nisn': '0223010004', 'name': 'Adhiwangsa Beryl Nugroho', 'class': '9-A'},
        {'id': '9A03', 'nisn': '0223010006', 'name': 'Ahmad Rafa Fahreza', 'class': '9-A'},
        {'id': '9A04', 'nisn': '0223010009', 'name': 'Azzaam', 'class': '9-A'},
        {'id': '9A05', 'nisn': '0223010011', 'name': 'Bayu Setioko', 'class': '9-A'},
        {'id': '9A06', 'nisn': '0223010013', 'name': 'Daffa Leorenzo', 'class': '9-A'},
        {'id': '9A07', 'nisn': '0223010015', 'name': 'Dihya Al Ghifari', 'class': '9-A'},
        {'id': '9A08', 'nisn': '0223010017', 'name': 'Fadhlur rohman hanif', 'class': '9-A'},
        {'id': '9A09', 'nisn': '0223010018', 'name': "Fathurrahman al'ghazi", 'class': '9-A'},
        {'id': '9A10', 'nisn': '0223010020', 'name': 'Fendra Athwan Syahdan', 'class': '9-A'},
        
        # Class 10-A (first 10 students)
        {'id': '10A01', 'nisn': '', 'name': 'Anugerah Rajendra Aji Pawenang', 'class': '10-A'},
        {'id': '10A02', 'nisn': '', 'name': 'Ehza Abdul Aziz', 'class': '10-A'},
        {'id': '10A03', 'nisn': '', 'name': 'Farhan', 'class': '10-A'},
        {'id': '10A04', 'nisn': '', 'name': 'Fawwaz Izzudin', 'class': '10-A'},
        {'id': '10A05', 'nisn': '', 'name': 'Hafidz Maulana Riyu Subagiyo', 'class': '10-A'},
        {'id': '10A06', 'nisn': '', 'name': 'Hibban Abdullah', 'class': '10-A'},
        {'id': '10A07', 'nisn': '', 'name': 'Jagad Almair Abimantrana', 'class': '10-A'},
        {'id': '10A08', 'nisn': '', 'name': 'Khalawatul Iman', 'class': '10-A'},
        {'id': '10A09', 'nisn': '', 'name': 'Kistiyan Zico Fridenta', 'class': '10-A'},
        {'id': '10A10', 'nisn': '', 'name': 'Luthfan Eka Rochman', 'class': '10-A'},
        
        # Class 11 (first 5 students)
        {'id': '1101', 'nisn': '0324010001', 'name': 'Abdul Hamid', 'class': '11'},
        {'id': '1102', 'nisn': '0324010002', 'name': 'Afgan Arofiq', 'class': '11'},
        {'id': '1103', 'nisn': '0324010004', 'name': 'Ahmad Wildan Agust Ramadhan', 'class': '11'},
        {'id': '1104', 'nisn': '0324010005', 'name': 'Akbar Firdaus Setyawan', 'class': '11'},
        {'id': '1105', 'nisn': '0324010006', 'name': 'Akhtar Danish Rasikh', 'class': '11'},
        
        # Class 12 (first 5 students)
        {'id': '1201', 'nisn': '0323010001', 'name': 'Abdul Aziz Risay Ar Royan', 'class': '12'},
        {'id': '1202', 'nisn': '0323010002', 'name': 'Abdul Halim Mustaqim', 'class': '12'},
        {'id': '1203', 'nisn': '0323010003', 'name': "Abdullah Umar Rifa'i", 'class': '12'},
        {'id': '1204', 'nisn': '0323010004', 'name': 'Abyyan Ammar Dhafi', 'class': '12'},
        {'id': '1205', 'nisn': '0323010007', 'name': 'Al Wildan Jibril Rahmat', 'class': '12'},
    ]
    
    # Create classroom mapping
    classroom_mapping = {}
    for classroom in Classroom.objects.all():
        if classroom.section:
            key = f"{classroom.grade}-{classroom.section}"
        else:
            key = str(classroom.grade)
        classroom_mapping[key] = classroom
    
    # Create students
    today = timezone.now().date()
    
    for student_data in students_data:
        class_key = student_data['class']
        if class_key in classroom_mapping:
            classroom = classroom_mapping[class_key]
            
            # Create student without calling full_clean() to bypass validation
            Student.objects.get_or_create(
                student_id=student_data['id'],
                defaults={
                    'nisn': student_data['nisn'],
                    'name': student_data['name'],
                    'classroom': classroom,
                    'enrollment_date': today,
                    'is_active': True
                }
            )


def reverse_populate_students(apps, schema_editor):
    """Reverse migration - remove populated data"""
    Student = apps.get_model('attendance', 'Student')
    Classroom = apps.get_model('attendance', 'Classroom')
    AcademicLevel = apps.get_model('attendance', 'AcademicLevel')
    
    # Delete in reverse order
    Student.objects.all().delete()
    Classroom.objects.all().delete()
    AcademicLevel.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0006_populate_day_schedule'),
    ]

    operations = [
        migrations.RunPython(
            populate_academic_levels,
            reverse_code=reverse_populate_students,
        ),
        migrations.RunPython(
            populate_classrooms,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            populate_students,
            reverse_code=migrations.RunPython.noop,
        ),
    ]