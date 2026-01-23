"""
Forms for Teacher Management
Includes forms for Teacher, Subject, and TeacherSchedule with validation
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from attendance.models import Teacher, Subject, TeacherSchedule, Classroom
from attendance.services.schedule_service import ScheduleService


class SubjectForm(forms.ModelForm):
    """Form for creating and editing subjects"""
    
    class Meta:
        model = Subject
        fields = ['code', 'name', 'category', 'description', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contoh: MAT, FIS, BIO (huruf besar)',
                'maxlength': 10
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama mata pelajaran'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Deskripsi mata pelajaran (opsional)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'code': 'Kode Mata Pelajaran',
            'name': 'Nama Mata Pelajaran',
            'category': 'Kategori',
            'description': 'Deskripsi',
            'is_active': 'Aktif',
        }
        help_texts = {
            'code': 'Kode unik mata pelajaran (huruf besar, alfanumerik)',
            'name': 'Nama lengkap mata pelajaran',
            'category': 'Kategori mata pelajaran',
        }
    
    def clean_code(self):
        """Validate and normalize subject code"""
        code = self.cleaned_data.get('code', '')
        
        # Convert to uppercase
        code = code.upper().strip()
        
        # Validate alphanumeric (allow hyphens and underscores)
        if not code.replace('_', '').replace('-', '').isalnum():
            raise ValidationError(
                'Kode mata pelajaran harus berisi huruf dan angka saja (boleh dengan tanda hubung atau underscore)'
            )
        
        # Check uniqueness (excluding current instance)
        existing = Subject.objects.filter(code=code)
        if self.instance and self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise ValidationError(f'Kode mata pelajaran "{code}" sudah digunakan')
        
        return code
    
    def clean_name(self):
        """Validate subject name"""
        name = self.cleaned_data.get('name', '').strip()
        
        if len(name) < 3:
            raise ValidationError('Nama mata pelajaran minimal 3 karakter')
        
        return name


class TeacherForm(forms.ModelForm):
    """Form for creating and editing teachers with photo upload handling"""
    
    # Additional field for subject selection - using AJAX for better performance
    subject_ids = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.none(),  # Will be set in __init__
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select select2-multiple',  # Add select2 for better UX
            'size': 8,
            'data-placeholder': 'Pilih mata pelajaran...'
        }),
        label='Mata Pelajaran',
        help_text='Pilih mata pelajaran yang diajarkan'
    )
    
    class Meta:
        model = Teacher
        fields = [
            'nip', 'full_name', 'photo', 'email', 'phone', 'address',
            'employment_date', 'employment_status',
            'is_homeroom_teacher', 'homeroom_class', 'is_active'
        ]
        widgets = {
            'nip': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nomor Induk Pegawai (max 20 karakter)',
                'maxlength': 20
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama lengkap ustadz/ustadzah'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/jpg,image/png'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '08xxxxxxxxxx'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Alamat lengkap'
            }),
            'employment_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'employment_status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_homeroom_teacher': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_is_homeroom_teacher'
            }),
            'homeroom_class': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_homeroom_class'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'nip': 'NIP',
            'full_name': 'Nama Lengkap',
            'photo': 'Foto',
            'email': 'Email',
            'phone': 'Nomor Telepon',
            'address': 'Alamat',
            'employment_date': 'Tanggal Mulai Kerja',
            'employment_status': 'Status Kepegawaian',
            'is_homeroom_teacher': 'Wali Kelas',
            'homeroom_class': 'Kelas yang Diampu',
            'is_active': 'Aktif',
        }
        help_texts = {
            'nip': 'Nomor Induk Pegawai unik (huruf besar dan angka)',
            'photo': 'Upload foto (JPG, PNG, max 5MB)',
            'employment_date': 'Tanggal mulai bekerja di sekolah',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Cache subjects and classrooms for better performance
        from django.core.cache import cache
        
        # Try to get subjects from cache
        cache_key_subjects = 'active_subjects_for_form'
        subjects = cache.get(cache_key_subjects)
        if subjects is None:
            subjects = Subject.objects.filter(
                is_active=True
            ).only('id', 'name', 'category').order_by('category', 'name')
            # Cache for 5 minutes
            cache.set(cache_key_subjects, list(subjects), 300)
        
        self.fields['subject_ids'].queryset = Subject.objects.filter(
            id__in=[s.id if hasattr(s, 'id') else s['id'] for s in subjects]
        ).only('id', 'name', 'category')
        
        # Try to get classrooms from cache
        cache_key_classrooms = 'active_classrooms_for_form'
        classrooms = cache.get(cache_key_classrooms)
        if classrooms is None:
            classrooms = Classroom.objects.filter(
                is_active=True
            ).select_related('academic_level').only(
                'id', 'name', 'grade', 'section',
                'academic_level__code'
            ).order_by(
                'academic_level__code', 'grade', 'section'
            )
            # Cache for 5 minutes
            cache.set(cache_key_classrooms, list(classrooms), 300)
        
        self.fields['homeroom_class'].queryset = Classroom.objects.filter(
            id__in=[c.id if hasattr(c, 'id') else c['id'] for c in classrooms]
        ).select_related('academic_level').only(
            'id', 'name', 'grade', 'section', 'academic_level__code'
        )
        self.fields['homeroom_class'].required = False
        
        # Set initial subjects if editing existing teacher (optimized)
        # Only fetch IDs, not full objects
        if self.instance and self.instance.pk:
            # Use values_list for faster query
            subject_ids = self.instance.subjects.values_list('id', flat=True)
            self.fields['subject_ids'].initial = list(subject_ids)
    
    def clean_nip(self):
        """Validate and normalize NIP"""
        nip = self.cleaned_data.get('nip', '').strip().upper()
        
        # Validate length
        if len(nip) < 1 or len(nip) > 20:
            raise ValidationError('NIP harus 1-20 karakter')
        
        # Validate alphanumeric
        if not nip.isalnum():
            raise ValidationError('NIP harus berisi huruf dan angka saja')
        
        # Check uniqueness (excluding current instance)
        existing = Teacher.objects.filter(nip=nip)
        if self.instance and self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise ValidationError(f'NIP "{nip}" sudah digunakan')
        
        return nip
    
    def clean_full_name(self):
        """Validate teacher name"""
        name = self.cleaned_data.get('full_name', '').strip()
        
        if len(name) < 3:
            raise ValidationError('Nama lengkap minimal 3 karakter')
        
        # Check for numbers in name
        if any(char.isdigit() for char in name):
            raise ValidationError('Nama tidak boleh mengandung angka')
        
        return name
    
    def clean_photo(self):
        """Validate photo upload"""
        photo = self.cleaned_data.get('photo')
        
        if photo:
            # Check file size (max 5MB)
            max_size = 5 * 1024 * 1024  # 5MB in bytes
            if photo.size > max_size:
                raise ValidationError('Ukuran foto maksimal 5MB')
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
            if photo.content_type not in allowed_types:
                raise ValidationError('Format foto harus JPG atau PNG')
        
        return photo
    
    def clean_email(self):
        """Validate email format"""
        email = self.cleaned_data.get('email', '').strip().lower()
        
        if email:
            # Check uniqueness (excluding current instance)
            existing = Teacher.objects.filter(email=email)
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(f'Email "{email}" sudah digunakan')
        
        return email
    
    def clean_phone(self):
        """Validate phone number"""
        phone = self.cleaned_data.get('phone', '').strip()
        
        if phone:
            # Remove common separators
            phone = phone.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
            
            # Validate numeric
            if not phone.isdigit():
                raise ValidationError('Nomor telepon harus berisi angka saja')
            
            # Validate length (Indonesian phone numbers)
            if len(phone) < 10 or len(phone) > 15:
                raise ValidationError('Nomor telepon harus 10-15 digit')
        
        return phone
    
    def clean_employment_date(self):
        """Validate employment date"""
        employment_date = self.cleaned_data.get('employment_date')
        
        if employment_date:
            # Check if date is not in the future
            if employment_date > timezone.now().date():
                raise ValidationError('Tanggal mulai kerja tidak boleh di masa depan')
        
        return employment_date
    
    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        is_homeroom = cleaned_data.get('is_homeroom_teacher')
        homeroom_class = cleaned_data.get('homeroom_class')
        
        # Validate homeroom_class is set if is_homeroom_teacher is True
        if is_homeroom and not homeroom_class:
            raise ValidationError({
                'homeroom_class': 'Kelas harus dipilih jika ustadz/ustadzah adalah wali kelas'
            })
        
        # Clear homeroom_class if not homeroom teacher
        if not is_homeroom:
            cleaned_data['homeroom_class'] = None
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save teacher and handle subject assignments"""
        teacher = super().save(commit=commit)
        
        if commit:
            # Handle subject assignments
            subject_ids = self.cleaned_data.get('subject_ids')
            if subject_ids is not None:
                teacher.subjects.set(subject_ids)
        
        return teacher


