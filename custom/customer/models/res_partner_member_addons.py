from odoo import models,fields,api
from datetime import date

class ResPartnerMemberAddons(models.Model):
    _inherit = 'res.partner'

    next_activation_date = fields.Date(string="Next Activation Date")
    next_expiry_date = fields.Date(string="Next Expiry Date")
    next_product_template_id = fields.Many2one('product.template', string="Next Package")
    timeline_user_id = fields.Many2one('res.users', string="User")
    renewal_in_queue = fields.Boolean(string="Renewal in queue", default=False)
    remarks = fields.Text(string="Remarks")
    scheduled_on_date = fields.Datetime(string="Scheduled on")
    renewal_queue_data_ids = fields.One2many('renewal.queue.data','member_id',"Renewal Queue Data")
    is_renewal_in_queue_edit_mode = fields.Boolean(string="Renewal in queue Edit Mode", default=False)
    show_renewal_queue_data_page = fields.Boolean(string="Show renewal in queue page", default=False)

    def action_membership_renewal_scheduler(self):

        memberships = self.search([('renewal_in_queue', '=', True)])
        today = date.today()

        for record in memberships:
            if record.next_activation_date and today >= record.next_activation_date and record.next_expiry_date and record.next_product_template_id and record.timeline_user_id:

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

                if record.renewal_queue_data_ids:
                    record.name = record.renewal_queue_data_ids[0].name
                    record.policy_no = record.renewal_queue_data_ids[0].policy_no
                    record.invoice_ref_date = record.renewal_queue_data_ids[0].invoice_ref_date
                    record.delivery_ref_date = record.renewal_queue_data_ids[0].delivery_ref_date
                    record.card_type_id = record.renewal_queue_data_ids[0].card_type_id
                    record.member_partner_category_id = record.renewal_queue_data_ids[0].member_partner_category_id
                    record.vehicle_chasis_no = record.renewal_queue_data_ids[0].vehicle_chasis_no
                    record.vehicle_plate = record.renewal_queue_data_ids[0].vehicle_plate
                    record.street = record.renewal_queue_data_ids[0].street
                    record.mobile = record.renewal_queue_data_ids[0].mobile
                    record.remarks = record.renewal_queue_data_ids[0].remarks

                record.member_activate_date = record.next_activation_date
                record.member_expiry_date = record.next_expiry_date
                record.product_template_id = record.next_product_template_id

                record.next_activation_date = False
                record.next_expiry_date = False
                record.next_product_template_id = False 
                record.timeline_user_id = False
                record.scheduled_on_date = False
                record.renewal_in_queue = False
                record.renewal_queue_data_ids = [(5, 0, 0)]

    def cancel_renewal_in_queue(self):
        for record in self:

            self.env['membership.timeline'].create({
                'member_id': record.id,
                'user': self.env.user.id,
                'time': fields.Datetime.now(),
                'status': f'Cancelled Renewal in Queue. Activation Date:{record.next_activation_date}, Expiry Date:{record.next_expiry_date}',
                'timeline_status': 'cancel',
            })

            record.renewal_in_queue = False
            record.next_activation_date = False
            record.next_expiry_date = False
            record.next_product_template_id = False 
            record.timeline_user_id = False
            record.scheduled_on_date = False
            record.show_renewal_queue_data_page = False
            record.renewal_queue_data_ids = [(5, 0, 0)]

    def renewal_in_queue_edit_mode_on(self):
        for record in self:
            record.is_renewal_in_queue_edit_mode = True

    def renewal_in_queue_edit_mode_off(self):
        for record in self:
            record.is_renewal_in_queue_edit_mode = False


    
class RenewalQueueData(models.Model):
        _name = 'renewal.queue.data'
        _description = 'Renewal Queue Data'

        member_id = fields.Many2one('res.partner', string="Member ID")
        name = fields.Char(string="Name")
        member_expiry_date = fields.Date(string='Member Expiry Date')
        policy_no = fields.Char(string='Policy Number')
        member_activate_date = fields.Date(string='Member Activate Date')
        invoice_ref_date = fields.Date(string='Invoice Ref Date')
        delivery_ref_date = fields.Date(string='Delivery Ref Date')
        product_template_id = fields.Many2one('product.template', string="Package")
        card_type_id = fields.Many2one('card.type', string='Card Type')
        member_partner_category_id = fields.Many2one('partner.category',string='Category')
        vehicle_chasis_no = fields.Char(string='Vehicle Chasis No')
        vehicle_plate = fields.Char(string='Vehicle Plate')
        street = fields.Char(string='Street')
        mobile = fields.Char(string='Mobile', widget='phone')
        remarks = fields.Text(string="Remarks")

