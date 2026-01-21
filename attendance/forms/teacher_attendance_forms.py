"""
Forms for Teacher Attendance Management
Includes forms for recording teacher attendance with location validation
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from attendance.models import TeacherAttendance, Teacher, TeacherSchedule


class TeacherAttendanceForm(forms.ModelForm):
    """Form for recording individual teacher attendance per JP"""
    
    # Hidden location fields (populated by JavaScript)
    latitude = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(attrs={
            'id': 'id_latitude'
        })
    )
    longitude = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(attrs={
            'id': 'id_longitude'
        })
    )
    is_location_valid = forms.BooleanField(
        required=False,
        widget=forms.HiddenInput(attrs={
            'id': 'id_is_location_valid'
        })
    )
    
    class Meta:
        model = TeacherAttendance
        fields = [
            'teacher', 'schedule', 'date', 'jp_number', 'status',
            'notes', 'is_substitute', 'substitute_for',
            'latitude', 'longitude', 'is_location_valid'
        ]
        widgets = {
            'teacher': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_teacher'
            }),
            'schedule': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_schedule'
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'id_date'
            }),
            'jp_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'placeholder': '1-10',
                'id': 'id_jp_number'
            }),
            'status': forms.RadioSelect(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Catatan tambahan (opsional)',
                'id': 'id_notes'
            }),
            'is_substitute': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_is_substitute'
            }),
            'substitute_for': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_substitute_for'
            }),
        }
        labels = {
            'teacher': 'Ustadz/Ustadzah',
            'schedule': 'Jadwal Mengajar',
            'date': 'Tanggal',
            'jp_number': 'Jam Pelajaran (JP)',
            'status': 'Status Kehadiran',
            'notes': 'Catatan',
            'is_substitute': 'Mengajar Pengganti',
            'substitute_for': 'Menggantikan',
        }
        help_texts = {
            'teacher': 'Pilih ustadz/ustadzah',
            'schedule': 'Jadwal mengajar (opsional)',
            'date': 'Tanggal absensi',
            'jp_number': 'Nomor JP (1-10)',
            'status': 'Pilih status kehadiran',
            'notes': 'Keterangan tambahan jika diperlukan',
            'is_substitute': 'Centang jika mengajar pengganti',
            'substitute_for': 'Pilih ustadz/ustadzah yang digantikan',
        }
    
    def __init__(self, *args, **kwargs):
        # Extract user from kwargs if provided
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter only active teachers
        self.fields['teacher'].queryset = Teacher.objects.filter(
            is_active=True
        ).order_by('full_name')
        
        # Filter only active schedules
        self.fields['schedule'].queryset = TeacherSchedule.objects.filter(
            is_active=True
        ).select_related('teacher', 'subject', 'classroom').order_by(
            'day_of_week', 'jp_start'
        )
        self.fields['schedule'].required = False
        
        # Filter substitute_for to active teachers
        self.fields['substitute_for'].queryset = Teacher.objects.filter(
            is_active=True
        ).order_by('full_name')
        self.fields['substitute_for'].required = False
        
        # Set default date to today
        if not self.instance.pk:
            self.fields['date'].initial = timezone.now().date()
        
        # Make notes optional
        self.fields['notes'].required = False
    
    def clean_date(self):
        """Validate attendance date based on user role"""
        date = self.cleaned_data.get('date')
        
        if date:
            # Check if date is in the future
            if date > timezone.now().date():
                raise ValidationError('Tanggal absensi tidak boleh di masa depan')
            
            # For teachers (non-staff), limit to 7 days in the past
            if self.user and not self.user.is_staff:
                days_past = (timezone.now().date() - date).days
                if days_past > 7:
                    raise ValidationError(
                        'Ustadz/ustadzah hanya dapat mencatat absensi untuk 7 hari terakhir. '
                        'Hubungi admin untuk absensi tanggal lebih lama.'
                    )
        
        return date
    
    def clean_jp_number(self):
        """Validate JP number"""
        jp_number = self.cleaned_data.get('jp_number')
        
        if jp_number is not None:
            if jp_number < 1 or jp_number > 10:
                raise ValidationError('Nomor JP harus antara 1 dan 10')
        
        return jp_number
    
    def clean_latitude(self):
        """Validate latitude"""
        latitude = self.cleaned_data.get('latitude')
        
        if latitude is not None:
            if latitude < -90 or latitude > 90:
                raise ValidationError('Latitude harus antara -90 dan 90')
        
        return latitude
    
    def clean_longitude(self):
        """Validate longitude"""
        longitude = self.cleaned_data.get('longitude')
        
        if longitude is not None:
            if longitude < -180 or longitude > 180:
                raise ValidationError('Longitude harus antara -180 dan 180')
        
        return longitude
    
    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        
        teacher = cleaned_data.get('teacher')
        date = cleaned_data.get('date')
        jp_number = cleaned_data.get('jp_number')
        is_substitute = cleaned_data.get('is_substitute')
        substitute_for = cleaned_data.get('substitute_for')
        
        # Validate substitute logic
        if is_substitute and not substitute_for:
            raise ValidationError({
                'substitute_for': 'Pilih ustadz/ustadzah yang digantikan jika mengajar pengganti'
            })
        
        if substitute_for and not is_substitute:
            raise ValidationError({
                'is_substitute': 'Centang "Mengajar Pengganti" jika menggantikan ustadz/ustadzah lain'
            })
        
        # Check for duplicate attendance (excluding current instance)
        if teacher and date and jp_number:
            existing = TeacherAttendance.objects.filter(
                teacher=teacher,
                date=date,
                jp_number=jp_number
            )
            
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(
                    f'Absensi untuk {teacher.full_name} pada tanggal {date} JP {jp_number} sudah ada'
                )
        
        # Validate location for self-service (non-admin users)
        if self.user and not self.user.is_staff:
            latitude = cleaned_data.get('latitude')
            longitude = cleaned_data.get('longitude')
            is_location_valid = cleaned_data.get('is_location_valid')
            
            if not latitude or not longitude:
                raise ValidationError(
                    'Lokasi diperlukan untuk absensi mandiri. '
                    'Pastikan GPS aktif dan izinkan akses lokasi.'
                )
            
            if not is_location_valid:
                raise ValidationError(
                    'Lokasi Anda berada di luar area sekolah. '
                    'Absensi mandiri hanya dapat dilakukan dari dalam area sekolah.'
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save attendance record with recorded_by field"""
        attendance = super().save(commit=False)
        
        # Set recorded_by if user is provided
        if self.user:
            attendance.recorded_by = self.user
        
        if commit:
            attendance.save()
        
        return attendance


