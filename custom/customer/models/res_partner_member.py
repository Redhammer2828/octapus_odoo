from odoo import models,fields,api

class ResPartnerMembers(models.Model):
    _inherit = 'res.partner'

    parent_customer_id = fields.Many2one('res.partner', string='Parent Customer')
    is_customer = fields.Boolean('Is_customer')
    # -----------------------------------------
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
    
    
    member_type = fields.Selection([ ('policy', 'Policy Member'),
                                    ('credit', 'Credit Member'),
                                    ('adhoc', 'Ad-hoc Member') ], string='Member Type')   
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


    adhoc_member = fields.Boolean(string='Adhoc Member')
    credit_member_ok = fields.Boolean(string='Credit Member OK')
    # active = fields.Boolean(string='Active')

    #notebook
    # product_template_id = fields.Many2one('product.template', string='Product Template')
    # service_ids = fields.Many2many('service.model', string='Services')
    # comment = fields.Text(string='Internal Notes')
    # membership_history = fields.One2many('membership.history.model', 'partner_id', string='Membership History')
    
    #-----------------------------------------
    
    @api.model
    def create(self, vals):
        # Check if the record is being created from 'res_partner_member_form'
        if self.env.context.get('from_res_partner_member_form'):
            vals['is_customer'] = True

        new_partner = super(ResPartnerMembers, self).create(vals)

        return new_partner
    