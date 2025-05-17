from odoo import models,fields,api
from datetime import date

class ResPartnerMemberAddons(models.Model):
    _inherit = 'res.partner'

    next_activation_date = fields.Date(string="Next Activation Date")
    next_expiry_date = fields.Date(string="Next Expiry Date")
    next_product_template_id = fields.Many2one('product.template', string="Next Package")
    timeline_user_id = fields.Many2one('res.users', string="User")
    renewal_in_queue = fields.Boolean(string="Renewal in queue", default=False)

    def action_membership_renewal_scheduler(self):

        memberships = self.search([('renewal_in_queue', '=', True)])
        today = date.today()

        for record in memberships:
            if today >= record.member_expiry_date and record.next_activation_date and record.next_expiry_date and record.next_product_template_id and record.timeline_user_id:

                self.env['membership.history'].create({
                    'name': record.name,  
                    'parent_customer_id': record.parent_customer_id.id,
                    'old_membership_number': record.old_membership_number,  
                    'ref_num': record.ref_num,
                    'member_partner_category_id': record.member_partner_category_id.id,
                    'product_template_id': record.product_template_id.id,
                    'member_type': record.member_type,
                    'policy_no': record.policy_no,
                    'vehicle_chasis_no': record.vehicle_chasis_no,
                    'vehicle_plate': record.vehicle_plate,
                    'vehicle_type': record.vehicle_type,
                    'member_activate_date': record.member_activate_date,
                    'member_expiry_date': record.member_expiry_date,
                    'invoice_ref_date': record.invoice_ref_date,
                    'card_type_id': record.card_type_id.id,
                    'history_id': record.id
                })

                membership_timeline = {
                    'member_id': record.id,
                    'user': record.timeline_user_id.id,
                    'time': fields.Datetime.now(),
                    'status': '',
                    'timeline_status': record.membership_state,
                }

                agent_group = self.env['res.groups'].search([('name', '=', 'Agent')], limit=1)
                if agent_group and agent_group in record.timeline_user_id.groups_id:
                    membership_timeline['status'] = 'Membership Renewed (Handled by Agent)'
                    self.env['membership.timeline'].create(membership_timeline)
                else:
                    membership_timeline['status'] = 'Membership Renewed - Manual'
                    self.env['membership.timeline'].create(membership_timeline)

                record.member_activate_date = record.next_activation_date
                record.member_expiry_date = record.next_expiry_date
                record.product_template_id = record.next_product_template_id

                record.next_activation_date = False
                record.next_expiry_date = False
                record.next_product_template_id = False 
                record.timeline_user_id = False
                record.renewal_in_queue = False

