from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ServiceLimitWizard(models.TransientModel):
    _name = 'service.limit.wizard'
    _description = 'Service Limit Wizard'

    service_id = fields.Many2one('aaa.service', string='Service', required=True)
    message = fields.Text(string='Message', readonly=True)
    existing_service_count = fields.Integer(string='Services Used', readonly=True)
    service_limit = fields.Integer(string='Service Limit', readonly=True)
    service_type = fields.Char(string='Service Type', readonly=True)
    limit_period = fields.Char(string='Limit Period', readonly=True)
    period_description = fields.Char(string='Period Description', readonly=True)
    show_proceed_only = fields.Boolean(string='Show Proceed Only', default=False, help='If true, only show the Proceed button in the wizard.')
    is_schedule_service = fields.Boolean(string='Is Schedule Service', default=False)

    def action_restrict(self):
        """Record that user chose not to proceed and close the wizard."""
        self.service_id.service_history_ids.create({
            'service_id': self.service_id.id,
            'user': self.env.user.id,
            'time': fields.Datetime.now(),
            'status': f'Service restricted due to limit (0/{self.service_limit} {self.service_type} allowed in {self.limit_period})',
            'timeline_status': 'initiate'
        })
        return {'type': 'ir.actions.act_window_close'}

    def action_proceed(self):
        """Allow dispatch to proceed and record in service history"""
        # Mark service as proceeded out-of-limit
        self.service_id.write({'is_out_of_limit_proceeded': True})

        if self.is_schedule_service:
            self.service_id.service_history_ids.create({
                'service_id': self.service_id.id,
                'user': self.env.user.id,
                'time': fields.Datetime.now(),
                'status': f'Service limit exceeded - Proceeded to schedule service for dispatch ({self.existing_service_count}/{self.service_limit} {self.service_type} services used in {self.limit_period} period)',
                'timeline_status': 'initiate'
            })
            
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
        
        # Add service history entry for proceed action
        self.service_id.service_history_ids.create({
            'service_id': self.service_id.id,
            'user': self.env.user.id,
            'time': fields.Datetime.now(),
            'status': f'Service limit exceeded - Proceeded with dispatch ({self.existing_service_count}/{self.service_limit} {self.service_type} services used in {self.limit_period} period)',
            'timeline_status': 'dispatch'
        })
        
        # Continue with normal dispatch logic
        self.service_id._dispatch_service()
        
        return {'type': 'ir.actions.act_window_close'}

    def action_restrict(self):
        """Restrict dispatch and record in service history"""
        # Add service history entry for restrict action
        self.service_id.service_history_ids.create({
            'service_id': self.service_id.id,
            'user': self.env.user.id,
            'time': fields.Datetime.now(),
            'status': f'Service limit exceeded - Dispatch restricted ({self.existing_service_count}/{self.service_limit} {self.service_type} services used in {self.limit_period} period)',
            'timeline_status': 'initiate'  # Keep in initiate state
        })
        
        # Show restriction message and close wizard
        message = _('Service dispatch has been restricted due to service limit being reached.')
        
        # Display notification and close wizard
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Service Restricted'),
                'message': message,
                'type': 'info',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }