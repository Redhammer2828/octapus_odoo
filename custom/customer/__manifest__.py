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
        # 'views/product_category.xml',
        # 'views/product_services.xml',
        # 'views/product_packages.xml',
        # 'static/src/js/partner_form.js',
    ],
    'installable': True,
    'application': True,
    'sequence': 2
}
