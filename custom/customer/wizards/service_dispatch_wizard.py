from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ServiceDispatchWizard(models.TransientModel):
    _name = 'service.dispatch.wizard'
    _description = 'Service Dispatch Wizard'

    service_id = fields.Many2one('aaa.service', string="Service")
    is_schedule_service = fields.Boolean(string="Is Schedule Service")
    # message = fields.Text(string="Message", default="Service not in package, proceed with cash/credit service?")

    def action_cash_service(self):
        # Set cash type then route through dispatch method which performs validation
        self.service_id.write({'type': 'cash'})
        
        if self.is_schedule_service:
            return {
                'name': _('Schedule Service'),
                'type': 'ir.actions.act_window',
                'res_model': 'schedule.service.wizard',
                'view_mode': 'form',
                'view_id': self.env.ref('customer.schedule_service_wizard_view_form').id,
                'target': 'new',
                'context': {
                    'default_service_id': self.service_id.id,
                },
            }
            
        self.create_service_history()
        self.service_id._dispatch_service()
        return {'type': 'ir.actions.act_window_close'}

    def action_credit_service(self):
        # Set member_type to credit then route through dispatch for consistent validation
        self.service_id.write({'member_type': 'credit'})

        if self.is_schedule_service:
            return {
                'name': _('Schedule Service'),
                'type': 'ir.actions.act_window',
                'res_model': 'schedule.service.wizard',
                'view_mode': 'form',
                'view_id': self.env.ref('customer.schedule_service_wizard_view_form').id,
                'target': 'new',
                'context': {
                    'default_service_id': self.service_id.id,
                },
            }
        
        self.create_service_history()
        self.service_id._dispatch_service()
        return {'type': 'ir.actions.act_window_close'}

    def create_service_history(self):
        self.env['service.history'].create({
            'service_id': self.service_id.id,
            'user': self.env.user.id,
            'time': fields.Datetime.now(),
            'status': self.service_id.state,
        })