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

    def action_renew(self):
        partner = self.env['res.partner'].browse(self._context.get('active_id'))
        
        if not partner:
            raise UserError("No active partner found for renewal.")
        
        # Log the values before the update
        logger.info("Updating Membership for Partner ID: %s", partner.id)
        logger.info("Card Type ID in Wizard: %s", self.card_type_id.id)

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

