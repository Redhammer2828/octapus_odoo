from odoo import models,fields,api, _
from odoo.exceptions import ValidationError
import logging
from lxml import etree
from odoo.exceptions import UserError, ValidationError
import json
from datetime import date
import random


logger = logging.getLogger(__name__)

class ResPartnerMembers(models.Model):
    _inherit = 'res.partner'

    parent_customer_id=fields.Many2one('res.partner',string='Customer',domain="[('is_company', '=', True)]")
    # Check Fields
    is_customer = fields.Boolean('Is_customer')
    is_vendor = fields.Boolean('Is_vendor')
    is_driver_available = fields.Boolean('Is Driver Available',default='False')
    is_duplicated = fields.Boolean(string='Duplicated Record', default=False)
    # Basic Fields
    ref_num = fields.Char(string='Membership Number', compute='_compute_member_ref_no', store=True)
    policy_no = fields.Char(string='Policy Number')
    vehicle_chasis_no = fields.Char(string='Vehicle Chasis No')
    old_membership_number = fields.Char(string='Old Membership Number')
    member_activate_date = fields.Date(string='Member Activate Date')
    member_expiry_date = fields.Date(string='Member Expiry Date')
    vehicle_type = fields.Char(string='Vehicle Type')
    vehicle_model = fields.Char(string='Vehicle Model')
    vehicle_reg_code = fields.Char(string='Vehicle Reg. Code')
    vehicle_plate = fields.Char(string='Vehicle Plate')
    vehicle_mfg_year = fields.Char(string='Vehicle Mfg Year')
    driving_license = fields.Char(string='Driving License')
    # Address Field
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street 2')
    city = fields.Char(string='City')
    zip = fields.Char(string='ZIP')
    function = fields.Char(string='Function')
    phone = fields.Char(string='Phone', widget='phone')
    mobile = fields.Char(string='Mobile', widget='phone')
    # personal details Fields
    email = fields.Char(string='Email', widget='email')
    website = fields.Char(string='Website', widget='url')
    lang = fields.Char(string='Language')
    invoice_ref_date = fields.Date(string='Invoice Ref Date')
    delivery_ref_date = fields.Date(string='Delivery Ref Date')
    mail_ref = fields.Char(string='Mail Ref')
    related_company_customer_code = fields.Char(string='Related Company Customer Code')
    # many2one fields
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country')
    user_ids = fields.Many2many('res.users', string='Users')
    category_id = fields.Many2many('res.partner.category', string='Category')
    title = fields.Many2one('res.partner.title', string='Title')
    vehcle_reg_country_id = fields.Many2one('res.country', string='Vehicle Reg. Country') #changed country to res.country
    # readonly fields
    membership_cancel_date = fields.Date(string='Membership Cancel Date')
    create_uid = fields.Many2one('res.users', string='Created By')
    card_type_id = fields.Many2one('card.type', string='Card Type') #Created card.type model 
    member_type = fields.Selection([ ('policy', 'Policy Member'),
                                    ('credit', 'Credit Member'),
                                    ('adhoc', 'Ad-hoc Member') ], string='Member Type')   
    adhoc_member = fields.Boolean(string='Adhoc Member')
    credit_member_ok = fields.Boolean(string='Credit Member OK')
    product_template_id = fields.Many2one('product.template', string="Package")
    service_ids = fields.Many2many('product.product', string="Services", widget="many2many_tags", options="{'no_create_edit': True}" ,compute='_compute_service_ids', store=True)
    member_partner_category_id = fields.Many2one('partner.category',string='Category',domain="[('partner_id', '=', parent_customer_id),('member_type', '=', member_type)]")
    #------------------------------------------------------------
    member_expired = fields.Boolean(string="Member Expired", compute='_compute_member_expired', store=True)
    policy_member_service_count = fields.Integer(string="Policy Services Count", compute='_compute_policy_member_service_count')
    policy_member_cash_service_count = fields.Integer(string="Policy Cash Services Count", compute='_compute_policy_member_cash_service_count')
    policy_member_credit_service_count = fields.Integer(string="Policy Credit Services Count" ,compute='_compute_policy_member_credit_service_count')
    credit_member_service_count = fields.Integer(string="Credit Services", compute='_compute_credit_member_service_count')
    adhoc_member_service_count = fields.Integer(string="Adhoc Services Count", compute='_compute_adhoc_member_service_count')                                                                                        
    # ------------------------------------------------------------    
    membership_state = fields.Selection([
    ('temp', "Temporary"),
    ('confirm', "Confirmed"),
    ('cancel', "Cancelled")
    ], string="Status", readonly=True, default='temp', tracking=True)
    # ---------------------------------------
    cancellation_comment = fields.Text('Cancelation Comment')
    # ----------------------------
    membership_history_ids= fields.One2many('membership.history','history_id', string='Membership History')
    
    def unlink(self):
        """Restrict deletion for users in groups named '' or 'new_dispatchers'."""
        current_user = self.env.user  # Get the currently logged-in user
        # Check if the user belongs to groups with specific names
        user_groups = current_user.groups_id  # Get all groups of the current user
        restricted_groups = ['Agent', 'Dispatcher']

        if any(group.name in restricted_groups for group in user_groups):
            raise UserError(
                "You cannot delete this record"
            )
        return super(ResPartnerMembers, self).unlink()
    
    @api.model
    def create(self, vals):
        if self.env.context.get('from_res_partner_member_form'):
            vals['is_customer'] = True
            vals['credit_member_ok'] = False
            vals['adhoc_member'] = False
            vals['member_type'] = 'policy'
        

        if self.env.context.get('from_res_partner_credit_member_form'):
            vals['is_customer'] = True
            vals['credit_member_ok'] = True
            vals['adhoc_member'] = False
            vals['member_type'] = 'credit'

        if self.env.context.get('from_res_partner_adhoc_member_form'):
            vals['is_customer'] = True
            vals['credit_member_ok'] = False
            vals['adhoc_member'] = True
            vals['member_type'] = 'adhoc'
        
        new_partner = super(ResPartnerMembers, self).create(vals)
        return new_partner
    
    @api.depends('parent_customer_id', 'member_partner_category_id', 'card_type_id')
    def _compute_member_ref_no(self):
        for record in self:
            if record.parent_customer_id and record.member_partner_category_id and record.card_type_id:
                customer_code = record.parent_customer_id.customer_code or ''
                category_name = record.member_partner_category_id.name or ''
                card_code = record.card_type_id.code or ''
                random_digits = str(random.randint(10000, 99999))
                record.ref_num = f"{customer_code}{category_name}{card_code}{random_digits}"
            else:
                record.ref_num = False

    def action_confirm_membership(self):
            for record in self:
                company = record.parent_customer_id  # Get the company directly
            
                if company:
                    # Step 1: Check if a vehicle with the same chassis number exists within the same company, excluding the current record
                    existing_members = self.env['res.partner'].search([
                        ('vehicle_chasis_no', '=', record.vehicle_chasis_no),
                        ('parent_customer_id', '=', company.id),
                        ('membership_state', '=', 'confirm'),
                        ('id', '!=', record.id)  # Exclude the current record from the search
                    ])
                    print("Existing members", existing_members)
                
                    if existing_members:
                        for existing_member in existing_members:
                            existing_expiry_date = existing_member.member_expiry_date
                            current_expiry_date = record.member_expiry_date
    
                            # Log for debugging purposes
                            print("Existing member expiry date", existing_expiry_date)
                            print("COMPANY",company)
    
                            # Handle case where the existing member's expiry date has passed
                            if existing_expiry_date and existing_expiry_date < date.today():
                                # Expired policy: Cancel the existing membership and confirm the new one
                                existing_member.membership_state = 'cancel'
                                record.membership_state = 'confirm'
                            else:
                                # Active policy exists: Raise validation error
                                if existing_member.name != record.name:
                                    # If the existing member has a different name, raise an error
                                    raise ValidationError(_("An active policy with the same chassis number under the selected company already exists!"))
                                else:
                                # If the same name and chassis number exist, handle expiry date difference
    
                                        current_expiry_date = record.member_expiry_date  # Ensure that you fetch the current record's expiry date
                                        existing_expiry_date = existing_member.member_expiry_date
    
                                        # **New validation check**: If the expiry dates are the same, raise an error
                                        if current_expiry_date == existing_expiry_date:
                                            raise ValidationError(_("A record with the same chassis number and expiry date already exists!"))
    
                                        # Calculate the difference in expiry dates
                                        date_difference = (current_expiry_date - existing_expiry_date).days
    
                                        if date_difference >= 365:
                                            # If the difference is greater than or equal to 365 days, suggest renewal
                                            raise ValidationError(_("An already existing record has an expiry difference of >= 365 days. Please proceed with membership renewal."))
                                        elif date_difference < 365:
                                            # If the difference is less than 365 days, suggest extension
                                            raise ValidationError(_("The same record exists with an expiry date difference of < 365 days. Please proceed with membership extension."))
                    
                        # If none of the existing members are active (i.e., all expired and cancelled), confirm the current record
                        record.membership_state = 'confirm'
    
            # Step 2: Check if the same chassis number exists under another company
            chassis_in_another_company = self.env['res.partner'].search([
                ('vehicle_chasis_no', '=', record.vehicle_chasis_no),
                ('parent_customer_id', '!=', company.id),  # Check if the chassis number exists under a different company
                ('membership_state', '=', 'confirm')
            ])
    
            if chassis_in_another_company:
                # Loop through each record that has the same chassis number in another company
                for other_member in chassis_in_another_company:
                    another_company_expiry_date = other_member.member_expiry_date
                    print("Another company expiry date", another_company_expiry_date)
    
                    if another_company_expiry_date and another_company_expiry_date >= date.today():
                        # If the existing record's expiry date is greater than or equal to the current date, raise an error
                        raise ValidationError(_("The same chassis number exists under another company with an active policy!"))
                    else:
                        # If the policy is expired, you can handle it as needed (e.g., cancel it)
                        other_member.membership_state = 'cancel'
            
                # If all the other company's records have expired policies, confirm the current record
                record.membership_state = 'confirm'
    
            # Step 3: Check that the expiry date is greater than the activation date if both are set
            if record.member_activate_date and record.member_expiry_date:
                if record.member_expiry_date <= record.member_activate_date:
                    raise ValidationError(_("The expiry date should be greater than the activation date."))
    
            # Step 4: Confirm membership if all validations pass
            record.membership_state = 'confirm'
    
    def copy(self, default=None):
        if default is None:
            default = {}

        # Adding 'Dup-' prefix to specific fields when duplicating
        default.update({
            'name': 'Dup-' + (self.name or ''),
            # 'ref_num': 'Dup-' + (self.ref_num or ''),
            # 'policy_no': 'Dup-' + (self.policy_no or ''),
            'vehicle_chasis_no': 'Dup-' + (self.vehicle_chasis_no or ''),
            # 'vehicle_plate': 'Dup-' + (self.vehicle_plate or ''),
            'membership_state': 'temp',
            'is_duplicated': True,
        })

        # Call the super method to create the duplicated record
        return super(ResPartnerMembers, self).copy(default)
    
    @api.depends('membership_state')
    def _compute_is_readonly(self):
        for record in self:
            record.is_readonly = record.membership_state == 'confirm'
    
        
    is_readonly = fields.Boolean(string='Read-Only', compute='_compute_is_readonly', store=True)
   
    @api.depends('member_expiry_date')
    def _compute_member_expired(self):
        for partner in self:
            if partner.member_expiry_date and partner.member_expiry_date < fields.Date.today():
                partner.member_expired = True
            else:
                partner.member_expired = False
