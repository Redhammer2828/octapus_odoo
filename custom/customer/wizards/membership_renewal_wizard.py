from odoo import models, fields, api
import logging
from odoo.exceptions import ValidationError, UserError
from datetime import date

logger = logging.getLogger(__name__)

class MembershipRenewalWizard(models.TransientModel):
    _name = 'membership.renewal.wizard'
    _description = "Membership Renewal Wizard"

    name = fields.Char(string="Name")
    parent_customer_id = fields.Many2one('res.partner', string='Parent Customer')
    activation_date = fields.Date('Activation Date', required=True)
    card_type_id = fields.Many2one('card.type', string='Card Type', readonly=False)  # Read-only as it's fetched automatically
    expiry_date = fields.Date('Expiry Date', required=True)
    vehicle_chasis_no = fields.Char(string='Vehicle Chasis Number')
    product_template_id = fields.Many2one('product.template', string="Packages")
    policy_no = fields.Char(string='Policy Number')
    invoice_ref_date = fields.Date(string='Invoice Date')
    delivery_ref_date = fields.Date(string='Delivery Date')
    vehicle_plate = fields.Char(string='Vehicle Plate')

    @api.model
    def default_get(self, fields_list):
        """
        Override the default_get method to fetch the card_type_id from res.partner and set it in the wizard.
        """
        # Fetch the default values using the parent method
        defaults = super(MembershipRenewalWizard, self).default_get(fields_list)
        # Get the active partner record from the context
        active_id = self.env.context.get('active_id')
        partner = self.env['res.partner'].browse(active_id)

        if partner:
            # Set the card_type_id from the partner in the wizard defaults
            defaults['name'] = partner.name
            defaults['card_type_id'] = partner.card_type_id.id
            defaults['policy_no'] = partner.policy_no
            defaults['invoice_ref_date'] = partner.invoice_ref_date
            defaults['delivery_ref_date'] = partner.delivery_ref_date
            defaults['vehicle_plate'] = partner.vehicle_plate
            # Log the card_type_id for debugging purposes
            logger.info("Default Card Type ID set in Wizard: %s", partner.card_type_id.id)

        return defaults

    # def action_renew(self):
    #         partner = self.env['res.partner'].browse(self._context.get('active_id'))
        
    #         if not partner:
    #             raise UserError("No active partner found for renewal.")
        
    #         # Log the values before the update
    #         logger.info("Updating Membership for Partner ID: %s", partner.id)
    #         logger.info("Card Type ID in Wizard: %s", self.card_type_id.id)
    
    #         # Create an entry in the membership.history model before updating the partner record
    #         mem_renewal = self.env['membership.history'].create({
    #             'name': partner.name,  # Using partner name
    #             'parent_customer_id': partner.parent_customer_id.id,
    #             'old_membership_number': partner.old_membership_number,  # Assuming ref is the membership number
    #             'ref_num': partner.ref_num,
    #             'member_partner_category_id': partner.member_partner_category_id.id,
    #             'product_template_id': partner.product_template_id.id,
    #             'member_type': partner.member_type,
    #             'policy_no': partner.policy_no,
    #             'vehicle_chasis_no': partner.vehicle_chasis_no,
    #             'vehicle_plate': partner.vehicle_plate,
    #             'vehicle_type': partner.vehicle_type,
    #             'member_activate_date': partner.member_activate_date,
    #             'member_expiry_date': partner.member_expiry_date,
    #             'invoice_ref_date': partner.invoice_ref_date,
    #             'card_type_id': partner.card_type_id.id,
    #             'history_id': partner.id
    #         })
    #         self.env['membership.timeline'].create({
    #             'member_id': partner.id,
    #             'user': self.env.user.id,
    #             'time': fields.Datetime.now(),
    #             'status': 'Membership Renewed',
    #             'timeline_status': partner.membership_state,
    #         })
    #         # Update the partner record with the new membership values
    #         partner.write({
    #             'parent_customer_id': self.parent_customer_id.id,
    #             'member_activate_date': self.activation_date,
    #             'card_type_id': self.card_type_id.id,
    #             'member_expiry_date': self.expiry_date,
    #             'vehicle_chasis_no': self.vehicle_chasis_no,
    #             'product_template_id': self.product_template_id.id,
    #         })
    #         # Log the updated values after the write operation
    #                 #Check if the logged-in user is in the "Agent" group
    #         agent_group = self.env['res.groups'].search([('name', '=', 'Agent')], limit=1)
    #         if agent_group and agent_group in self.env.user.groups_id:
    #             partner.membership_state = 'temp'  # Only update if user is actually in the group

    def action_renew(self):

        partner_id = self._context.get('active_id')
       
        if self.expiry_date <= self.activation_date:
            raise UserError("Expiry Date must be greater than Activation Date.")
        partner = self.env['res.partner'].browse(partner_id)
        if not partner:
            raise UserError("No active partner found for renewal.")
        
        if self.env.user.partner_id.is_agent_user == True:
            services = self.env['aaa.service'].search([('member_id', '=', partner_id), ('vehicle_chasis_no', '=', self.vehicle_chasis_no), ('customer_id', '=', self.parent_customer_id.id), ('state', 'not in', ['cancel', 'done_cancel'])])

            for service in services:
                service_date = service.service_time.date()
                if service_date >= self.activation_date:
                    formatted_date = self.activation_date.strftime("%d-%m-%Y")
                    raise UserError(f"Cannot renew membership. There are active services on or after the activation date {formatted_date}.")
                

        # Log the values before the update
        logger.info("Updating Membership for Partner ID: %s", partner.id)
        logger.info("Card Type ID in Wizard: %s", self.card_type_id.id)

        membership_timeline = {
                'member_id': partner.id,
                'user': self.env.user.id,
                'time': fields.Datetime.now(),
                'status': '',
                'timeline_status': '',
            }

        today = date.today()

        if today >= self.activation_date:

            # Create an entry in the membership.history model before updating the partner record
            self.env['membership.history'].create({
                'name': partner.name,  
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
                'member_expiry_date': partner.member_expiry_date,
                'invoice_ref_date': partner.invoice_ref_date,
                'card_type_id': partner.card_type_id.id,
                'history_id': partner.id
            })

        
            # Check if the logged-in user is in the "Agent" group
            agent_group = self.env['res.groups'].search([('name', '=', 'Agent')], limit=1)
            if agent_group and agent_group in self.env.user.groups_id:
                # If user is in the "Agent" group, change membership_state and create a different timeline
                partner.membership_state = 'temp'
                membership_timeline['status'] = 'Membership Renewed - Handled by Agent'
                membership_timeline['timeline_status'] = 'temp'
                self.env['membership.timeline'].create(membership_timeline)
            else:
                # Default timeline entry for non-agent users
                membership_timeline['status'] = 'Membership Renewed - Manual'
                membership_timeline['timeline_status'] = partner.membership_state
                self.env['membership.timeline'].create(membership_timeline)

            # Update the partner record with the new membership values
            
            partner.write({
                'name': self.name,
                'parent_customer_id': self.parent_customer_id.id,
                'member_activate_date': self.activation_date,
                'card_type_id': self.card_type_id.id,
                'member_expiry_date': self.expiry_date,
                'vehicle_chasis_no': self.vehicle_chasis_no,
                'product_template_id': self.product_template_id.id,
                'policy_no': self.policy_no,
                'vehicle_plate': self.vehicle_plate,
                'invoice_ref_date': self.invoice_ref_date,
                'delivery_ref_date': self.delivery_ref_date,
            })

            logger.info("Membership renewed for Partner ID: %s", partner.id)

        else:

            if partner.renewal_in_queue:
                raise UserError(f"Membership renewal already initiated. Will be automatically renewed on {partner.next_activation_date}")
            
            elif partner.membership_state == 'temp':
                raise UserError(f"Membership already renewed temporarily by AGENT.")
            
            else:
                # Check if the logged-in user is in the "Agent" group
                agent_group = self.env['res.groups'].search([('name', '=', 'Agent')], limit=1)
                it_group = self.env['res.groups'].search([('name', '=', 'IT Group')], limit=1)
                if agent_group and agent_group in self.env.user.groups_id:
                    # If user is in the "Agent" group, change membership_state and create a different timeline

                    self.env['membership.history'].create({
                        'name': partner.name,  
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
                        'member_expiry_date': partner.member_expiry_date,
                        'invoice_ref_date': partner.invoice_ref_date,
                        'card_type_id': partner.card_type_id.id,
                        'history_id': partner.id
                    })

                    partner.membership_state = 'temp'
                    membership_timeline['status'] = 'Membership Renewed - Handled by Agent'
                    membership_timeline['timeline_status'] = 'temp'
                    self.env['membership.timeline'].create(membership_timeline)

                    partner.write({
                        'name': self.name,
                        'parent_customer_id': self.parent_customer_id.id,
                        'member_activate_date': self.activation_date,
                        'card_type_id': self.card_type_id.id,
                        'member_expiry_date': self.expiry_date,
                        'vehicle_chasis_no': self.vehicle_chasis_no,
                        'product_template_id': self.product_template_id.id,
                        'policy_no': self.policy_no,
                        'vehicle_plate': self.vehicle_plate,
                        'invoice_ref_date': self.invoice_ref_date,
                        'delivery_ref_date': self.delivery_ref_date,
                    })

                    logger.info("Membership renewed for Partner ID: %s", partner.id)

                elif it_group and it_group in self.env.user.groups_id:
                    # Default timeline entry for non-agent users
                    membership_timeline['status'] = f'Membership Renewal in Queue - Manual (Activation Date: {self.activation_date}, Expiry Date: {self.expiry_date})'
                    membership_timeline['timeline_status'] = partner.membership_state
                    self.env['membership.timeline'].create(membership_timeline)

                    renewal_queue_data_ids_items = {
                        'name': self.name,
                        'card_type_id': self.card_type_id.id,
                        'policy_no': self.policy_no,
                        'ref_num': partner.ref_num,
                        'member_partner_category_id': partner.member_partner_category_id.id,
                        'vehicle_plate': self.vehicle_plate,
                        'vehicle_type': partner.vehicle_type,
                        'vehicle_chasis_no': self.vehicle_chasis_no,
                        'invoice_ref_date': self.invoice_ref_date,
                        'delivery_ref_date': self.delivery_ref_date,
                        'member_activate_date': self.activation_date,
                        'member_expiry_date': self.expiry_date,
                    }

                    partner.write({
                        'next_activation_date': self.activation_date,
                        'next_expiry_date': self.expiry_date,
                        'next_product_template_id': self.product_template_id.id,
                        'timeline_user_id': self.env.user.id,
                        'scheduled_on_date': fields.Datetime.now(),
                        'renewal_in_queue': True,
                        'show_renewal_queue_data_page': True,
                        'renewal_queue_data_ids':[(0,0,renewal_queue_data_ids_items)]
                    })

                    logger.info(f"Membership for Partner ID: {partner.id} will be renewed on {self.activation_date}")
