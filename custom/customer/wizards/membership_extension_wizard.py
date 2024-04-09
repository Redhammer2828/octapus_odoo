from odoo import models, fields, api

class MembershipExtensionWizard(models.TransientModel):
    _name = 'membership.extension.wizard'

    expiry_date = fields.Date('Expiry Date')
    new_expiry_date = fields.Date('New Expiry Date')

    def action_extension(self):
        partner = self.env['res.partner'].browse(self._context.get('active_id'))
        partner.member_expiry_date = self.new_expiry_date