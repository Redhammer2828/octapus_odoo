from odoo import fields, models, api

class CreateTemporaryMemberWizard(models.TransientModel):
    _name = 'create.temporary.member.wizard'
    _description = 'Create Temporary Member Wizard'

    problem_statement = fields.Char(string="Problem Statement", default="Do you want to create a temporary member?")
    
    def action_proceed(self):
        """
        When 'Proceed' is clicked, open the membership form.
        """
        # Open the member form view to create a new member
        return {
            'name': 'Create Temporary Member',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'form',
            'view_id': self.env.ref('customer.res_partner_member_form').id,
            'target': 'current',
            'context': {'default_member_type': 'policy'},  # Default member type could be adjusted
        }

    def action_cancel(self):
        """
        When 'Cancel' is clicked, close the wizard.
        """
        return {'type': 'ir.actions.act_window_close'}
