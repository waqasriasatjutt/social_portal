{
    'name': 'User-Specific Social Marketing',
    'version': '1.0',
    'category': 'Marketing',
    'summary': 'Manage social media accounts, campaigns, and ads per user',
    'depends': ['social_marketing'],
    'data': [
        'security/ir.model.access.csv',
        'views/social_marketing_views.xml',
    ],
    'installable': True,
}
