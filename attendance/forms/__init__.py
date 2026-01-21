"""
Forms package for attendance application
"""
# Import teacher forms from this package
from .teacher_forms import (
    SubjectForm,
    TeacherForm,
    TeacherScheduleForm,
)

# Import attendance forms
from .attendance_forms import (
    AttendanceFilterForm,
)

# Import all other forms from the legacy forms.py file
# We'll re-export them here for backwards compatibility
import sys
import os

# Add parent directory to path to import from forms.py
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import from the attendance.forms module (the forms.py file)
# This works because Python will find forms.py before the forms/ package
# when importing from the parent attendance module
try:
    # Import the forms.py module directly
    import importlib
    forms_module = importlib.import_module('attendance.forms', package='attendance')
    
    # Get all the forms we need
    StudentForm = getattr(forms_module, 'StudentForm', None)
    StudentFilterForm = getattr(forms_module, 'StudentFilterForm', None)
    ClassroomForm = getattr(forms_module, 'ClassroomForm', None)
    HolidayForm = getattr(forms_module, 'HolidayForm', None)
    DayScheduleForm = getattr(forms_module, 'DayScheduleForm', None)
    UserForm = getattr(forms_module, 'UserForm', None)
    JPReportFilterForm = getattr(forms_module, 'JPReportFilterForm', None)
    BulkAttendanceForm = getattr(forms_module, 'BulkAttendanceForm', None)
except (ImportError, AttributeError) as e:
    # If import fails, set to None
    StudentForm = None
    StudentFilterForm = None
    ClassroomForm = None
    HolidayForm = None
    DayScheduleForm = None
    UserForm = None
    JPReportFilterForm = None
    BulkAttendanceForm = None

__all__ = [
    # Teacher forms
    'SubjectForm',
    'TeacherForm',
    'TeacherScheduleForm',
    # Attendance forms
    'AttendanceFilterForm',
    # Legacy forms from forms.py
    'StudentForm',
    'StudentFilterForm',
    'ClassroomForm',
    'HolidayForm',
    'DayScheduleForm',
    'UserForm',
    'JPReportFilterForm',
    'BulkAttendanceForm',
]