#-------------------------------COUNT CALCULATION-----------------------------------------------------   
    @api.depends('name')
    def _compute_policy_member_service_count(self):
        for partner in self:
            service_member_ids = self.env['aaa.service'].search([
                ('member_id', '=', self.id),
                ('type', '=', 'non_cash'),
                ('member_type', '=', 'policy')
            ])
            print("MEMBER SERVICES", service_member_ids.ids)
            partner.policy_member_service_count= len(service_member_ids)

    
    def action_view_policy_service(self):
       
        return {
            'name': 'Services',
            'type': 'ir.actions.act_window',
            'res_model': 'aaa.service',
            'view_mode': 'tree,form',
            'domain': [('member_id', '=', self.id), ('member_type','=','policy'), ('type', '=', 'non_cash')],
            'context': {
                'from_res_partner_member_form': True,
                'default_customer_id': self.parent_customer_id,
                'default_member_id': self.id,  # Pre-select the parent customer
            },
            'views': [(self.env.ref('customer.call_center_all_service_view_tree').id, 'tree'),
                    (self.env.ref('customer.call_center_service_form').id, 'form')],
         
        }
    
    @api.depends('name')
    def _compute_policy_member_cash_service_count(self):
        for cash in self:
            cash_service_ids = self.env['aaa.service'].search([
                ('member_id', '=', self.id),
                ('type', '=', 'cash'),
                ('member_type', '=', 'policy')
            ])
            print("CASH SERVICES", cash_service_ids.ids)
            cash.policy_member_cash_service_count= len(cash_service_ids)
 
    def action_view_cash_service(self):
         
         return {
            'name': 'Services',
            'type': 'ir.actions.act_window',
            'res_model': 'aaa.service',
            'view_mode': 'tree,form',
            'domain': [('member_id', '=', self.id), ('member_type','=','policy'), ('type', '=', 'cash')],
            'context': {
                'from_res_partner_member_form': True,
                'default_customer_id': self.parent_customer_id,
                'default_member_id': self.id,  # Pre-select the parent customer
            },
            'views': [(self.env.ref('customer.call_center_all_service_view_tree').id, 'tree'),
                    (self.env.ref('customer.call_center_service_form').id, 'form')],
        }
    
    @api.depends('name')
    def _compute_credit_member_service_count(self):
        for partner in self:
            service_member_ids = self.env['aaa.service'].search([
                ('member_id', '=', self.id),
                ('type', '=', 'non_cash'),
                ('member_type', '=', 'credit')
            ])
            print("MEMBER SERVICES", service_member_ids.ids)
            partner.credit_member_service_count= len(service_member_ids)
 
    def action_view_credit_service(self):
       
            return {
            'name': 'Credit Services',
            'type': 'ir.actions.act_window',
            'res_model': 'aaa.service',
            'view_mode': 'tree,form',
            'domain': [('member_id', '=', self.id), ('member_type','=','credit'), ('type', '=', 'non_cash')],
            'context': {
                'from_res_partner_member_form': True,
                'default_customer_id': self.parent_customer_id,
                'default_member_id': self.id,  # Pre-select the parent customer
            },
            'views': [(self.env.ref('customer.call_center_all_service_view_tree').id, 'tree'),
                    (self.env.ref('customer.call_center_service_form').id, 'form')],
         
        }
   
    @api.depends('name')
    def _compute_adhoc_member_service_count(self):
        for partner in self:
            service_member_ids = self.env['aaa.service'].search([
                ('member_id', '=', self.id),
                ('type', '=', 'cash'),
                ('member_type', '=', 'adhoc')
            ])
            print("MEMBER SERVICES", service_member_ids.ids)
            partner.adhoc_member_service_count= len(service_member_ids)
 
    def action_view_adhoc_service(self):
       
            return {
            'name': 'Adhoc Services',
            'type': 'ir.actions.act_window',
            'res_model': 'aaa.service',
            'view_mode': 'tree,form',
            'domain': [('member_id', '=', self.id), ('member_type','=','adhoc'), ('type', '=', 'cash')],
            'context': {
                'from_res_partner_member_form': True,
                'default_customer_id': self.parent_customer_id,
                'default_member_id': self.id,  # Pre-select the parent customer
            },
            'views': [(self.env.ref('customer.call_center_all_service_view_tree').id, 'tree'),
                    (self.env.ref('customer.call_center_service_form').id, 'form')],
         
        }
