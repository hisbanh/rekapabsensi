from django import forms
from django.utils import timezone
from django.contrib.auth.models import User
from .models import (
    AttendanceRecord, AttendanceStatus, Student, Classroom, 
    AcademicLevel, Holiday, DaySchedule, Teacher, TeacherSchedule
)


# ============================================
# Student Management Forms
# ============================================

class StudentForm(forms.ModelForm):
    """Form for creating and editing students"""
    
    class Meta:
        model = Student
        fields = [
            'student_id', 'nisn', 'name', 'classroom', 
            'date_of_birth', 'gender', 'address', 'parent_phone',
            'enrollment_date', 'is_active'
        ]
        widgets = {
            'student_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contoh: S001'
            }),
            'nisn': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '10 digit NISN'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama lengkap siswa'
            }),
            'classroom': forms.Select(attrs={
                'class': 'form-select'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Alamat lengkap'
            }),
            'parent_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nomor telepon orang tua'
            }),
            'enrollment_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter only active classrooms
        self.fields['classroom'].queryset = Classroom.objects.filter(
            is_active=True
        ).select_related('academic_level').order_by(
            'academic_level__code', 'grade', 'section'
        )


class StudentFilterForm(forms.Form):
    """Form for filtering student list"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Cari nama atau NIS...'
        })
    )
    classroom = forms.ModelChoiceField(
        required=False,
        queryset=Classroom.objects.none(),
        empty_label='Semua Kelas',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Semua Status'), ('active', 'Aktif'), ('inactive', 'Nonaktif')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['classroom'].queryset = Classroom.objects.filter(
            is_active=True
        ).select_related('academic_level').order_by(
            'academic_level__code', 'grade', 'section'
        )


# ============================================
# Classroom Management Forms
# ============================================

class ClassroomForm(forms.ModelForm):
    """Form for creating and editing classrooms"""
    
    class Meta:
        model = Classroom
        fields = [
            'academic_level', 'grade', 'section', 'name',
            'capacity', 'room_number', 'homeroom_teacher',
            'academic_year', 'is_active'
        ]
        widgets = {
            'academic_level': forms.Select(attrs={
                'class': 'form-select'
            }),
            'grade': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 12
            }),
            'section': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'A, B, C, dll.'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama kelas (opsional)'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 100
            }),
            'room_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nomor ruangan'
            }),
            'homeroom_teacher': forms.Select(attrs={
                'class': 'form-select'
            }),
            'academic_year': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '2024/2025'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['academic_level'].queryset = AcademicLevel.objects.filter(is_active=True)
        self.fields['homeroom_teacher'].queryset = User.objects.filter(is_active=True)
        self.fields['homeroom_teacher'].required = False


# ============================================
# Holiday Management Forms
# ============================================

class HolidayForm(forms.ModelForm):
    """Form for creating and editing holidays"""
    
    apply_scope = forms.ChoiceField(
        choices=[('all', 'Semua Kelas'), ('specific', 'Pilih Kelas Tertentu')],
        initial='all',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Holiday
        fields = ['date', 'name', 'holiday_type', 'description', 'classrooms']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama hari libur'
            }),
            'holiday_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Keterangan tambahan (opsional)'
            }),
            'classrooms': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': 6
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['classrooms'].queryset = Classroom.objects.filter(
            is_active=True
        ).select_related('academic_level').order_by(
            'academic_level__code', 'grade', 'section'
        )
        self.fields['classrooms'].required = False
        
        # Set initial apply_scope based on instance
        if self.instance and self.instance.pk:
            if self.instance.apply_to_all:
                self.initial['apply_scope'] = 'all'
            else:
                self.initial['apply_scope'] = 'specific'
    
    def clean(self):
        cleaned_data = super().clean()
        apply_scope = cleaned_data.get('apply_scope')
        classrooms = cleaned_data.get('classrooms')
        
        if apply_scope == 'specific' and not classrooms:
            raise forms.ValidationError(
                'Pilih minimal satu kelas jika memilih "Pilih Kelas Tertentu"'
            )
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        apply_scope = self.cleaned_data.get('apply_scope')
        
        if apply_scope == 'all':
            instance.apply_to_all = True
        else:
            instance.apply_to_all = False
        
        if commit:
            instance.save()
            # Handle M2M relationship
            if apply_scope == 'all':
                instance.classrooms.clear()
            else:
                self.save_m2m()
        
        return instance


# ============================================
# Day Schedule Forms
# ============================================

class DayScheduleForm(forms.ModelForm):
    """Form for editing day schedule"""
    
    class Meta:
        model = DaySchedule
        fields = ['default_jp_count', 'is_school_day']
        widgets = {
            'default_jp_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10
            }),
            'is_school_day': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


# ============================================
# User Management Forms
# ============================================

class UserForm(forms.ModelForm):
    """Form for creating and editing users"""
    
    password1 = forms.CharField(
        label='Password',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Masukkan password'
        })
    )
    password2 = forms.CharField(
        label='Konfirmasi Password',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ulangi password'
        })
    )
    role = forms.ChoiceField(
        choices=[('guru', 'Guru'), ('admin', 'Admin')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username untuk login'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama depan'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama belakang'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial role based on instance
        if self.instance and self.instance.pk:
            if self.instance.is_superuser:
                self.initial['role'] = 'admin'
            else:
                self.initial['role'] = 'guru'
            # Password not required for edit
            self.fields['password1'].help_text = 'Kosongkan jika tidak ingin mengubah password'
        else:
            # Password required for new user
            self.fields['password1'].required = True
            self.fields['password2'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError('Password tidak cocok')
            if len(password1) < 8:
                raise forms.ValidationError('Password minimal 8 karakter')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Set password if provided
        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)
        
        # Set role
        role = self.cleaned_data.get('role')
        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
        else:
            user.is_staff = True
            user.is_superuser = False
        
        if commit:
            user.save()
        
        return user


# ============================================
# Attendance Forms (existing)
# ============================================

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = AttendanceRecord
        fields = ['student', 'date', 'status', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class AttendanceFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    classroom = forms.ModelChoiceField(
        required=False,
        queryset=Classroom.objects.none(),
        empty_label='Semua Kelas',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Semua Status')] + list(AttendanceStatus.choices),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate classroom choices dynamically
        self.fields['classroom'].queryset = Classroom.objects.filter(
            is_active=True
        ).select_related('academic_level').order_by(
            'academic_level__code', 'grade', 'section'
        )

class BulkAttendanceForm(forms.Form):
    date = forms.DateField(
        initial=timezone.now().date(),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    classroom = forms.ModelChoiceField(
        queryset=Classroom.objects.none(),
        empty_label='Pilih Kelas',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate classroom choices dynamically
        self.fields['classroom'].queryset = Classroom.objects.filter(
            is_active=True
        ).select_related('academic_level').order_by(
            'academic_level__code', 'grade', 'section'
        )


# ============================================
# JP-Based Report Forms
# ============================================

class JPReportFilterForm(forms.Form):
    """Form for filtering JP-based attendance reports"""
    
    REPORT_TYPE_CHOICES = [
        ('class', 'Laporan Per Kelas'),
        ('student', 'Laporan Per Siswa'),
    ]
    
    report_type = forms.ChoiceField(
        choices=REPORT_TYPE_CHOICES,
        initial='class',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'report_type'
        })
    )
    classroom = forms.ModelChoiceField(
        required=False,
        queryset=Classroom.objects.none(),
        empty_label='Pilih Kelas',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'classroom'
        })
    )
    student = forms.ModelChoiceField(
        required=False,
        queryset=Student.objects.none(),
        empty_label='Pilih Siswa',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'student'
        })
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'id': 'start_date'
        })
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'id': 'end_date'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default dates (current month)
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        
        if not self.data.get('start_date'):
            self.initial['start_date'] = first_day_of_month
        if not self.data.get('end_date'):
            self.initial['end_date'] = today
        
        # Populate classroom choices
        self.fields['classroom'].queryset = Classroom.objects.filter(
            is_active=True
        ).select_related('academic_level').order_by(
            'academic_level__code', 'grade', 'section'
        )
        
        # Populate student choices
        self.fields['student'].queryset = Student.objects.filter(
            is_active=True
        ).select_related('classroom', 'classroom__academic_level').order_by('name')
    
    def clean(self):
        cleaned_data = super().clean()
        report_type = cleaned_data.get('report_type')
        classroom = cleaned_data.get('classroom')
        student = cleaned_data.get('student')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # Validate required fields based on report type
        if report_type == 'class' and not classroom:
            raise forms.ValidationError('Pilih kelas untuk laporan per kelas')
        
        if report_type == 'student' and not student:
            raise forms.ValidationError('Pilih siswa untuk laporan per siswa')
        
        # Validate date range
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError('Tanggal mulai tidak boleh lebih besar dari tanggal akhir')
            
            # Limit date range to 3 months
            max_days = 93  # ~3 months
            if (end_date - start_date).days > max_days:
                raise forms.ValidationError(f'Rentang tanggal maksimal {max_days} hari')
        
        return cleaned_data



# ============================================
# Teacher Management Forms
# ============================================

class TeacherForm(forms.ModelForm):
    """Form for creating and editing teachers"""
    
    class Meta:
        model = Teacher
        fields = [
            'teacher_id', 'nip', 'name', 'user', 'subjects',
            'academic_year', 'is_active'
        ]
        widgets = {
            'teacher_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contoh: U001'
            }),
            'nip': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '18 digit NIP'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama lengkap ustadz'
            }),
            'user': forms.Select(attrs={
                'class': 'form-select'
            }),
            'subjects': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Mata pelajaran (pisahkan dengan koma)'
            }),
            'academic_year': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '2024/2025'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter only active users without teacher profile
        self.fields['user'].queryset = User.objects.filter(
            is_active=True,
            teacher_profile__isnull=True
        ) | User.objects.filter(
            id=self.instance.user_id if self.instance and self.instance.user_id else None
        )
        self.fields['user'].required = False


class TeacherScheduleForm(forms.ModelForm):
    """Form for creating and editing teacher schedules"""
    
    jp_numbers_display = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contoh: 1,2,3 atau 1-5'
        }),
        help_text='Masukkan nomor JP (pisahkan dengan koma atau gunakan range)'
    )
    
    class Meta:
        model = TeacherSchedule
        fields = ['teacher', 'day_of_week', 'subject', 'is_piket', 'academic_year', 'notes']
        widgets = {
            'teacher': forms.Select(attrs={
                'class': 'form-select'
            }),
            'day_of_week': forms.Select(attrs={
                'class': 'form-select'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mata pelajaran'
            }),
            'is_piket': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'academic_year': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '2024/2025'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Catatan tambahan'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher'].queryset = Teacher.objects.filter(is_active=True).order_by('name')
        
        # Set initial jp_numbers_display from instance
        if self.instance and self.instance.pk and self.instance.jp_numbers:
            self.initial['jp_numbers_display'] = ','.join(map(str, self.instance.jp_numbers))
    
    def clean_jp_numbers_display(self):
        """Parse JP numbers from display string"""
        jp_str = self.cleaned_data.get('jp_numbers_display', '').strip()
        
        if not jp_str:
            return []
        
        jp_numbers = []
        
        try:
            # Split by comma
            parts = jp_str.split(',')
            
            for part in parts:
                part = part.strip()
                
                # Check if it's a range (e.g., "1-5")
                if '-' in part:
                    start, end = part.split('-')
                    start = int(start.strip())
                    end = int(end.strip())
                    
                    if start > end:
                        raise forms.ValidationError(f"Range tidak valid: {part}")
                    
                    jp_numbers.extend(range(start, end + 1))
                else:
                    # Single number
                    jp_numbers.append(int(part))
            
            # Remove duplicates and sort
            jp_numbers = sorted(set(jp_numbers))
            
            # Validate range
            for jp in jp_numbers:
                if jp < 1 or jp > 10:
                    raise forms.ValidationError(f"Nomor JP harus antara 1-10, ditemukan: {jp}")
            
            return jp_numbers
            
        except ValueError:
            raise forms.ValidationError("Format JP tidak valid. Gunakan angka, koma, atau range (contoh: 1,2,3 atau 1-5)")
    
    def clean(self):
        cleaned_data = super().clean()
        jp_numbers = cleaned_data.get('jp_numbers_display', [])
        teacher = cleaned_data.get('teacher')
        day_of_week = cleaned_data.get('day_of_week')
        
        if jp_numbers and teacher and day_of_week is not None:
            # Check for overlapping JP with other schedules on the same day
            existing_schedules = TeacherSchedule.objects.filter(
                teacher=teacher,
                day_of_week=day_of_week
            )
            
            # Exclude current instance if editing
            if self.instance and self.instance.pk:
                existing_schedules = existing_schedules.exclude(pk=self.instance.pk)
            
            # Check for overlap
            for schedule in existing_schedules:
                if schedule.jp_numbers:
                    overlap = set(jp_numbers) & set(schedule.jp_numbers)
                    if overlap:
                        day_name = dict(TeacherSchedule.DAY_CHOICES).get(day_of_week, 'hari ini')
                        overlap_str = ', '.join(map(str, sorted(overlap)))
                        raise forms.ValidationError(
                            f'JP {overlap_str} sudah digunakan untuk jadwal lain di hari {day_name} '
                            f'({schedule.subject or "tanpa mata pelajaran"}). '
                            f'Silakan pilih JP yang berbeda.'
                        )
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set jp_numbers from parsed display
        instance.jp_numbers = self.cleaned_data.get('jp_numbers_display', [])
        
        if commit:
            instance.save()
        
        return instance


class TeacherAttendanceFilterForm(forms.Form):
    """Form for filtering teacher attendance reports"""
    
    teacher = forms.ModelChoiceField(
        required=False,
        queryset=Teacher.objects.none(),
        empty_label='Semua Ustadz',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default dates (current month)
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        
        if not self.data.get('start_date'):
            self.initial['start_date'] = first_day_of_month
        if not self.data.get('end_date'):
            self.initial['end_date'] = today
        
        # Populate teacher choices
        self.fields['teacher'].queryset = Teacher.objects.filter(
            is_active=True
        ).order_by('name')
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # Validate date range
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError('Tanggal mulai tidak boleh lebih besar dari tanggal akhir')
        
        return cleaned_data