class BulkAttendanceForm(forms.Form):
    """Form for recording attendance for multiple JP at once"""
    
    teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.none(),
        label='Ustadz/Ustadzah',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_bulk_teacher'
        }),
        help_text='Pilih ustadz/ustadzah'
    )
    
    date = forms.DateField(
        label='Tanggal',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'id': 'id_bulk_date'
        }),
        help_text='Tanggal absensi'
    )
    
    # JP selection fields (1-10)
    jp_1_status = forms.ChoiceField(
        required=False,
        choices=[('', '-')] + TeacherAttendance.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        label='JP 1'
    )
    jp_2_status = forms.ChoiceField(
        required=False,
        choices=[('', '-')] + TeacherAttendance.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        label='JP 2'
    )
    jp_3_status = forms.ChoiceField(
        required=False,
        choices=[('', '-')] + TeacherAttendance.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        label='JP 3'
    )
    jp_4_status = forms.ChoiceField(
        required=False,
        choices=[('', '-')] + TeacherAttendance.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        label='JP 4'
    )
    jp_5_status = forms.ChoiceField(
        required=False,
        choices=[('', '-')] + TeacherAttendance.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        label='JP 5'
    )
    jp_6_status = forms.ChoiceField(
        required=False,
        choices=[('', '-')] + TeacherAttendance.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        label='JP 6'
    )
    jp_7_status = forms.ChoiceField(
        required=False,
        choices=[('', '-')] + TeacherAttendance.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        label='JP 7'
    )
    jp_8_status = forms.ChoiceField(
        required=False,
        choices=[('', '-')] + TeacherAttendance.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        label='JP 8'
    )
    jp_9_status = forms.ChoiceField(
        required=False,
        choices=[('', '-')] + TeacherAttendance.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        label='JP 9'
    )
    jp_10_status = forms.ChoiceField(
        required=False,
        choices=[('', '-')] + TeacherAttendance.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        label='JP 10'
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Catatan umum untuk semua JP (opsional)',
            'id': 'id_bulk_notes'
        }),
        label='Catatan',
        help_text='Catatan yang akan diterapkan ke semua JP'
    )
    
    # Hidden location fields (populated by JavaScript)
    latitude = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_bulk_latitude'})
    )
    longitude = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_bulk_longitude'})
    )
    is_location_valid = forms.BooleanField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_bulk_is_location_valid'})
    )
    
    def __init__(self, *args, **kwargs):
        # Extract user from kwargs if provided
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter only active teachers
        self.fields['teacher'].queryset = Teacher.objects.filter(
            is_active=True
        ).order_by('full_name')
        
        # Set default date to today
        if not self.data.get('date'):
            self.initial['date'] = timezone.now().date()
    
    def clean_date(self):
        """Validate attendance date based on user role"""
        date = self.cleaned_data.get('date')
        
        if date:
            # Check if date is in the future
            if date > timezone.now().date():
                raise ValidationError('Tanggal absensi tidak boleh di masa depan')
            
            # For teachers (non-staff), limit to 7 days in the past
            if self.user and not self.user.is_staff:
                days_past = (timezone.now().date() - date).days
                if days_past > 7:
                    raise ValidationError(
                        'Ustadz/ustadzah hanya dapat mencatat absensi untuk 7 hari terakhir. '
                        'Hubungi admin untuk absensi tanggal lebih lama.'
                    )
        
        return date
    
    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        
        # Check if at least one JP status is selected
        has_status = False
        for i in range(1, 11):
            jp_status = cleaned_data.get(f'jp_{i}_status')
            if jp_status:
                has_status = True
                break
        
        if not has_status:
            raise ValidationError('Pilih minimal satu status JP untuk dicatat')
        
        # Validate location for self-service (non-admin users)
        if self.user and not self.user.is_staff:
            latitude = cleaned_data.get('latitude')
            longitude = cleaned_data.get('longitude')
            is_location_valid = cleaned_data.get('is_location_valid')
            
            if not latitude or not longitude:
                raise ValidationError(
                    'Lokasi diperlukan untuk absensi mandiri. '
                    'Pastikan GPS aktif dan izinkan akses lokasi.'
                )
            
            if not is_location_valid:
                raise ValidationError(
                    'Lokasi Anda berada di luar area sekolah. '
                    'Absensi mandiri hanya dapat dilakukan dari dalam area sekolah.'
                )
        
        return cleaned_data
    
    def get_jp_statuses(self):
        """Get dictionary of JP numbers and their statuses"""
        jp_statuses = {}
        for i in range(1, 11):
            status = self.cleaned_data.get(f'jp_{i}_status')
            if status:
                jp_statuses[i] = status
        return jp_statuses
    
    def save(self, commit=True):
        """
        Save multiple attendance records (one per JP with status)
        Returns tuple: (created_count, error_list)
        """
        if not commit:
            return (0, [])
        
        teacher = self.cleaned_data.get('teacher')
        date = self.cleaned_data.get('date')
        notes = self.cleaned_data.get('notes', '')
        latitude = self.cleaned_data.get('latitude')
        longitude = self.cleaned_data.get('longitude')
        is_location_valid = self.cleaned_data.get('is_location_valid', False)
        
        jp_statuses = self.get_jp_statuses()
        
        created_count = 0
        errors = []
        
        for jp_number, status in jp_statuses.items():
            try:
                # Check if attendance already exists
                existing = TeacherAttendance.objects.filter(
                    teacher=teacher,
                    date=date,
                    jp_number=jp_number
                ).first()
                
                if existing:
                    # Update existing record
                    existing.status = status
                    existing.notes = notes
                    existing.latitude = latitude
                    existing.longitude = longitude
                    existing.is_location_valid = is_location_valid
                    if self.user:
                        existing.updated_by = self.user
                    existing.save()
                    created_count += 1
                else:
                    # Create new record
                    attendance = TeacherAttendance(
                        teacher=teacher,
                        date=date,
                        jp_number=jp_number,
                        status=status,
                        notes=notes,
                        latitude=latitude,
                        longitude=longitude,
                        is_location_valid=is_location_valid,
                        recorded_by=self.user if self.user else None
                    )
                    attendance.save()
                    created_count += 1
            
            except Exception as e:
                errors.append(f'JP {jp_number}: {str(e)}')
        
        return (created_count, errors)
