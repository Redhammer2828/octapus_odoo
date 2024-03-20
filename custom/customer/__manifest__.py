# customer/__manifest__.py
{
    'name': 'Customer',
    'version': '1.0',
    'depends': ['base', 'web','product'],
    'author': 'Sasoft',
    'category': 'Sales',
    'description': 'Customers Management',
    'data': [
        'security/ir.model.access.csv',
        # 'views/view.xml'
        'views/res_partner_customer.xml',
        'views/res_partner_member.xml',
        'views/config_product.xml',
        'views/card_type.xml',
        'views/product_packages.xml',
        'views/product_category.xml',
        'views/member_vehicle_type.xml',
        'views/member_vehicle_model.xml',
        'views/location.xml',
        'views/external_service.xml',
        'views/res_partner_adhoc_member.xml',
        'views/res_partner_credit_member.xml',
        'views/product_service.xml',
        # 'views/product_packages.xml',
        # 'static/src/js/partner_form.js',
    ],
    'installable': True,
    'application': True,
    'sequence': 2
}
