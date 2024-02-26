from odoo import models,fields,api

class ResPartnerMembers(models.Model):
    _inherit = 'res.partner'

    parent_customer_id = fields.Many2one('res.partner', string='Parent Customer')
    is_customer = fields.Boolean('Is_customer')

    # membership_state = fields.Selection([
    #     ('confirm', 'Confirm'),
    #     ('cancel', 'Cancel'),
    #     ('temporary', 'Temporary')
    # ], string='Membership State', default='temporary')
    
    @api.model
    def create(self, vals):
        # Check if the record is being created from 'res_partner_member_form'
        if self.env.context.get('from_res_partner_member_form'):
            vals['is_customer'] = True

        new_partner = super(ResPartnerMembers, self).create(vals)

        return new_partner
    
    