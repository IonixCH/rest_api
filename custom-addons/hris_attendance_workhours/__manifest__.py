{
    'name': 'HRIS Attendance Working Hours',
    'version': '17.0.1.0.0',
    'summary': 'Add working hours field to attendance',
    'description': """
        This module adds working hours calculation field to hr.attendance model
        to display formatted working hours (HH:MM:SS) in attendance views.
    """,
    'author': 'HRIS Team',
    'website': '',
    'category': 'Human Resources',
    'license': 'LGPL-3',
    'depends': ['hr_attendance', 'hris_attendance_gps'],
    'data': [
        'views/hr_attendance_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
