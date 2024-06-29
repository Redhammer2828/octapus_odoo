from odoo import models,fields,api

# POLICY_MEMBER_STATE = [
#     ('temp', "Temporary"),
#     ('confirm', "Confirmed"),
#     ('cancel', "Cancelled"),
# ]

class ResPartnerMembers(models.Model):
    _inherit = 'res.partner'

    parent_customer_id = fields.Many2one('res.partner', string='Customer')
    is_customer = fields.Boolean('Is_customer')
    # -----------------------------------------
    ref_num = fields.Char('Membership Number')

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
    # personal details
    email = fields.Char(string='Email', widget='email')
    website = fields.Char(string='Website', widget='url')

    lang = fields.Char(string='Language')
    invoice_ref_date = fields.Date(string='Invoice Ref Date')
    delivery_ref_date = fields.Date(string='Delivery Ref Date')
    mail_ref = fields.Char(string='Mail Ref')
    related_company_customer_code = fields.Char(string='Related Company Customer Code')
    
    
    # type = fields.Selection([('private', 'Private'), ('public', 'Public')], string='Type')
    
    # many2one fields
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country')
    user_ids = fields.Many2many('res.users', string='Users')
    category_id = fields.Many2many('res.partner.category', string='Category')
    title = fields.Many2one('res.partner.title', string='Title')
    # region_code_id = fields.Many2one('region.code', string='Region Code')

    # vehicle_emirate_id = fields.Many2one('emirate', string='Vehicle Emirate')
    vehcle_reg_country_id = fields.Many2one('res.country', string='Vehicle Reg. Country') #changed country to res.country

    # readonly fields
    membership_cancel_date = fields.Date(string='Membership Cancel Date')
    create_uid = fields.Many2one('res.users', string='Created By')

    card_type_id = fields.Many2one('card.type', string='Card Type') #Created card.type model 
    # member_sequence_id = fields.Many2one('member.sequence', string='Member Sequence')


    member_type = fields.Selection([ ('policy', 'Policy Member'),
                                    ('credit', 'Credit Member'),
                                    ('adhoc', 'Ad-hoc Member') ], string='Member Type')   
    
    adhoc_member = fields.Boolean(string='Adhoc Member')
    credit_member_ok = fields.Boolean(string='Credit Member OK')
    # active = fields.Boolean(string='Active')

    #notebook
    # product_template_id = fields.Many2one('product.template', string='Product Template')
    # service_ids = fields.Many2many('service.model', string='Services')
    # comment = fields.Text(string='Internal Notes')
    # membership_history = fields.One2many('membership.history.model', 'partner_id', string='Membership History')
    product_template_id = fields.Many2one('product.template', string="Package")
    service_ids = fields.Many2many('product.product', string="Services", widget="many2many_tags", options="{'no_create_edit': True}")
    member_partner_category_id = fields.Many2one('partner.category', string='Category')

    #------------------------------------------------------------
    member_expired = fields.Boolean(
        string="Member Expired", 
        compute='_compute_member_expired', 
        store=True
    )
    policy_member_service_count = fields.Integer(string="Policy Services Count", compute='_compute_policy_member_service_count')
    # ------------------------------------------------------------
    # membership_state = fields.Selection(
    #     selection=POLICY_MEMBER_STATE,
    #     string="Status",
    #     readonly=True, copy=False, index=True,
    #     tracking=3,
    #     default='temp')
    
    membership_state = fields.Selection([
    ('temp', "Temporary"),
    ('confirm', "Confirmed"),
    ('cancel', "Cancelled")
    ], string="Status", readonly=True, default='temp', tracking=True)
    # ---------------------------------------
    cancellation_comment = fields.Text('Cancelation Comment')
    # ----------------------------

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

    def action_confirm_membership(self):
        self.membership_state = 'confirm'

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
                
    @api.depends('service_ids')
    def _compute_policy_member_service_count(self):
        for partner in self:
            partner.policy_member_service_count = len(partner.service_ids)

    def action_view_policy_service(self):
        # Add your action code here
        pass

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
                ''
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
        self.membership_state = 'temp'
        view_id = self.env.ref('customer.call_center_credit_service_credit_new_view_form').id
        return{
            'name': 'Service Policy',
            'type': 'ir.actions.act_window',
            'res_model':'aaa.service',
            'view_mode':'form',
            'view_id': view_id,
            #'target': 'new',
            'context': {
                'default_customer_id': self.parent_customer_id.id,
                'default_sequence_id': self.member_partner_category_id.id,
                'default_card_type': self.card_type_id.id,
                'default_vehicle_chasis_no': self.vehicle_chasis_no,
                'default_vehicle_type_id': self.vehicle_type,
                'default_product_id': self.product_template_id.id,
                'default_member_type' : self.member_type,
                #'default_member_id' : self.policy_no,
                'active_id': self.id,
                'active_model': self._name,
            }
           
        }
    
    def action_create_enquiry(self):
        pass
    
    @api.onchange('product_template_id')
    def _onchange_product_template_id(self):
        if self.product_template_id:
            print("=========",self.product_template_id)
            services = self.env['product.package.service'].search([('product_template_id', '=', self.product_template_id.id)])

            print("SERVICE LIST",services)
            product_ids = services.mapped('product_id').ids
            print("Product IDs:", product_ids)
            if product_ids:
                related_products = self.env['product.template'].search([('id', 'in', product_ids)])
                print("Related Products:", related_products)
                self.service_ids = [(6, 0, related_products.ids)]

    # @api.onchange('parent_customer_id')
    # def _onchange_parent_customer_id(self):
    #     if self.parent_customer_id:
    #         partner_categories = self.env['partner.category'].search([
    #             ('partner_id', '=', self.parent_customer_id.id),
    #             ('member_type', '=', 'policy')
    #         ])
    #         print("Parent Customer ID",self.parent_customer_id)
    #         print("PARTNER CATEGORIES",partner_categories)

    # @api.onchange('parent_customer_id')
    # def _onchange_parent_customer_id(self):
    #     if self.parent_customer_id:
    #         product_categories = self.env['partner.category'].search([('partner_id', '=', self.parent_customer_id.id)])
    #         return {'domain': {'member_partner_category_id': [('id', 'in', product_categories.ids)]}}
    #     else:
    #         return {'domain': {'member_partner_category_id': [('id', 'in', [])]}}

    # def search_partner_categories(self):
    #     if self.parent_customer_id:
    #         partner_categories = self.env['partner.category'].search([('partner_id', '=', self.parent_customer_id.id)])
    #         return partner_categories
    #     else:
    #         return self.env['partner.category'].browse([])  # Return an empty recordset if no parent_customer_id

    # @api.onchange('parent_customer_id') 
    # def _onchange_parent_customer_id(self):
    #     if self.parent_customer_id:
    #         partner_categories = self.env['partner.category'].search([
    #             ('partner_id', '=', self.parent_customer_id.id),
    #             ('member_type', '=', 'policy')
    #         ])
    #         domain = [('id', 'in', partner_categories.ids)]
    #     else:
    #         domain = [('id', '=', 0)]
    #     return {'domain': {'member_partner_category_id': domain}}

    # @api.model
    # def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
    #     args = args or []
    #     if name:
    #         args = [('name', operator, name)] + args
    #     return self.search(args, limit=limit).name_get()