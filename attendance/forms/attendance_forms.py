"""
Attendance-related forms
"""
from django import forms
from django.utils import timezone
from attendance.models import Classroom, AttendanceStatus


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
