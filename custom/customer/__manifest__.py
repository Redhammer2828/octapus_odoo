# customer/__manifest__.py
{
    'name': 'Customer',
    'version': '1.0',
    'depends': ['base', 'web','product','hr'],
    'author': 'Sasoft',
    'category': 'Customer',
    'description': 'Customers Management',
    'assets': {
        'web.assets_backend': [
            # 'web/static/src/js/core/**/*',  # Ensure that core web assets are included
            # 'web/static/src/js/widgets/**/*',  # Widgets and core functionality
            # '/customer/static/lib/jquery-ui/jquery-ui.min.js',  # Include jQuery UI
            # '/customer/static/lib/jquery-ui/jquery-ui.min.css',  # Include jQuery UI CSS
            # '/customer/static/src/js/location_autocomplete.js',  # Your custom JS file
            # 'customer/static/src/js/location_widget.js',
            # 'web.core',  # Required dependency
            # 'web.Widget',  # Required dependency
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_customer.xml',
        'views/res_partner_member.xml',
        'views/res_partner_member_temp.xml',
        'views/res_partner_member_cancel.xml',
        'views/config_product.xml',
        'views/card_type.xml',
        'views/country_code.xml',
        'views/product_packages.xml',
        'views/product_category.xml',
        'views/member_vehicle_type.xml',
        'views/member_vehicle_model.xml',
        'views/location.xml',
        'views/external_service.xml',
        'views/res_partner_adhoc_member.xml',
        'views/res_partner_credit_member.xml',
        'views/product_service.xml',
        'views/policy_member_search.xml',
        'views/credit_member_search.xml',
        'views/data_upload_file.xml',
        'views/upload_history.xml',
        'views/member_upload_cancel.xml',
        'views/rejected_upload_members.xml',
        'views/cancellation_history.xml',
        'views/credit_member_upload.xml',
        'views/credit_member_upload_history.xml',
        'views/credit_member_upload_rejected.xml',
        'views/call_center_menu.xml',
        'views/call_center_service_form.xml',
        'views/call_center_enquiry.xml',
        'views/call_center_all_service_view.xml',
        'views/policy_member_service_history.xml',
        'views/res_partner_vendor.xml',
        'wizards/upload_member_wizard.xml',
        'wizards/membership_extension_wizard.xml',
        'wizards/membership_renewal_wizard.xml',
        'wizards/membership_cancel_wizard.xml',
        'wizards/member_cancel_upload_wizard.xml',
        'wizards/credit_member_upload_wizard.xml',
        'wizards/service_dispatch_wizard.xml',
        'wizards/service_cash_wizard.xml',
        'wizards/schedule_service_wizard.xml',
        'data/scheduled_action.xml',
        'data/sequence_data.xml',
        # 'views/product_packages.xml',
        # 'static/src/js/customer.js',
    ],

    # 'assets': {
    #     'web.assets_backend': [
    #         'customer/static/src/js/location_autocomplete.js',
    #         'https://code.jquery.com/jquery-3.6.0.min.js',  # Add jQuery here
    #     ],
    # },
    'installable': True,
    'application': True,
    'sequence': 2,
}