class TeacherScheduleForm(forms.ModelForm):
    """Form for creating and editing teacher schedules with conflict detection"""
    
    class Meta:
        model = TeacherSchedule
        fields = [
            'teacher', 'subject', 'classroom',
            'day_of_week', 'jp_start', 'jp_end',
            'room_number', 'notes',
            'effective_date', 'end_date', 'is_active'
        ]
        widgets = {
            'teacher': forms.Select(attrs={
                'class': 'form-select'
            }),
            'subject': forms.Select(attrs={
                'class': 'form-select'
            }),
            'classroom': forms.Select(attrs={
                'class': 'form-select'
            }),
            'day_of_week': forms.Select(attrs={
                'class': 'form-select'
            }),
            'jp_start': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'placeholder': '1-10'
            }),
            'jp_end': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'placeholder': '1-10'
            }),
            'room_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nomor ruangan (opsional)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Catatan tambahan (opsional)'
            }),
            'effective_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'teacher': 'Ustadz/Ustadzah',
            'subject': 'Mata Pelajaran',
            'classroom': 'Kelas',
            'day_of_week': 'Hari',
            'jp_start': 'JP Mulai',
            'jp_end': 'JP Selesai',
            'room_number': 'Nomor Ruangan',
            'notes': 'Catatan',
            'effective_date': 'Tanggal Berlaku',
            'end_date': 'Tanggal Berakhir',
            'is_active': 'Aktif',
        }
        help_texts = {
            'jp_start': 'Jam Pelajaran mulai (1-10)',
            'jp_end': 'Jam Pelajaran selesai (1-10)',
            'effective_date': 'Tanggal mulai berlaku jadwal ini',
            'end_date': 'Tanggal berakhir jadwal (opsional)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter only active teachers
        self.fields['teacher'].queryset = Teacher.objects.filter(
            is_active=True
        ).order_by('full_name')
        
        # Filter only active subjects
        self.fields['subject'].queryset = Subject.objects.filter(
            is_active=True
        ).order_by('category', 'name')
        
        # Filter only active classrooms
        self.fields['classroom'].queryset = Classroom.objects.filter(
            is_active=True
        ).select_related('academic_level').order_by(
            'academic_level__code', 'grade', 'section'
        )
        
        # Set default effective_date to today if creating new schedule
        if not self.instance.pk:
            self.fields['effective_date'].initial = timezone.now().date()
        
        # Make end_date optional
        self.fields['end_date'].required = False
    
    def clean_jp_start(self):
        """Validate JP start"""
        jp_start = self.cleaned_data.get('jp_start')
        
        if jp_start is not None:
            if jp_start < 1 or jp_start > 10:
                raise ValidationError('JP mulai harus antara 1 dan 10')
        
        return jp_start
    
    def clean_jp_end(self):
        """Validate JP end"""
        jp_end = self.cleaned_data.get('jp_end')
        
        if jp_end is not None:
            if jp_end < 1 or jp_end > 10:
                raise ValidationError('JP selesai harus antara 1 dan 10')
        
        return jp_end
    
    def clean(self):
        """Cross-field validation and conflict detection"""
        cleaned_data = super().clean()
        
        teacher = cleaned_data.get('teacher')
        classroom = cleaned_data.get('classroom')
        day_of_week = cleaned_data.get('day_of_week')
        jp_start = cleaned_data.get('jp_start')
        jp_end = cleaned_data.get('jp_end')
        effective_date = cleaned_data.get('effective_date')
        end_date = cleaned_data.get('end_date')
        
        # Validate jp_end >= jp_start
        if jp_start is not None and jp_end is not None:
            if jp_end < jp_start:
                raise ValidationError({
                    'jp_end': 'JP selesai harus lebih besar atau sama dengan JP mulai'
                })
        
        # Validate effective_date <= end_date
        if effective_date and end_date:
            if effective_date > end_date:
                raise ValidationError({
                    'end_date': 'Tanggal berakhir harus lebih besar atau sama dengan tanggal berlaku'
                })
        
        # Detect scheduling conflicts using ScheduleService
        if teacher and day_of_week is not None and jp_start and jp_end:
            try:
                conflicts = ScheduleService.detect_conflicts(
                    teacher_id=teacher.id,
                    day=day_of_week,
                    jp_start=jp_start,
                    jp_end=jp_end,
                    effective_date=effective_date,
                    end_date=end_date,
                    exclude_schedule_id=self.instance.pk if self.instance.pk else None
                )
                
                if conflicts:
                    conflict_messages = []
                    for conflict in conflicts:
                        if conflict['type'] == 'teacher':
                            msg = (
                                f"Ustadz/Ustadzah {conflict['teacher_name']} sudah memiliki jadwal "
                                f"pada {conflict['day_name']} JP {conflict['jp_start']}-{conflict['jp_end']} "
                                f"({conflict['subject_name']})"
                            )
                            conflict_messages.append(msg)
                        elif conflict['type'] == 'classroom':
                            msg = (
                                f"Kelas {conflict['classroom_name']} sudah dijadwalkan "
                                f"pada {conflict['day_name']} JP {conflict['jp_start']}-{conflict['jp_end']} "
                                f"dengan {conflict['teacher_name']} ({conflict['subject_name']})"
                            )
                            conflict_messages.append(msg)
                    
                    if conflict_messages:
                        raise ValidationError({
                            'jp_start': 'Konflik jadwal ditemukan: ' + '; '.join(conflict_messages)
                        })
            
            except Exception as e:
                # If ScheduleService is not available or error occurs, fall back to basic validation
                # This allows the form to work even if service layer has issues
                pass
        
        return cleaned_data
