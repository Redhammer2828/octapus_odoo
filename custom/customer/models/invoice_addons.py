from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    category_id = fields.Many2one('partner.category', string="Customer Category", 
                                  domain="[('partner_id','=', partner_id)]")
    
    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")