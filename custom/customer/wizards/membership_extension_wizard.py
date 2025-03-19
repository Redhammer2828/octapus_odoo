from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class MembershipExtensionWizard(models.TransientModel):
    _name = 'membership.extension.wizard'

    expiry_date = fields.Date('Expiry Date')
    new_expiry_date = fields.Date('New Expiry Date')

    def action_extension(self):
        partner = self.env['res.partner'].browse(self._context.get('active_id'))
 
        if not partner:
            raise UserError("No active partner found for extension.")
        # Create an entry in the membership.history model before updating the partner record
        mem_renewal = self.env['membership.history'].create({
            'name': partner.name,  # Using partner name
            'parent_customer_id': partner.parent_customer_id.id,
            'old_membership_number': partner.old_membership_number,  # Assuming old_membership_number exists
            'ref_num': partner.ref_num,
            'member_partner_category_id': partner.member_partner_category_id.id,
            'product_template_id': partner.product_template_id.id,
            'member_type': partner.member_type,
            'policy_no': partner.policy_no,
            'vehicle_chasis_no': partner.vehicle_chasis_no,
            'vehicle_plate': partner.vehicle_plate,
            'vehicle_type': partner.vehicle_type,
            'member_activate_date': partner.member_activate_date,
            'member_expiry_date': partner.member_expiry_date,  # Storing old expiry date
            'invoice_ref_date': partner.invoice_ref_date,
            'card_type_id': partner.card_type_id.id,
            'history_id': partner.id
        })
        self.env['membership.timeline'].create({
            'member_id': partner.id,
            'user': self.env.user.id,
            'time': fields.Datetime.now(),
            'status': 'Membership Renewal',
            'timeline_status': partner.membership_state,
        })
        # Update the partner's expiry date with the new value
        partner.member_expiry_date = self.new_expiry_date