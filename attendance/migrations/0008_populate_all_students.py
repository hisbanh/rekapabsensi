# Generated migration for populating all students data
from django.db import migrations
from django.utils import timezone


def populate_all_students(apps, schema_editor):
    """Populate all students data"""
    Student = apps.get_model('attendance', 'Student')
    Classroom = apps.get_model('attendance', 'Classroom')
    
    # Complete students data
    students_data = [
        # Class 7-A (complete)
        {'id': '7A11', 'nisn': '', 'name': 'Farhan', 'class': '7-A'},
        {'id': '7A12', 'nisn': '', 'name': 'Fauzan Abdilah', 'class': '7-A'},
        {'id': '7A13', 'nisn': '', 'name': 'Hanif Ardi Prasetiyo', 'class': '7-A'},
        {'id': '7A14', 'nisn': '', 'name': 'Humaydi Ibnu Junayd', 'class': '7-A'},
        {'id': '7A15', 'nisn': '', 'name': 'Ibrahim Ubaidillah Mubarrok', 'class': '7-A'},
        {'id': '7A16', 'nisn': '', 'name': "Ibrohim Hani Arrifa'l", 'class': '7-A'},
        {'id': '7A17', 'nisn': '', 'name': 'Khaizan Aufar Alzan', 'class': '7-A'},
        {'id': '7A18', 'nisn': '', 'name': 'Lukman Nurrokhib', 'class': '7-A'},
        {'id': '7A19', 'nisn': '', 'name': 'Muhamad Nawwaf', 'class': '7-A'},
        {'id': '7A20', 'nisn': '', 'name': 'Muhammad Fadhil Akbar', 'class': '7-A'},
        {'id': '7A21', 'nisn': '', 'name': 'Muhammad Hasan Fakhrurozi', 'class': '7-A'},
        {'id': '7A22', 'nisn': '', 'name': 'Muhammad Huda Al Fayyadh', 'class': '7-A'},
        {'id': '7A23', 'nisn': '', 'name': 'Muhammad Ihsan Fakhrullah', 'class': '7-A'},
        {'id': '7A24', 'nisn': '', 'name': 'Muhammad Irsyad Azka Syarif', 'class': '7-A'},
        {'id': '7A25', 'nisn': '', 'name': 'Muhammad Naafi Dhaifullah', 'class': '7-A'},
        {'id': '7A26', 'nisn': '', 'name': 'Muhammad Rafif Zufarian', 'class': '7-A'},
        {'id': '7A27', 'nisn': '', 'name': "Muhammad Raihan Khoirunni'Am", 'class': '7-A'},
        {'id': '7A28', 'nisn': '', 'name': 'Muhammad Yazid Hidayah', 'class': '7-A'},
        {'id': '7A29', 'nisn': '', 'name': 'Muhammad Zhafrand Aqila Zia Ul Haq', 'class': '7-A'},
        {'id': '7A30', 'nisn': '', 'name': 'Nuri Sahin Sutanto', 'class': '7-A'},
        {'id': '7A31', 'nisn': '', 'name': 'Oktavian Cahyo Firdaus', 'class': '7-A'},

        # Class 7-B (complete)
        {'id': '7B01', 'nisn': '', 'name': 'Abdul Hakam As Syarif', 'class': '7-B'},
        {'id': '7B02', 'nisn': '', 'name': 'Abdurrahman Fawaz', 'class': '7-B'},
        {'id': '7B03', 'nisn': '', 'name': 'Ahmad Faiz Fakhruddin', 'class': '7-B'},
        {'id': '7B04', 'nisn': '', 'name': 'Ahmad Zidan Fawwaz', 'class': '7-B'},
        {'id': '7B05', 'nisn': '', 'name': 'Bintang Hizbullah', 'class': '7-B'},
        {'id': '7B06', 'nisn': '', 'name': 'Danadyaksa Akhtar Aditya', 'class': '7-B'},
        {'id': '7B07', 'nisn': '', 'name': 'Farhan Maher Abdullah', 'class': '7-B'},
        {'id': '7B08', 'nisn': '', 'name': 'Faza Maher Muhammad', 'class': '7-B'},
        {'id': '7B09', 'nisn': '', 'name': 'Fikri Nur Hafiy', 'class': '7-B'},
        {'id': '7B10', 'nisn': '', 'name': 'Jafar Alfarizi', 'class': '7-B'},
        {'id': '7B11', 'nisn': '', 'name': 'Kautsar Nabiha Putra Mustofa', 'class': '7-B'},
        {'id': '7B12', 'nisn': '', 'name': 'M. Khaizan Yafe Mudhaffar', 'class': '7-B'},
        {'id': '7B13', 'nisn': '', 'name': 'Mohammad Aufa Hafiz Kanz', 'class': '7-B'},
        {'id': '7B14', 'nisn': '', 'name': 'Muh. Fatah Al Mubarok', 'class': '7-B'},
        {'id': '7B15', 'nisn': '', 'name': 'Muh. Fatih Al Mutanniq', 'class': '7-B'},
        {'id': '7B16', 'nisn': '', 'name': 'Muhammad Faqih Ali', 'class': '7-B'},
        {'id': '7B17', 'nisn': '', 'name': 'Muhammad Hasan Faqih Adz Dzikri', 'class': '7-B'},
        {'id': '7B18', 'nisn': '', 'name': 'Muhammad Nafis Alfatih', 'class': '7-B'},
        {'id': '7B19', 'nisn': '', 'name': 'Muhammad Zulfadhli Adnan', 'class': '7-B'},
        {'id': '7B20', 'nisn': '', 'name': 'Nabhani Zaky Aqil Widiyanto', 'class': '7-B'},
        {'id': '7B21', 'nisn': '', 'name': 'Naufal Abdullah Rafif', 'class': '7-B'},
        {'id': '7B22', 'nisn': '', 'name': 'Naufal Asnawi Afham Muzaffar', 'class': '7-B'},
        {'id': '7B23', 'nisn': '', 'name': 'Nizam Ruzain Baihaqi', 'class': '7-B'},
        {'id': '7B24', 'nisn': '', 'name': 'Orlando Vitto Ramadhani Dewanta', 'class': '7-B'},
        {'id': '7B25', 'nisn': '', 'name': 'Syahin Mubarok', 'class': '7-B'},
        {'id': '7B26', 'nisn': '', 'name': 'Ubaidullah Subhan', 'class': '7-B'},
        {'id': '7B27', 'nisn': '', 'name': 'Ukkasyah', 'class': '7-B'},
        {'id': '7B28', 'nisn': '', 'name': 'Valiant Oceanic', 'class': '7-B'},
        {'id': '7B29', 'nisn': '', 'name': "Yahya 'Abdul Jabbar", 'class': '7-B'},
        {'id': '7B30', 'nisn': '', 'name': 'Yusuf Al-Atsary', 'class': '7-B'},

        # Class 12 (complete - including the problematic student 1230)
        {'id': '1206', 'nisn': '0323010008', 'name': 'Ammar Alfarisi', 'class': '12'},
        {'id': '1207', 'nisn': '0323010009', 'name': 'Aryana azfar assyahmi', 'class': '12'},
        {'id': '1208', 'nisn': '0323010011', 'name': 'Faisal Hafizsyah', 'class': '12'},
        {'id': '1209', 'nisn': '0323010012', 'name': 'Fatthan Abi Fakhrurrahman', 'class': '12'},
        {'id': '1210', 'nisn': '0323010014', 'name': 'Ibrahim Abdurrahman', 'class': '12'},
        {'id': '1211', 'nisn': '0323010015', 'name': 'Kevin rahman khadafi', 'class': '12'},
        {'id': '1212', 'nisn': '0323010016', 'name': 'Krido Serayu Hesti', 'class': '12'},
        {'id': '1213', 'nisn': '0323010017', 'name': 'Luqman', 'class': '12'},
        {'id': '1214', 'nisn': '0323010019', 'name': 'M. Thoriq Mulki Penjalang', 'class': '12'},
        {'id': '1215', 'nisn': '0323010020', 'name': 'Mas\'ud Abdurrohman As Sajid', 'class': '12'},
        {'id': '1216', 'nisn': '0323010021', 'name': 'Muhamad Rizky Tamtomo', 'class': '12'},
        {'id': '1217', 'nisn': '0323010022', 'name': 'Muhammad Affan Nashat', 'class': '12'},
        {'id': '1218', 'nisn': '0323010023', 'name': 'Muhammad Daffa Alfarizi', 'class': '12'},
        {'id': '1219', 'nisn': '0323010024', 'name': 'Muhammad Diarra Hamka', 'class': '12'},
        {'id': '1220', 'nisn': '0323010025', 'name': 'Muhammad Duta Heriansyah', 'class': '12'},
        {'id': '1221', 'nisn': '0323010026', 'name': 'Muhammad Hafiizh Faturrahman', 'class': '12'},
        {'id': '1222', 'nisn': '0323010027', 'name': 'Muhammad Naufal Ghiffari', 'class': '12'},
        {'id': '1223', 'nisn': '0323010029', 'name': 'Muhammad Saif', 'class': '12'},
        {'id': '1224', 'nisn': '0323010030', 'name': 'Muhammad Zuhdhan Rifai', 'class': '12'},
        {'id': '1225', 'nisn': '0323010031', 'name': 'Naufal Mazini', 'class': '12'},
        {'id': '1226', 'nisn': '0323010032', 'name': 'Omar Zahraan Darmawan', 'class': '12'},
        {'id': '1227', 'nisn': '0323010033', 'name': 'Rizki Abdullah', 'class': '12'},
        {'id': '1228', 'nisn': '0323010035', 'name': 'Salman Al Farisi', 'class': '12'},
        {'id': '1229', 'nisn': '0323010036', 'name': 'Yusril Huda', 'class': '12'},
        {'id': '1230', 'nisn': '0323010037', 'name': 'Ziyyal Fifayadhi Aldiya Kafi', 'class': '12'},  # The problematic student
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


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0007_populate_students_data'),
    ]

    operations = [
        migrations.RunPython(
            populate_all_students,
            reverse_code=migrations.RunPython.noop,
        ),
    ]