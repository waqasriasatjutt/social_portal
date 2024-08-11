{
    'name': 'Global Payments Gateway',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Integrate Global Payments with Odoo 17',
    'description': 'Module for integrating Global Payments API with Odoo 17',
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
}
