{
    'name': 'HRIS REST API',
    'version': '1.0.0',
    'category': 'Human Resources',
    'summary': 'REST API for HRIS Flutter Application',
    'description': """
        This module provides REST API endpoints for the HRIS Flutter application.
        It includes authentication, employee management, leave management, and other HR features.
    """,    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',    'depends': [
        'base',
        'hr',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/api_endpoints.xml',
        'data/leave_types_demo.xml',
        'data/company_coordinates.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
