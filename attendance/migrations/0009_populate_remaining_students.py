# Generated migration for populating remaining students data
from django.db import migrations
from django.utils import timezone


def populate_remaining_students(apps, schema_editor):
    """Populate remaining students data"""
    Student = apps.get_model('attendance', 'Student')
    Classroom = apps.get_model('attendance', 'Classroom')
    
    # Remaining students data (150 siswa yang belum masuk)
    students_data = [
        # Class 8-A (remaining students)
        {'id': '8A11', 'nisn': '0224010024', 'name': 'Hanan Dzulhilmi', 'class': '8-A'},
        {'id': '8A12', 'nisn': '0224010025', 'name': 'Hasta Setiyawardana Hidayatullah', 'class': '8-A'},
        {'id': '8A13', 'nisn': '0224010030', 'name': 'Ihsan Ilahi Zhahir', 'class': '8-A'},
        {'id': '8A14', 'nisn': '0224010031', 'name': 'Ihsan Nabil Al Farisi', 'class': '8-A'},
        {'id': '8A15', 'nisn': '0224010061', 'name': 'Irfan Hakim', 'class': '8-A'},
        {'id': '8A16', 'nisn': '0224010033', 'name': 'Kais Sebti', 'class': '8-A'},
        {'id': '8A17', 'nisn': '0224010034', 'name': 'Karim Abdirrahman', 'class': '8-A'},
        {'id': '8A18', 'nisn': '0224010035', 'name': 'Muaddib Zuhrul Anam', 'class': '8-A'},
        {'id': '8A19', 'nisn': '0224010036', 'name': 'Muhamad Chadzo Awfa Waqor', 'class': '8-A'},
        {'id': '8A20', 'nisn': '0224010039', 'name': 'Muhammad Darussalam Robi`Uts Tsani', 'class': '8-A'},
        {'id': '8A21', 'nisn': '0224010042', 'name': 'Muhammad Zaki Abdurrahman', 'class': '8-A'},
        {'id': '8A22', 'nisn': '0224010045', 'name': 'Nararya Luthfian Zhafi Septandria', 'class': '8-A'},
        {'id': '8A23', 'nisn': '0224010046', 'name': 'Qaisar Muhammad At Taqiy', 'class': '8-A'},
        {'id': '8A24', 'nisn': '0224010048', 'name': 'Rakin Ayyasy', 'class': '8-A'},
        {'id': '8A25', 'nisn': '0224010051', 'name': 'Resky Fatria Priyono', 'class': '8-A'},

        # Class 8-B (complete)
        {'id': '8B01', 'nisn': '0224010002', 'name': 'Abdurrahman Rasyid', 'class': '8-B'},
        {'id': '8B02', 'nisn': '0224010008', 'name': 'Alif Lukman Hanif Assajad', 'class': '8-B'},
        {'id': '8B03', 'nisn': '0224010011', 'name': 'Aria Dzaky Syalia Rahman', 'class': '8-B'},
        {'id': '8B04', 'nisn': '0224010012', 'name': 'Azhar Faqih Aditya Karisma', 'class': '8-B'},
        {'id': '8B05', 'nisn': '0224010013', 'name': 'Bukhara Tsaqiif Alkhemi', 'class': '8-B'},
        {'id': '8B06', 'nisn': '0224010014', 'name': 'Devante Pramawina Wicaksono', 'class': '8-B'},
        {'id': '8B07', 'nisn': '0224010016', 'name': "Fadli Fauzil 'Adhim", 'class': '8-B'},
        {'id': '8B08', 'nisn': '0224010020', 'name': 'Fathurrahman Alfarizi', 'class': '8-B'},
        {'id': '8B09', 'nisn': '0224010021', 'name': 'Fawwaz', 'class': '8-B'},
        {'id': '8B10', 'nisn': '0224010023', 'name': 'Hamzah Afif Abdullah', 'class': '8-B'},
        {'id': '8B11', 'nisn': '0224010026', 'name': 'Haydar Dimas Fabregas', 'class': '8-B'},
        {'id': '8B12', 'nisn': '0224010028', 'name': 'Husain Malik Yahya', 'class': '8-B'},
        {'id': '8B13', 'nisn': '0224010029', 'name': 'Ibrahim Al Mustaqim', 'class': '8-B'},
        {'id': '8B14', 'nisn': '0224010032', 'name': 'Ismail Al Atsary', 'class': '8-B'},
        {'id': '8B15', 'nisn': '0224010037', 'name': 'Muhamad Dzaki Al Rasyid', 'class': '8-B'},
        {'id': '8B16', 'nisn': '0224010038', 'name': 'Muhammad Alfarisy', 'class': '8-B'},
        {'id': '8B17', 'nisn': '0224010040', 'name': 'Muhammad Faiz Al Farhan', 'class': '8-B'},
        {'id': '8B18', 'nisn': '0224010041', 'name': "Muhammad Resya A'Zam Al-Ghifari", 'class': '8-B'},
        {'id': '8B19', 'nisn': '0224010043', 'name': 'Muhammad Zein Askanito', 'class': '8-B'},
        {'id': '8B20', 'nisn': '0224010044', 'name': 'Muzaffar', 'class': '8-B'},
        {'id': '8B21', 'nisn': '0224010047', 'name': 'Rafka Abdullah', 'class': '8-B'},
        {'id': '8B22', 'nisn': '0224010049', 'name': 'Rasya Iqbal Athaya', 'class': '8-B'},
        {'id': '8B23', 'nisn': '0224010052', 'name': 'Saifulloh Mufid El Qorny', 'class': '8-B'},
        {'id': '8B24', 'nisn': '0224010053', 'name': 'Saputra Azka Satria Imam Sahid', 'class': '8-B'},
        {'id': '8B25', 'nisn': '0224010056', 'name': 'Umar Abdillah', 'class': '8-B'},
        {'id': '8B26', 'nisn': '0224010057', 'name': 'Umar Abdul Rozaq Afify', 'class': '8-B'},
        {'id': '8B27', 'nisn': '0224010058', 'name': 'Wikan Hafesh Abdurahman', 'class': '8-B'},
        {'id': '8B28', 'nisn': '0224010059', 'name': 'Zaid Al Arsyad', 'class': '8-B'},

        # Class 9-A (remaining students)
        {'id': '9A11', 'nisn': '0223010024', 'name': 'Islami Syahputra Wijaya', 'class': '9-A'},
        {'id': '9A12', 'nisn': '0223010026', 'name': 'Joeshep Raynaldi Wijaya Mara', 'class': '9-A'},
        {'id': '9A13', 'nisn': '0223010028', 'name': 'M. Arkan Khairiy Saputra', 'class': '9-A'},
        {'id': '9A14', 'nisn': '0223010029', 'name': 'M. Hafidzurrahman Alfa K', 'class': '9-A'},
        {'id': '9A15', 'nisn': '0223010030', 'name': 'Malik Nur Rahmat Muttaqin', 'class': '9-A'},
        {'id': '9A16', 'nisn': '0223010032', 'name': 'Muhamad Syukri Musyafa', 'class': '9-A'},
        {'id': '9A17', 'nisn': '0223010036', 'name': 'Muhammad Gemilang Damai Prakarsa', 'class': '9-A'},
        {'id': '9A18', 'nisn': '0223010044', 'name': 'Muhammad Umar Al Mukhbit', 'class': '9-A'},
        {'id': '9A19', 'nisn': '0223010050', 'name': 'Raihan Althaf Pratama', 'class': '9-A'},
        {'id': '9A20', 'nisn': '0223010051', 'name': 'Reza Putra Medavin', 'class': '9-A'},
        {'id': '9A21', 'nisn': '0223010052', 'name': 'Syahdan Arfan Irsyad', 'class': '9-A'},
        {'id': '9A22', 'nisn': '0223010053', 'name': 'Wildan', 'class': '9-A'},
        {'id': '9A23', 'nisn': '0223010056', 'name': 'Zidan Sidqy Ar-Rosyid', 'class': '9-A'},
        {'id': '9A24', 'nisn': '0223010058', 'name': 'Zulfikar Arkan Raharja', 'class': '9-A'},

        # Class 9-B (complete)
        {'id': '9B01', 'nisn': '0223010002', 'name': 'Abdurrahman Ahmad Mubarrok', 'class': '9-B'},
        {'id': '9B02', 'nisn': '0223010003', 'name': 'Abyyan Hayyan', 'class': '9-B'},
        {'id': '9B03', 'nisn': '0223010005', 'name': 'Agung Fahri Fauzi', 'class': '9-B'},
        {'id': '9B04', 'nisn': '0223010007', 'name': 'Aisar', 'class': '9-B'},
        {'id': '9B05', 'nisn': '0223010008', 'name': 'Arka Adiswara', 'class': '9-B'},
        {'id': '9B06', 'nisn': '0223010010', 'name': 'Bayu Anugerah Al Halimu', 'class': '9-B'},
        {'id': '9B07', 'nisn': '0223010012', 'name': 'Catur Gilang Saputra', 'class': '9-B'},
        {'id': '9B08', 'nisn': '0223010014', 'name': 'Damian Rozaq Ramadhan', 'class': '9-B'},
        {'id': '9B09', 'nisn': '0223010016', 'name': 'Dzaky Annaafi Habibullah', 'class': '9-B'},
        {'id': '9B10', 'nisn': '0223010019', 'name': 'Fauzan', 'class': '9-B'},
        {'id': '9B11', 'nisn': '0223010033', 'name': 'Muhammad Afif Azizi', 'class': '9-B'},
        {'id': '9B12', 'nisn': '0223010034', 'name': 'Muhammad Aqeela Qaf Maliqi', 'class': '9-B'},
        {'id': '9B13', 'nisn': '0223010035', 'name': 'Muhammad Farras', 'class': '9-B'},
        {'id': '9B14', 'nisn': '0223010037', 'name': 'Muhammad Haidar Abdurrahman', 'class': '9-B'},
        {'id': '9B15', 'nisn': '0223010038', 'name': 'Muhammad Hibban', 'class': '9-B'},
        {'id': '9B16', 'nisn': '0223010039', 'name': 'Muhammad Izzan Faqih', 'class': '9-B'},
        {'id': '9B17', 'nisn': '0223010040', 'name': "Muhammad Naafi' Ali Firmansyah", 'class': '9-B'},
        {'id': '9B18', 'nisn': '0223010042', 'name': 'Muhammad Razin Fadil', 'class': '9-B'},
        {'id': '9B19', 'nisn': '0223010043', 'name': 'Muhammad Rizqi Nurruzzaman', 'class': '9-B'},
        {'id': '9B20', 'nisn': '0223010045', 'name': 'Nabhan Jubair', 'class': '9-B'},
        {'id': '9B21', 'nisn': '0223010047', 'name': 'Nizam Ahmad Alfarizi', 'class': '9-B'},
        {'id': '9B22', 'nisn': '0223010048', 'name': 'Rafan Nafi Abdulwali', 'class': '9-B'},
        {'id': '9B23', 'nisn': '0223010049', 'name': 'Rafif Abdul Zhariif', 'class': '9-B'},
        {'id': '9B24', 'nisn': '0223010054', 'name': 'Wildan Firdaus Jauzi Al-Ghazali', 'class': '9-B'},
        {'id': '9B25', 'nisn': '0223010057', 'name': 'Ziyan Muhammad El Arkan', 'class': '9-B'},

        # Class 10-A (remaining students)
        {'id': '10A11', 'nisn': '', 'name': 'Mirza Arkan Ardisa', 'class': '10-A'},
        {'id': '10A12', 'nisn': '', 'name': 'Mufid Shiddiq', 'class': '10-A'},
        {'id': '10A13', 'nisn': '', 'name': 'Muhammad Abdillah Mukhtar', 'class': '10-A'},
        {'id': '10A14', 'nisn': '', 'name': 'Muhammad Aisy Zhafran', 'class': '10-A'},
        {'id': '10A15', 'nisn': '', 'name': 'Muhammad Azzam Ramadhan', 'class': '10-A'},
        {'id': '10A16', 'nisn': '', 'name': 'Muhammad Fauzan Mubarok', 'class': '10-A'},
        {'id': '10A17', 'nisn': '', 'name': 'Muhammad Furqon', 'class': '10-A'},
        {'id': '10A18', 'nisn': '', 'name': 'Muhammad Haikal Kamil', 'class': '10-A'},
        {'id': '10A19', 'nisn': '', 'name': 'Muhammad Karim Rosyid', 'class': '10-A'},
        {'id': '10A20', 'nisn': '', 'name': 'Muhammad Keifa Alhanif Wiguna', 'class': '10-A'},
        {'id': '10A21', 'nisn': '', 'name': 'Muhammad Tifa Nugroho', 'class': '10-A'},
        {'id': '10A22', 'nisn': '', 'name': 'Musa', 'class': '10-A'},
        {'id': '10A23', 'nisn': '', 'name': 'Nandra Ibrah Rajaa', 'class': '10-A'},
        {'id': '10A24', 'nisn': '', 'name': 'Rifqy Haidar Fadhil', 'class': '10-A'},
        {'id': '10A25', 'nisn': '', 'name': 'Syauqi Shiroi', 'class': '10-A'},
        {'id': '10A26', 'nisn': '', 'name': 'Tegar Afnur Suradi', 'class': '10-A'},

        # Class 10-B (complete)
        {'id': '10B01', 'nisn': '', 'name': 'Abdullah', 'class': '10-B'},
        {'id': '10B02', 'nisn': '', 'name': 'Abdullah Al Muhtadi', 'class': '10-B'},
        {'id': '10B03', 'nisn': '', 'name': 'Ahmad Haidir', 'class': '10-B'},
        {'id': '10B04', 'nisn': '', 'name': 'Arjuna Putra', 'class': '10-B'},
        {'id': '10B05', 'nisn': '', 'name': 'Fayyad Abid Adima', 'class': '10-B'},
        {'id': '10B06', 'nisn': '', 'name': 'Gibran Elroy Hidayat', 'class': '10-B'},
        {'id': '10B07', 'nisn': '', 'name': 'Hamzah Lathif', 'class': '10-B'},
        {'id': '10B08', 'nisn': '', 'name': 'Hasan', 'class': '10-B'},
        {'id': '10B09', 'nisn': '', 'name': 'Husain', 'class': '10-B'},
        {'id': '10B10', 'nisn': '', 'name': 'Ibnu Labib', 'class': '10-B'},
        {'id': '10B11', 'nisn': '', 'name': 'Ibrahim Zafran Setiawan', 'class': '10-B'},
        {'id': '10B12', 'nisn': '', 'name': 'Irsyad Abdillah', 'class': '10-B'},
        {'id': '10B13', 'nisn': '', 'name': 'Jamal Abdullah', 'class': '10-B'},
        {'id': '10B14', 'nisn': '', 'name': 'Khaleed Salman Irfani', 'class': '10-B'},
        {'id': '10B15', 'nisn': '', 'name': 'Muhammad Azzam Atstsauri', 'class': '10-B'},
        {'id': '10B16', 'nisn': '', 'name': 'Muhammad Ihsan Andono', 'class': '10-B'},
        {'id': '10B17', 'nisn': '', 'name': 'Muhammad Ikhsan', 'class': '10-B'},
        {'id': '10B18', 'nisn': '', 'name': 'Muhammad Nurul Aziz', 'class': '10-B'},
        {'id': '10B19', 'nisn': '', 'name': 'Muhammad Raffa Miftahul Sodiqin', 'class': '10-B'},
        {'id': '10B20', 'nisn': '', 'name': 'Muhammad Rifqi Hafizh', 'class': '10-B'},
        {'id': '10B21', 'nisn': '', 'name': 'Muhammad Rifqy Al-Faayid', 'class': '10-B'},
        {'id': '10B22', 'nisn': '', 'name': 'Muhammad Zaidan Shidqi Effendy', 'class': '10-B'},
        {'id': '10B23', 'nisn': '', 'name': 'Muhammad Fadhil Al Atsari', 'class': '10-B'},
        {'id': '10B24', 'nisn': '', 'name': 'Nararya Ega Parama', 'class': '10-B'},
        {'id': '10B25', 'nisn': '', 'name': 'Nidal Addna', 'class': '10-B'},
        {'id': '10B26', 'nisn': '', 'name': 'Radhitya Arrazi Faraj', 'class': '10-B'},
        {'id': '10B27', 'nisn': '', 'name': 'Rafa Iqbal Maulana Putra', 'class': '10-B'},
        {'id': '10B28', 'nisn': '', 'name': "Sa'ad Ali Tamam", 'class': '10-B'},
        {'id': '10B29', 'nisn': '', 'name': 'Umair Abdullah', 'class': '10-B'},

        # Class 11 (remaining students)
        {'id': '1106', 'nisn': '0324010007', 'name': 'Alifqy Jati Raharjo', 'class': '11'},
        {'id': '1107', 'nisn': '0324010008', 'name': 'Atha Sava Nararya', 'class': '11'},
        {'id': '1108', 'nisn': '0324010009', 'name': 'Auriel Ainuriza', 'class': '11'},
        {'id': '1109', 'nisn': '0324010010', 'name': 'Bilal Abid Abdulloh', 'class': '11'},
        {'id': '1110', 'nisn': '0324010012', 'name': 'Farij Alessandro Nesta', 'class': '11'},
        {'id': '1111', 'nisn': '0324010013', 'name': 'Fathii Rizq Al Hassan', 'class': '11'},
        {'id': '1112', 'nisn': '0324010014', 'name': 'Fauzan Anwari Ahmad', 'class': '11'},
        {'id': '1113', 'nisn': '0324010015', 'name': 'Hegel Fawwaz Mufadhdhal', 'class': '11'},
        {'id': '1114', 'nisn': '0324010016', 'name': 'Hubaib Fadhillah Trisani', 'class': '11'},
        {'id': '1115', 'nisn': '0324010017', 'name': 'Humam Afkar Respati', 'class': '11'},
        {'id': '1116', 'nisn': '0324010018', 'name': 'Ibrahim Hasan Ramadhan', 'class': '11'},
        {'id': '1117', 'nisn': '0324010021', 'name': 'Khairul Azzam', 'class': '11'},
        {'id': '1118', 'nisn': '0324010022', 'name': 'M. Fikar Anwar', 'class': '11'},
        {'id': '1119', 'nisn': '0324010023', 'name': 'Muhammad Danish Arsyad', 'class': '11'},
        {'id': '1120', 'nisn': '0324010024', 'name': 'Muhammad Faiz Al Akbar', 'class': '11'},
        {'id': '1121', 'nisn': '0324010025', 'name': 'Muhammad Farras Ash-Shidqi', 'class': '11'},
        {'id': '1122', 'nisn': '0324010026', 'name': 'Muhammad Farras Dzaky', 'class': '11'},
        {'id': '1123', 'nisn': '0324010027', 'name': 'Muhammad Fattah', 'class': '11'},
        {'id': '1124', 'nisn': '0324010028', 'name': 'Muhammad Gaza Alfathi', 'class': '11'},
        {'id': '1125', 'nisn': '0324010029', 'name': 'Muhamad Rahil Al Ghifari', 'class': '11'},
        {'id': '1126', 'nisn': '0324010033', 'name': 'Raid Fahri Mahdi', 'class': '11'},
        {'id': '1127', 'nisn': '0324010035', 'name': 'Rizki', 'class': '11'},
        {'id': '1128', 'nisn': '0324010036', 'name': 'Salman Baihaqi Hakim', 'class': '11'},
        {'id': '1129', 'nisn': '', 'name': 'Usamah', 'class': '11'},
        {'id': '1130', 'nisn': '0324010037', 'name': 'Youmi Hafidz Azami', 'class': '11'},
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
        ('attendance', '0008_populate_all_students'),
    ]

    operations = [
        migrations.RunPython(
            populate_remaining_students,
            reverse_code=migrations.RunPython.noop,
        ),
    ]