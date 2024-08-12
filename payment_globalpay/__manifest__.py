{
    'name': 'Payment Provider: Global Payments',
    'category': 'Accounting/Payment Providers',
    'version': '1.0',
    'sequence': 350,
    'summary': "Integration with Global Payments.",
    'depends': ['payment'],
    'data': [
        'views/payment_globalpay_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_provider_data.xml',
    ],
    'license': 'LGPL-3',
}