# ----------------------------------------------------------------------------------------------------- 
    def action_membership_renewal(self):
        view_id = self.env.ref('customer.membership_renewal_wizard_form').id
        return {
            'name': 'Membership Renewal',
            'type': 'ir.actions.act_window',
            'res_model': 'membership.renewal.wizard',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
            'context': {
                'default_parent_customer_id': self.parent_customer_id.id,
                'default_activation_date': self.member_activate_date,
                'default_card_type_id': self.card_type_id.name,
                'default_vehicle_chasis_no': self.vehicle_chasis_no,
                'default_product_template_id': self.product_template_id.id,
                'active_id': self.id,
                'active_model': self._name,
            }
        }
        
    def action_membership_extension(self):
        view_id = self.env.ref('customer.membership_extension_wizard_form').id
        return {
            'name': 'Membership Extension',
            'type': 'ir.actions.act_window',
            'res_model': 'membership.extension.wizard',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
            'context': {
                'default_expiry_date': self.member_expiry_date,
                'active_id': self.id,
                'active_model': self._name,
            }
        }

    def action_membership_cancel(self):
        view_id = self.env.ref('customer.membership_cancel_wizard_form').id
        return {
            'name': 'Membership Cancellation',
            'type': 'ir.actions.act_window',
            'res_model': 'membership.cancel.wizard',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
            'context': {
                'active_id': self.id,
                'active_model': self._name,
                # 'default_membership_cancel_date': self.membership_cancel_date
            }
        }

    def action_create_service(self):
        view_id = self.env.ref('customer.call_center_service_form').id
 
        vehicle_model = self.env['member.vehicle.type'].search([('name', '=', self.vehicle_model)], limit=1)
        print("VEHICLE_MODEL:", self.vehicle_model)
        print("VEHICLE_RECORD:", vehicle_model)
 
        card_type = self.env['card.type'].browse(self.card_type_id.id)
        card_type_name = card_type.name
 
        # Fetch the res.partner record directly by name
        partner = self.env['res.partner'].search([('name', '=', self.name)], limit=1)
        print("DEBUG: Partner fetched:", partner)
 
        # Pre-create the aaa.service record with the fetched partner ID
        service_vals = {
            'customer_id': self.parent_customer_id.id,
            'sequence_id': self.member_partner_category_id.id,
            'card_type': card_type_name,
            'member_contact_no': self.mobile,
            'vehicle_chasis_no': self.vehicle_chasis_no,
            'vehicle_type': self.vehicle_type,
            'vehicle_model': self.vehicle_model,
            'vehicle_plate': self.vehicle_plate,
            'policy_no': self.policy_no,
            # 'product_id': self.service_ids.id,
            'member_type': self.member_type,
            'member_id': partner.id if partner else False,  # Directly assign partner ID here
            'member_activate_date': self.member_activate_date,
            'member_expiry_date': self.member_expiry_date,
            'type': 'non_cash',
        }
 
        # Create the service record directly
        service_record = self.env['aaa.service'].create(service_vals)
 
        # Return the form view for the newly created record
        return {
            'name': 'Service Policy',
            'type': 'ir.actions.act_window',
            'res_model': 'aaa.service',
            'view_mode': 'form',
            'res_id': service_record.id,  # Open the newly created record
            'view_id': view_id,
        }
    
    def action_create_enquiry(self):
        view_id = self.env.ref('customer.call_center_enquiry_view_form').id
 
        # Fetch the service IDs from res.partner
        member = self.env['res.partner'].browse(self.id)
        service_ids = member.service_ids.ids  # Assuming 'service_ids' is a One2many or Many2many field in res.partner
        view_id = self.env.ref('customer.view_enquiry_complaint_wizard_form').id
        return {
            'name': 'Select Enquiry or Complaint',
            'type': 'ir.actions.act_window',
            'res_model':'enquiry.complaint.wizard',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
            'context': {
                #'default_enq_cm_id ':,
                'default_member_id': self.id,
                'default_customer_id': self.parent_customer_id.id,
                'default_policy_no': self.policy_no,
                'default_email': self.email,
                'default_mobile': self.mobile,
                'default_vehicle_chasis_no': self.vehicle_chasis_no,
                'default_vehicle_plate_no': self.vehicle_plate,
                'active_id': self.id,
                'active_model': self._name,
                'default_service_id': service_ids[0] if service_ids else False,  # Set a default if needed
                'domain_service_id': [('id', 'in', service_ids)],
            },
        }
    

    def action_policy_service_history(self):
        # Retrieve services taken by the member
        service_partners = self.env['aaa.service'].search([('member_id', '=', self.id)])

        # Initialize a dictionary to store product_id counts
        product_count_dict = {}

        # Loop through each service partner and gather related product IDs
        for service in service_partners:
            product_id = service.product_id.id
            print("PRODUCT ID", product_id)
            
            # Increment the count for this product_id
            if product_id in product_count_dict:
                product_count_dict[product_id] += 1
            else:
                product_count_dict[product_id] = 1
            
            # Retrieve addon services related to the current service
            addon_services = self.env['aaa.service.addon'].search([('service_id', '=', service.id)])
            
            # Loop through each addon service and add related product IDs to the dictionary
            for addon in addon_services:
                addon_product_id = addon.product_id.id
                if addon_product_id in product_count_dict:
                    product_count_dict[addon_product_id] += 1
                else:
                    product_count_dict[addon_product_id] = 1
        
        # Convert the dictionary to the format required for line_ids
        service_lines = [(0, 0, {'product_id': product_id, 'count': count}) for product_id, count in product_count_dict.items()]
        print("SERVICE LINES", service_lines)

        # Create or update the record with the service history lines
        history_record = self.env['policy.service.history'].create({
            'member_id': self.id,
            'line_ids': service_lines,
        })

        # Return the action to open the form view of the created record
        view_id = self.env.ref('customer.policy_service_history_view_form').id
        context = {
            'default_member_id': self.id,
            'default_member_activate_date': self.member_activate_date,
            'default_member_expiry_date': self.member_expiry_date,
            'active_id': history_record.id,
            'active_model': 'policy.service.history',
        }
        return {
            'name': 'Policy Service History',
            'type': 'ir.actions.act_window',
            'res_model': 'policy.service.history',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
            'res_id': history_record.id,
            'context': context,
        }

    @api.depends('product_template_id')
    def _compute_service_ids(self):
        for record in self:
            if record.product_template_id:
                services = self.env['product.package.service'].search([('product_template_id', '=', record.product_template_id.id)])
                product_ids = services.mapped('product_id').ids
                if product_ids:
                    record.service_ids = [(6, 0, product_ids)]
                else:
                    record.service_ids = [(6, 0, [])]
            else:
                record.service_ids = [(6, 0, [])]

    @api.onchange('parent_customer_id')
    def _onchange_parent_customer_id(self):
        if self.parent_customer_id:
            partner_categories = self.env['partner.category'].search([
                ('partner_id', '=', self.parent_customer_id.id),
                ('member_type', '=', 'policy')
            ])
            print("Parent Customer ID",self.parent_customer_id)
            print("PARTNER CATEGORIES",partner_categories)

    class MembershipHistory(models.Model):
        _name = 'membership.history'
        _description = 'Membership History'

        # name = fields.Char('Name')
        # ref_num = fields.Char('Ref Num')
        policy_no = fields.Char(string='Policy Number')
        vehicle_chasis_no = fields.Char(string='Vehicle Chasis No')
        vehicle_type = fields.Char(string='Vehicle Type')
        vehicle_plate = fields.Char(string='Vehicle Plate')
        member_activate_date = fields.Date(string='Member Activate Date')
        member_expiry_date = fields.Date(string='Member Expiry Date')
        card_type_id = fields.Many2one('card.type', string='Card Type')
        history_id = fields.Many2one('res.partner', string="Replaced Member")
        