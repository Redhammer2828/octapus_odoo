from odoo import models, fields, api

class Enquiry(models.Model):
    _name = 'aaa.enquiry'
    _description = 'Enquiry'

    name = fields.Char(string='Name', readonly=True)
    customer_id = fields.Many2one('res.partner', string='Customer')
    member_id = fields.Many2one('res.partner', string='Member')
    service_id = fields.Many2one('product.template', string='Service')
    mem_name = fields.Char(string='Member Name')
    membership = fields.Char(string='Membership')
    mobile = fields.Char(string='Mobile')
    enquiry = fields.Text(string='Enquiry')
    create_date = fields.Datetime(string='Create Date', readonly=True, default=fields.Datetime.now)
    vehicle_chasis_no = fields.Char(string='Vehicle Chasis No')
    vehicle_plate_no = fields.Char(string='Vehicle Plate No')
    policy_no = fields.Char(string='Policy No')
    email = fields.Char(string='Email')
    created_by = fields.Many2one('res.users', string='Created By', readonly=True, default=lambda self: self.env.user)

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        if not self.customer_id:
            self.member_id = False

    @api.onchange('member_id')
    def _onchange_member_id(self):
        if not self.member_id:
            self.service_id = False
