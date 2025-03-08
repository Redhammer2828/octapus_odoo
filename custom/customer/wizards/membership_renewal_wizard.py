from odoo import models, fields, api
import logging
from odoo.exceptions import ValidationError, UserError

logger = logging.getLogger(__name__)

class MembershipRenewalWizard(models.TransientModel):
    _name = 'membership.renewal.wizard'
    _description = "Membership Renewal Wizard"

    parent_customer_id = fields.Many2one('res.partner', string='Parent Customer')
    activation_date = fields.Date('Activation Date', required=True)
    card_type_id = fields.Many2one('card.type', string='Card Type', readonly=True)  # Read-only as it's fetched automatically
    expiry_date = fields.Date('Expiry Date', required=True)
    vehicle_chasis_no = fields.Char(string='Vehicle Chasis Number')
    product_template_id = fields.Many2one('product.template', string="Packages")

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
            defaults['card_type_id'] = partner.card_type_id.id

            # Log the card_type_id for debugging purposes
            logger.info("Default Card Type ID set in Wizard: %s", partner.card_type_id.id)

        return defaults

    # def action_renew(self):
    #     partner = self.env['res.partner'].browse(self._context.get('active_id'))
        
    #     if not partner:
    #         raise UserError("No active partner found for renewal.")
        
    #     # Log the values before the update
    #     logger.info("Updating Membership for Partner ID: %s", partner.id)
    #     logger.info("Card Type ID in Wizard: %s", self.card_type_id.id)

    #     # Update the partner record with the new membership values
    #     partner.write({
    #         'parent_customer_id': self.parent_customer_id.id,
    #         'member_activate_date': self.activation_date,
    #         'card_type_id': self.card_type_id.id,
    #         'member_expiry_date': self.expiry_date,
    #         'vehicle_chasis_no': self.vehicle_chasis_no,
    #         'product_template_id': self.product_template_id.id,
    #     })

    #     # Log the updated values after the write operation
    #     logger.info("Partner's updated Card Type ID: %s", partner.card_type_id.id)

    def action_renew(self):
            partner = self.env['res.partner'].browse(self._context.get('active_id'))
        
            if not partner:
                raise UserError("No active partner found for renewal.")
        
            # Log the values before the update
            logger.info("Updating Membership for Partner ID: %s", partner.id)
            logger.info("Card Type ID in Wizard: %s", self.card_type_id.id)
    
            # Create an entry in the membership.history model before updating the partner record
            mem_renewal = self.env['membership.history'].create({
                'name': partner.name,  # Using partner name
                'parent_customer_id': partner.parent_customer_id.id,
                'old_membership_number': partner.old_membership_number,  # Assuming ref is the membership number
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
            logger.info("Membership history record created with ID: %s", mem_renewal.id)
            # Update the partner record with the new membership values
            partner.write({
                'parent_customer_id': self.parent_customer_id.id,
                'member_activate_date': self.activation_date,
                'card_type_id': self.card_type_id.id,
                'member_expiry_date': self.expiry_date,
                'vehicle_chasis_no': self.vehicle_chasis_no,
                'product_template_id': self.product_template_id.id,
            })
            # Log the updated values after the write operation
            logger.info("Partner's updated Card Type ID: %s", partner.card_type_id.id)
