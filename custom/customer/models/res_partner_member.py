from odoo import models,fields,api

POLICY_MEMBER_STATE = [
    ('temp', "Temporary"),
    ('confirm', "Confirmed"),
    ('cancel', "Cancelled"),
]

class ResPartnerMembers(models.Model):
    _inherit = 'res.partner'

    parent_customer_id = fields.Many2one('res.partner', string='Parent Customer')
    is_customer = fields.Boolean('Is_customer')
    # -----------------------------------------
    ref_num = fields.Char('Ref Num')

    policy_no = fields.Char(string='Policy No')
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
    product_template_id = fields.Many2one('product.template', string="Product Template")
    service_ids = fields.Many2many('product.product', string="Services", widget="many2many_tags", options="{'no_create_edit': True}")
    member_partner_category_id = fields.Many2one('partner.category', string='Category')
    #-----------------------------------------
    membership_state = fields.Selection(
        selection=POLICY_MEMBER_STATE,
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='temp')
    
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