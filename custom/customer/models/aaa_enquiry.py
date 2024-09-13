from odoo import models, fields, api

class Enquiry(models.Model):
    _name = 'aaa.enquiry'
    _description = 'Enquiry'

    name = fields.Char(string='Name', readonly=True)
    mem_name = fields.Char(string='Member Name')
    mobile = fields.Char(string='Mobile')
    email = fields.Char(string='Email')
    enquiry = fields.Text(string='Enquiry')
    vehicle_chasis_no = fields.Char(string='Vehicle Chasis No')
    vehicle_plate_no = fields.Char(string='Vehicle Plate No')
    membership = fields.Char(string='Membership')
    create_date = fields.Datetime(string='Create Date', readonly=True, default=fields.Datetime.now)
    created_by = fields.Many2one('res.users', string='Created By', readonly=True, default=lambda self: self.env.user)
    policy_no = fields.Char(string='Policy No')
    date = fields.Datetime(string='Create Date', readonly=True, default=fields.Datetime.now)
    
    customer_id = fields.Many2one('res.partner', string='Customer')
    member_id = fields.Many2one('res.partner', string='Member')
    service_id = fields.Many2one('product.template', string='Service')
    enq_id = fields.Many2one('aaa.service',string='Enq_Service',ondelete='cascade') #IN aaa.enquiry
    
    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        if not self.customer_id:
            self.member_id = False

    @api.onchange('member_id')
    def _onchange_member_id(self):
        if not self.member_id:
            self.service_id = False
