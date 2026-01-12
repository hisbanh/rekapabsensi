# SIPA YAUMI - Sistem Informasi Presensi Pesantren Yaumi

## Overview

SIPA YAUMI adalah sistem informasi presensi berbasis web yang dirancang khusus untuk Pesantren Yaumi Yogyakarta. Sistem ini dibangun menggunakan arsitektur enterprise-grade dengan Django 6.0 dan mengikuti best practices dalam pengembangan software.

## Features

### Core Features
- **Dashboard Komprehensif**: Statistik real-time kehadiran siswa
- **Manajemen Siswa**: CRUD lengkap dengan validasi data
- **Pencatatan Absensi**: Bulk attendance recording dengan validasi
- **Laporan & Analytics**: Laporan detail dengan filter dan export CSV
- **Audit Trail**: Logging semua aktivitas sistem untuk keamanan

### Advanced Features
- **Service Layer Architecture**: Pemisahan business logic dari presentation layer
- **Enterprise Security**: Audit logging, session management, CSRF protection
- **Performance Optimization**: Database indexing, query optimization
- **Responsive Design**: Bootstrap 5 dengan desain modern
- **Real-time Charts**: Visualisasi data dengan Chart.js

## Architecture

### System Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Presentation  │    │   Business      │    │   Data Access   │
│     Layer       │◄──►│     Layer       │◄──►│     Layer       │
│   (Views/Forms) │    │   (Services)    │    │   (Models/DB)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Directory Structure
```
sipa_yaumi/
├── attendance/                 # Main application
│   ├── services/              # Business logic layer
│   │   ├── attendance_service.py
│   │   ├── student_service.py
│   │   └── report_service.py
│   ├── models.py              # Data models
│   ├── views.py               # Presentation layer
│   ├── admin.py               # Admin interface
│   ├── forms.py               # Form definitions
│   ├── middleware.py          # Custom middleware
│   └── exceptions.py          # Custom exceptions
├── templates/                 # HTML templates
├── static/                    # Static files
└── requirements.txt           # Dependencies
```

## Installation

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Setup Instructions

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd rekap-absensi
   ```

2. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

5. **Database Setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Populate Initial Data**
   ```bash
   python manage.py populate_students
   ```

8. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

## Configuration

### Environment Variables
Create a `.env` file based on `.env.example`:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Application Settings
Configure application-specific settings in `settings.py`:

```python
SIPA_YAUMI = {
    'SCHOOL_NAME': 'PESANTREN YAUMI YOGYAKARTA',
    'APP_NAME': 'SIPA YAUMI',
    'VERSION': '2.0.0',
    'PAGINATION_SIZE': 20,
    'MAX_EXPORT_RECORDS': 10000,
}
```

## Usage

### Accessing the System
1. **Main Application**: http://127.0.0.1:8000/
2. **Admin Panel**: http://127.0.0.1:8000/admin/

### Key Workflows

#### 1. Taking Attendance
1. Navigate to "Ambil Absensi"
2. Select date and class
3. Mark attendance status for each student
4. Add notes if necessary
5. Save attendance records

#### 2. Viewing Reports
1. Go to "Laporan Absensi"
2. Apply filters (date range, class, status)
3. View paginated results
4. Export to CSV if needed

#### 3. Student Management
1. Access "Data Siswa"
2. Search and filter students
3. View individual student details
4. Check attendance history and statistics

## API Endpoints

### REST API
- `GET /api/stats/` - Attendance statistics
- `GET /students/` - Student list with filters
- `POST /attendance/` - Bulk attendance creation

### Export Endpoints
- `GET /export/` - CSV export with filters

## Database Schema

### Core Models
- **Student**: Student information and profile
- **AttendanceRecord**: Daily attendance records
- **AttendanceSummary**: Monthly aggregated data
- **AuditLog**: System activity logging

### Relationships
```
Student (1) ──── (N) AttendanceRecord
Student (1) ──── (N) AttendanceSummary
User (1) ──── (N) AttendanceRecord
User (1) ──── (N) AuditLog
```

## Security Features

### Authentication & Authorization
- Django's built-in authentication system
- Session-based authentication
- CSRF protection
- Permission-based access control

### Audit & Monitoring
- Comprehensive audit logging
- IP address tracking
- User activity monitoring
- Security headers implementation

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- Secure session management

## Performance Optimization

### Database Optimization
- Strategic database indexing
- Query optimization with select_related/prefetch_related
- Pagination for large datasets
- Connection pooling ready

### Caching Strategy
- Template caching in production
- Redis support for session storage
- Query result caching capabilities

## Testing

### Running Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test attendance

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Test Structure
- Unit tests for models and services
- Integration tests for views
- Form validation tests
- API endpoint tests

## Deployment

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Configure proper database (PostgreSQL/MySQL)
- [ ] Set up Redis for caching
- [ ] Configure email settings
- [ ] Set up static file serving
- [ ] Configure logging
- [ ] Set up monitoring (Sentry)

### Docker Deployment
```bash
# Build image
docker build -t sipa-yaumi .

# Run container
docker run -p 8000:8000 sipa-yaumi
```

## Monitoring & Maintenance

### Logging
- Application logs: `logs/django.log`
- Audit logs: Database table `attendance_auditlog`
- Error tracking: Sentry integration ready

### Backup Strategy
- Database backups: Daily automated
- Media files: Regular sync
- Configuration: Version controlled

## Contributing

### Development Guidelines
1. Follow PEP 8 style guide
2. Write comprehensive tests
3. Document all functions and classes
4. Use type hints where applicable
5. Follow the service layer pattern

### Code Quality Tools
```bash
# Code formatting
black .
isort .

# Linting
flake8

# Type checking
mypy attendance/
```

## Support & Documentation

### Technical Support
- Email: support@sipayaumi.com
- Documentation: Internal wiki
- Issue tracking: GitHub Issues

### System Requirements
- **Minimum**: 2GB RAM, 10GB storage
- **Recommended**: 4GB RAM, 50GB storage
- **Database**: SQLite (dev), PostgreSQL (prod)

## License

This project is proprietary software developed for Pesantren Yaumi Yogyakarta.

## Changelog

### Version 2.0.0 (Current)
- Enterprise architecture implementation
- Service layer pattern
- Enhanced security features
- Comprehensive audit logging
- Performance optimizations
- Modern UI/UX design

### Version 1.0.0
- Basic attendance functionality
- Student management
- Simple reporting

---

**SIPA YAUMI** - Sistem Informasi Presensi Pesantren Yaumi
Developed with ❤️ for Pesantren Yaumi Yogyakarta