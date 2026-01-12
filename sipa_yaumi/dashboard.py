"""
Custom Grappelli dashboard for SIPA Beta 
"""
from django.utils.translation import gettext_lazy as _
from grappelli.dashboard import modules, Dashboard
from grappelli.dashboard.utils import get_admin_site_name


class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard for SIPA Beta  admin.
    """

    def init_with_context(self, context):
        site_name = get_admin_site_name(context)
        
        # append a group for "Administration" & "Applications"
        self.children.append(modules.Group(
            _('Manajemen Siswa'),
            column=1,
            collapsible=True,
            children = [
                modules.AppList(
                    _('Siswa & Kelas'),
                    column=1,
                    collapsible=True,
                    models=('attendance.models.Student', 'attendance.models.Classroom', 'attendance.models.AcademicLevel'),
                ),
            ]
        ))

        # append a group for "Attendance"
        self.children.append(modules.Group(
            _('Manajemen Absensi'),
            column=1,
            collapsible=True,
            children = [
                modules.AppList(
                    _('Absensi & Laporan'),
                    column=1,
                    collapsible=True,
                    models=('attendance.models.AttendanceRecord', 'attendance.models.AttendanceSummary'),
                ),
            ]
        ))

        # append a group for "System"
        self.children.append(modules.Group(
            _('Sistem & Audit'),
            column=1,
            collapsible=True,
            children = [
                modules.AppList(
                    _('Sistem'),
                    column=1,
                    collapsible=True,
                    models=('attendance.models.AuditLog', 'django.contrib.auth.*'),
                ),
            ]
        ))

        # append a link list module for "quick links"
        self.children.append(modules.LinkList(
            _('Quick Links'),
            column=2,
            children=[
                [_('Dashboard Utama'), '/'],
                [_('Ambil Absensi'), '/attendance/take/'],
                [_('Daftar Siswa'), '/attendance/students/'],
                [_('Laporan'), '/attendance/reports/'],
                [_('Dokumentasi'), 'https://docs.djangoproject.com/'],
            ]
        ))

        # append a recent actions module
        self.children.append(modules.RecentActions(
            _('Recent Actions'),
            limit=10,
            collapsible=False,
            column=2,
        ))

        # append a feed module
        self.children.append(modules.Feed(
            _('Latest Django News'),
            column=2,
            feed_url='http://www.djangoproject.com/rss/weblog/',
            limit=5
        ))