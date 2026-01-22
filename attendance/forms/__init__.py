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

# Import teacher attendance forms
from .teacher_attendance_forms import (
    TeacherAttendanceForm,
    BulkAttendanceForm as TeacherBulkAttendanceForm,
)

# Import legacy forms from forms.py file
# We need to import from the parent module to avoid circular imports
# The forms.py file exists at attendance/forms.py (sibling to this package)
import sys
import importlib.util

# Initialize forms to None
StudentForm = None
StudentFilterForm = None
ClassroomForm = None
HolidayForm = None
DayScheduleForm = None
UserForm = None
JPReportFilterForm = None
BulkAttendanceForm = None

try:
    # Import from attendance.forms module (the .py file, not this package)
    # We need to temporarily manipulate sys.modules to avoid the circular reference
    
    # Save the current attendance.forms module (this package)
    current_forms_module = sys.modules.get('attendance.forms')
    
    # Temporarily remove it so we can import the .py file
    if 'attendance.forms' in sys.modules:
        del sys.modules['attendance.forms']
    
    # Now import the forms.py file as a different module name
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    forms_py_path = os.path.join(os.path.dirname(current_dir), 'forms.py')
    
    if os.path.exists(forms_py_path):
        spec = importlib.util.spec_from_file_location("attendance.legacy_forms", forms_py_path)
        legacy_forms = importlib.util.module_from_spec(spec)
        sys.modules['attendance.legacy_forms'] = legacy_forms
        spec.loader.exec_module(legacy_forms)
        
        # Extract the forms we need
        StudentForm = getattr(legacy_forms, 'StudentForm', None)
        StudentFilterForm = getattr(legacy_forms, 'StudentFilterForm', None)
        ClassroomForm = getattr(legacy_forms, 'ClassroomForm', None)
        HolidayForm = getattr(legacy_forms, 'HolidayForm', None)
        DayScheduleForm = getattr(legacy_forms, 'DayScheduleForm', None)
        UserForm = getattr(legacy_forms, 'UserForm', None)
        JPReportFilterForm = getattr(legacy_forms, 'JPReportFilterForm', None)
        BulkAttendanceForm = getattr(legacy_forms, 'BulkAttendanceForm', None)
    
    # Restore the current module
    if current_forms_module:
        sys.modules['attendance.forms'] = current_forms_module
        
except Exception as e:
    import traceback
    print(f"Warning: Could not load legacy forms from forms.py: {e}")
    traceback.print_exc()
    
    # Make sure to restore the module even on error
    if current_forms_module:
        sys.modules['attendance.forms'] = current_forms_module

__all__ = [
    # Teacher forms
    'SubjectForm',
    'TeacherForm',
    'TeacherScheduleForm',
    # Teacher attendance forms
    'TeacherAttendanceForm',
    'TeacherBulkAttendanceForm',
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
