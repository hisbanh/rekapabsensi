"""
Student Service Layer
Handles all business logic related to student management
"""
from typing import List, Dict, Optional
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError

from ..models import Student, AttendanceRecord, Classroom, AcademicLevel
from ..exceptions import StudentServiceError


class StudentService:
    """Service class for student-related business operations"""
    
    @staticmethod
    def get_students_with_filters(
        classroom_id: str = None,
        academic_level: str = None,
        grade: int = None,
        search_query: str = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict:
        """Get filtered and paginated students"""
        queryset = Student.objects.select_related(
            'classroom', 'classroom__academic_level'
        ).all()
        
        # Apply filters
        if classroom_id:
            queryset = queryset.filter(classroom_id=classroom_id)
            
        if academic_level:
            queryset = queryset.filter(classroom__academic_level__code=academic_level)
            
        if grade:
            queryset = queryset.filter(classroom__grade=grade)
            
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(student_id__icontains=search_query) |
                Q(nisn__icontains=search_query)
            )
        
        # Order by classroom and name
        queryset = queryset.order_by(
            'classroom__academic_level__code',
            'classroom__grade',
            'classroom__section',
            'name'
        )
        
        # Pagination
        paginator = Paginator(queryset, per_page)
        students_page = paginator.get_page(page)
        
        return {
            'students': students_page,
            'total_count': paginator.count,
            'page_count': paginator.num_pages,
            'current_page': page,
            'has_previous': students_page.has_previous(),
            'has_next': students_page.has_next(),
        }
    
    @staticmethod
    def get_classroom_list() -> List[Classroom]:
        """Get list of all classrooms"""
        return list(
            Classroom.objects.select_related('academic_level')
            .filter(is_active=True)
            .order_by('academic_level__code', 'grade', 'section')
        )
    
    @staticmethod
    def get_academic_levels() -> List[AcademicLevel]:
        """Get list of all academic levels"""
        return list(
            AcademicLevel.objects.filter(is_active=True)
            .order_by('level_type', 'code')
        )
    
    @staticmethod
    def get_students_by_classroom(classroom_id: str) -> List[Student]:
        """Get all students in a specific classroom"""
        return list(
            Student.objects.filter(classroom_id=classroom_id, is_active=True)
            .order_by('name')
        )
    
    @staticmethod
    def get_students_by_grade(grade: int) -> List[Student]:
        """Get all students in a specific grade"""
        return list(
            Student.objects.filter(classroom__grade=grade, is_active=True)
            .select_related('classroom', 'classroom__academic_level')
            .order_by('classroom__section', 'name')
        )
    
    @staticmethod
    def get_student_detail(student_id: str) -> Optional[Student]:
        """Get student by ID with error handling"""
        try:
            return Student.objects.select_related(
                'classroom', 'classroom__academic_level'
            ).get(student_id=student_id)
        except Student.DoesNotExist:
            return None
    
    @staticmethod
    def validate_student_data(student_data: Dict) -> List[str]:
        """Validate student data"""
        errors = []
        
        required_fields = ['student_id', 'name', 'classroom']
        for field in required_fields:
            if not student_data.get(field):
                errors.append(f"Field '{field}' is required")
        
        # Check for duplicate student_id
        if student_data.get('student_id'):
            existing = Student.objects.filter(
                student_id=student_data['student_id']
            ).exists()
            if existing:
                errors.append(f"Student ID '{student_data['student_id']}' already exists")
        
        # Validate classroom exists
        if student_data.get('classroom'):
            if isinstance(student_data['classroom'], str):
                try:
                    Classroom.objects.get(id=student_data['classroom'])
                except Classroom.DoesNotExist:
                    errors.append(f"Classroom with ID '{student_data['classroom']}' does not exist")
        
        return errors
    
    @staticmethod
    def create_student(student_data: Dict) -> Student:
        """Create a new student with validation"""
        errors = StudentService.validate_student_data(student_data)
        if errors:
            raise StudentServiceError(f"Validation errors: {', '.join(errors)}")
        
        return Student.objects.create(**student_data)
    
    @staticmethod
    def update_student(student_id: str, student_data: Dict) -> Student:
        """Update existing student"""
        try:
            student = Student.objects.get(student_id=student_id)
            
            for field, value in student_data.items():
                if hasattr(student, field):
                    setattr(student, field, value)
            
            student.full_clean()
            student.save()
            return student
            
        except Student.DoesNotExist:
            raise StudentServiceError(f"Student with ID '{student_id}' not found")
        except ValidationError as e:
            raise StudentServiceError(f"Validation error: {e}")
    
    @staticmethod
    def get_classroom_statistics() -> List[Dict]:
        """Get statistics for each classroom"""
        classrooms = StudentService.get_classroom_list()
        stats = []
        
        for classroom in classrooms:
            student_count = Student.objects.filter(
                classroom=classroom, is_active=True
            ).count()
            stats.append({
                'classroom': classroom,
                'classroom_name': str(classroom),
                'academic_level': classroom.academic_level.code,
                'grade': classroom.grade,
                'section': classroom.section,
                'student_count': student_count,
                'capacity': classroom.capacity,
                'utilization_rate': (student_count / classroom.capacity * 100) if classroom.capacity > 0 else 0
            })
        
        return stats
    
    @staticmethod
    def get_academic_level_statistics() -> List[Dict]:
        """Get statistics for each academic level"""
        academic_levels = StudentService.get_academic_levels()
        stats = []
        
        for level in academic_levels:
            student_count = Student.objects.filter(
                classroom__academic_level=level, is_active=True
            ).count()
            classroom_count = Classroom.objects.filter(
                academic_level=level, is_active=True
            ).count()
            
            stats.append({
                'academic_level': level,
                'level_name': level.name,
                'level_code': level.code,
                'student_count': student_count,
                'classroom_count': classroom_count,
                'grade_range': level.grade_range
            })
        
        return stats
    
    # Backward compatibility methods
    @staticmethod
    def get_class_list() -> List[str]:
        """Get list of all classroom names (backward compatibility)"""
        classrooms = StudentService.get_classroom_list()
        return [str(classroom) for classroom in classrooms]
    
    @staticmethod
    def get_students_by_class(class_name: str) -> List[Student]:
        """Get students by class name (backward compatibility)"""
        # Try to parse class name and find matching classroom
        try:
            # Handle different formats: "7-A", "11", "12", etc.
            if '-' in class_name:
                grade_str, section = class_name.split('-', 1)
                grade = int(grade_str)
                classroom = Classroom.objects.get(grade=grade, section=section)
            else:
                grade = int(class_name)
                classroom = Classroom.objects.get(grade=grade, section='')
            
            return StudentService.get_students_by_classroom(str(classroom.id))
        except (ValueError, Classroom.DoesNotExist):
            return []
    
    @staticmethod
    def get_class_statistics() -> List[Dict]:
        """Get class statistics (backward compatibility)"""
        return StudentService.get_classroom_statistics()