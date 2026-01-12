from django import forms
from django.utils import timezone
from .models import AttendanceRecord, AttendanceStatus, Student

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
    class_name = forms.ChoiceField(
        required=False,
        choices=[('', 'Semua Kelas')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Semua Status')] + list(AttendanceStatus.choices),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate class choices dynamically
        classes = Student.objects.values_list('class_name', flat=True).distinct().order_by('class_name')
        class_choices = [('', 'Semua Kelas')] + [(cls, cls) for cls in classes]
        self.fields['class_name'].choices = class_choices

class BulkAttendanceForm(forms.Form):
    date = forms.DateField(
        initial=timezone.now().date(),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    class_name = forms.ChoiceField(
        choices=[('', 'Pilih Kelas')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate class choices dynamically
        classes = Student.objects.values_list('class_name', flat=True).distinct().order_by('class_name')
        class_choices = [('', 'Pilih Kelas')] + [(cls, cls) for cls in classes]
        self.fields['class_name'].choices = class_choices