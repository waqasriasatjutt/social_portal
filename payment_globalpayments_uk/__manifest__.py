{
    'name': 'Global Payments UK Payment Gateway',
    'version': '1.0',
    'summary': 'Integrate Global Payments UK with Odoo 17',
    'description': 'This module provides integration with Global Payments UK for processing payments.',
    'author': 'Your Name',
    'category': 'Accounting/Payment',
    'depends': ['payment'],
    'data': [
        'views/payment_acquirer_views.xml',
        'views/payment_provider_views.xml',
        'data/payment_acquirer_data.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
