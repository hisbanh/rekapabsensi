"""
Utility functions for SIPA YAUMI
"""
from django.utils.translation import gettext_lazy as _


def environment_callback(request):
    """
    Callback to show environment info in admin
    """
    return ["Development", "warning"]  # [text, color]


def dashboard_callback(request, context):
    """
    Callback to customize dashboard
    """
    # Return additional context as a dictionary
    return {
        "custom_stats": [
            {
                "title": _("Quick Stats"),
                "metric": "278",
                "footer": _("Total Students"),
                "chart": '<div class="text-green-600">↗ 12%</div>',
            },
            {
                "title": _("Today's Attendance"),
                "metric": "95%",
                "footer": _("Attendance Rate"),
                "chart": '<div class="text-blue-600">→ 0%</div>',
            },
            {
                "title": _("Active Classes"),
                "metric": "10",
                "footer": _("Classrooms"),
                "chart": '<div class="text-purple-600">→ 0%</div>',
            },
            {
                "title": _("This Month"),
                "metric": "92%",
                "footer": _("Average Attendance"),
                "chart": '<div class="text-green-600">↗ 3%</div>',
            },
        ]
    }