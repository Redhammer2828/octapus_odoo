from odoo import fields, models, api
import random

class CreateTemporaryMemberWizard(models.TransientModel):
    _name = 'create.temporary.member.wizard'
    _description = 'Create Temporary Member Wizard'

    problem_statement = fields.Char(string="Problem Statement", default="Do you want to create a temporary member?")
    
    # def action_proceed(self):
    #     """
    #     When 'Proceed' is clicked, open the membership form.
    #     """
    #     # Open the member form view to create a new member
    #     return {
    #         'name': 'Create Temporary Member',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'res.partner',
    #         'view_mode': 'form',
    #         'view_id': self.env.ref('customer.res_partner_member_form').id,
    #         'target': 'current',
    #         'context': {'default_member_type': 'policy'},  # Default member type could be adjusted
    #     }

    def _generate_temp_chassis_no(self):
        """
        Generate a random chassis number with the prefix 'TEMP'.
        """
        random_number = random.randint(100000, 999999)
        return f"TEMP{random_number}"
    
    def action_proceed(self):
        """
        When 'Proceed' is clicked, open the membership form.
        """

        # Fetch the parent customer ID for 'ARABIAN AUTOMOBILE ASSOCIATION QATAR'
        parent_customer = self.env['res.partner'].search([('name', '=', 'ARABIAN AUTOMOBILE ASSOCIATION')], limit=1)
        parent_customer_id = parent_customer.id if parent_customer else False
        # Open the member form view to create a new member
        return {
            'name': 'Create Temporary Member',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'form',
            'view_id': self.env.ref('customer.res_partner_member_form').id,
            'target': 'current',
            'context': {
                'default_member_type': 'policy',  # Default member type could be adjusted
                'default_parent_customer_id':  parent_customer_id,
                'default_vehicle_chasis_no': self._generate_temp_chassis_no(),
            },
        }


    def action_cancel(self):
        """
        When 'Cancel' is clicked, close the wizard.
        """
        return {'type': 'ir.actions.act_window_close'}
