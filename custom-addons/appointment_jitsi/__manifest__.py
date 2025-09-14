
{
    'name': 'Appointment Jitsi',
    'summary': 'Custom Module for Appointment, Integration With Jitsi API',
    'description': '''
        Custom Module for Appointment, Integration With Jitsi API.\n\nFeatures:\n1. Automatic Link Generation: When an appointment is created, a unique Jitsi meeting link is generated using the Jitsi API.\n2. Link Storage: The generated Jitsi meeting link is stored in a custom field within the appointment record in Odoo.\n3. Email Notification: Customizes the appointment confirmation email template to include the Jitsi meeting link.\n4. Security: Each link is unique to the appointment, ensuring the privacy and security of the meetings.
    ''',
    'author': 'Doodex',
    'company': 'Doodex',
    'website': 'https://www.doodex.net/',
    'category': 'Appointment',
    'license': 'LGPL-3',
    'version': '17.0.1.0.0',
    'depends': [
        'base',
        'appointment',
        'calendar',
        'website_slides',  # Tambahkan dependensi eLearning
    ],
    'data': [
        'views/calendar_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'images': ['static/description/banner.png'],
}
