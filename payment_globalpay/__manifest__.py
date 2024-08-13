# __manifest__.py
{
    'name': 'Payment Provider: Global Payments',
    'version': '1.0',
    'category': 'Accounting/Payment Providers',
    'sequence': 350,
    'summary': "Integration with Global Payments for processing payments.",
    'author': 'Your Name or Company',
    'website': 'https://www.globalpay.com',
    'depends': ['payment'],
    'data': [
        'views/payment_globalpay_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_provider_data.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
