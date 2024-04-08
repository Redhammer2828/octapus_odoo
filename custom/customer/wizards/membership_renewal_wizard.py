from odoo import models, fields, api

class MembershipRenewalWizard(models.TransientModel):
    _name = 'membership.renewal.wizard'
    _description = "Membership Renewal Wizard"

    parent_customer_id = fields.Many2one('res.partner', string='Parent Customer')
    activation_date = fields.Date('Activation Date')
    card_type_id = fields.Many2one('card.type', string='Card Type') #Created card.type model 
    expiry_date = fields.Date('Expiry Date')
    vehicle_chasis_no = fields.Char(string='Vehicle Chasis Number')
    product_template_id = fields.Many2one('product.template', string="Packages")

    def action_renew(self):
        partner = self.env['res.partner'].browse(self._context.get('active_id'))
        partner.write({
            'parent_customer_id': self.parent_customer_id.id,
            'member_activate_date': self.activation_date,
            'card_type_id': self.card_type_id.id,
            'member_expiry_date': self.expiry_date,
            'vehicle_chasis_no': self.vehicle_chasis_no,
            'product_template_id': self.product_template_id.id,
            # Add any additional fields or logic you need for membership renewal
        })