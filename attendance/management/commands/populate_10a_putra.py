"""
Management command to populate Kelas 10A Putra students.
"""
from django.core.management.base import BaseCommand
from attendance.models import Student, Classroom, AcademicLevel


class Command(BaseCommand):
    help = 'Populate Kelas 10A Putra with student data'

    def handle(self, *args, **options):
        # Get or create SMA academic level
        sma, _ = AcademicLevel.objects.get_or_create(
            code='SMA',
            defaults={
                'name': 'Sekolah Menengah Atas',
                'level_type': 'SMA',
                'min_grade': 10,
                'max_grade': 12
            }
        )
        
        # Get or create Kelas 10A Putra
        classroom, created = Classroom.objects.get_or_create(
            name='Kelas 10A Putra',
            defaults={
                'academic_level': sma,
                'grade': 10,
                'section': 'A',
                'academic_year': '2025/2026',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created classroom: {classroom.name}'))
        else:
            self.stdout.write(f'Using existing classroom: {classroom.name}')
        
        # Student data for Kelas 10A Putra
        students_data = [
            {'no': 1, 'name': 'Anugerah Rajendra Aji Pawenang'},
            {'no': 2, 'name': 'Ehza Abdul Aziz'},
            {'no': 3, 'name': 'Farhan'},
            {'no': 4, 'name': 'Fawwaz Izzudin'},
            {'no': 5, 'name': 'Hafidz Maulana Riyu Subagiyo'},
            {'no': 6, 'name': 'Hibban Abdullah'},
            {'no': 7, 'name': 'Jagad Almair Abimantrana'},
            {'no': 8, 'name': 'Khalawatul Iman'},
            {'no': 9, 'name': 'Kistiyan Zico Fridenta'},
            {'no': 10, 'name': 'Luthfan Eka Rochman'},
            {'no': 11, 'name': 'Mirza Arkan Ardisa'},
            # No. 12 is empty/skipped
            {'no': 13, 'name': 'Mufid Shiddiq'},
            {'no': 14, 'name': 'Muhammad Abdillah Mukhtar'},
            {'no': 15, 'name': 'Muhammad Aisy Zhafran'},
            {'no': 16, 'name': 'Muhammad Azzam Ramadhan'},
            {'no': 17, 'name': 'Muhammad Fauzan Mubarok'},
            {'no': 18, 'name': 'Muhammad Furqon'},
            {'no': 19, 'name': 'Muhammad Haikal Kamil'},
            {'no': 20, 'name': 'Muhammad Karim Rosyid'},
            {'no': 21, 'name': 'Muhammad Keifa Alhanif Wiguna'},
            {'no': 22, 'name': 'Muhammad Tifa Nugroho'},
            {'no': 23, 'name': 'Musa'},
            {'no': 24, 'name': 'Nandra Ibrah Rajaa'},
            {'no': 25, 'name': 'Rifqy Haidar Fadhil'},
            {'no': 26, 'name': 'Syauqi Shiroi'},
            {'no': 27, 'name': 'Tegar Afnur Suradi'},
        ]
        
        created_count = 0
        updated_count = 0
        
        for student_data in students_data:
            # Generate student_id based on class and number
            student_id = f"10AP{student_data['no']:03d}"
            
            student, created = Student.objects.update_or_create(
                student_id=student_id,
                defaults={
                    'name': student_data['name'],
                    'classroom': classroom,
                    'gender': 'M',  # Putra = Male/Laki-laki
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f"  Created: {student.name}")
            else:
                updated_count += 1
                self.stdout.write(f"  Updated: {student.name}")
        
        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Created: {created_count}, Updated: {updated_count}'
        ))
