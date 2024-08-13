{
    'name': 'Custom Social Marketing',
    'version': '1.0',
    'depends': ['social'],
    'author': 'Your Name',
    'category': 'Marketing',
    'description': 'Custom Social Marketing module with user-specific portals in Odoo 17.',
    'data': [
        'security/social_security.xml',
        'security/ir.model.access.csv',
        'views/social_account.xml',
        'views/social_post.xml',
        'views/social_compaign_views.xml',
        'views/social_marketing_views.xml',
    ],
    'installable': True,
    'application': True,
}
