from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class MembershipExtensionWizard(models.TransientModel):
    _name = 'membership.extension.wizard'

    expiry_date = fields.Date('Expiry Date')
    new_expiry_date = fields.Date('New Expiry Date')
    issue_debit_note = fields.Boolean('Issue Debit Note')

    # def action_extension(self):
    #     partner = self.env['res.partner'].browse(self._context.get('active_id'))
 
    #     if not partner:
    #         raise UserError("No active partner found for extension.")
    #     # Create an entry in the membership.history model before updating the partner record
    #     mem_renewal = self.env['membership.history'].create({
    #         'name': partner.name,  # Using partner name
    #         'parent_customer_id': partner.parent_customer_id.id,
    #         'old_membership_number': partner.old_membership_number,  # Assuming old_membership_number exists
    #         'ref_num': partner.ref_num,
    #         'member_partner_category_id': partner.member_partner_category_id.id,
    #         'product_template_id': partner.product_template_id.id,
    #         'member_type': partner.member_type,
    #         'policy_no': partner.policy_no,
    #         'vehicle_chasis_no': partner.vehicle_chasis_no,
    #         'vehicle_plate': partner.vehicle_plate,
    #         'vehicle_type': partner.vehicle_type,
    #         'member_activate_date': partner.member_activate_date,
    #         'member_expiry_date': partner.member_expiry_date,  # Storing old expiry date
    #         'invoice_ref_date': partner.invoice_ref_date,
    #         'card_type_id': partner.card_type_id.id,
    #         'history_id': partner.id
    #     })
    #     self.env['membership.timeline'].create({
    #         'member_id': partner.id,
    #         'user': self.env.user.id,
    #         'time': fields.Datetime.now(),
    #         'status': 'Membership Extended',
    #         'timeline_status': partner.membership_state,
    #     })
    #     # Update the partner's expiry date with the new value
    #     partner.member_expiry_date = self.new_expiry_date
        
    #     #Check if the logged-in user is in the "Agent" group
    #     agent_group = self.env['res.groups'].search([('name', '=', 'Agent')], limit=1)
    #     if agent_group and agent_group in self.env.user.groups_id:
    #         partner.membership_state = 'temp'  # Only update if user is actually in the group

    def action_extension(self):
        if self.new_expiry_date <= self.expiry_date:
            raise UserError("New Expiry Date must be greater than old Expiry Date.")
        partner = self.env['res.partner'].browse(self._context.get('active_id'))

        if not partner:
            raise UserError("No active partner found for extension.")
        # Create an entry in the membership.history model before updating the partner record
        mem_renewal = self.env['membership.history'].create({
            'name': partner.name,  # Using partner name
            'parent_customer_id': partner.parent_customer_id.id,
            'old_membership_number': partner.old_membership_number,  
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
        # Check if the logged-in user is in the "Agent" group
        # agent_group = self.env['res.groups'].search([('name', '=', 'Agent')], limit=1)
        data_manager_group = self.env['res.groups'].search([('name', '=', 'Data Manager')], limit=1)
        if data_manager_group and data_manager_group in self.env.user.groups_id:

            # Default timeline entry for data manager users
            self.env['membership.timeline'].create({
                'member_id': partner.id,
                'user': self.env.user.id,
                'time': fields.Datetime.now(),
                'status': 'Membership Extended - Manual',
                'timeline_status': partner.membership_state,
            })
            
        else:
            partner = self.env['res.partner'].browse(self._context.get('active_id'))
            # If user is not in the "Data Manager" group, change membership_state and create a different timeline
            partner.membership_state = 'temp'
            
            self.env['membership.timeline'].create({
                'member_id': partner.id,
                'user': self.env.user.id,
                'time': fields.Datetime.now(),
                'status': 'Membership Extended by non Data Manager',
                'timeline_status': 'temp',
            })

        # Update the partner's expiry date with the new value
        partner.member_expiry_date = self.new_expiry_date
        partner.issue_debit_note = self.issue_debit_note
