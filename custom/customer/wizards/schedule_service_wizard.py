from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta
 
class ScheduleServiceWizard(models.TransientModel):
    _name = 'schedule.service.wizard'
    _description = 'Schedule Service Wizard'
 
    service_id = fields.Many2one('aaa.service', string="Service")
    schedule_date = fields.Datetime(string='Schedule Date')
    action_date = fields.Datetime(string='Action Date', required=True)
 
    @api.onchange('schedule_date')
    def _onchange_schedule_date(self):
        """Automatically set action_date to be one hour before schedule_date."""
        if self.schedule_date:
            self.action_date = self.schedule_date - timedelta(hours=1)
 
    def action_schedule(self):
        for record in self:
            # Ensure both dates are set
            if not record.action_date or not record.schedule_date:
                raise UserError('Both Action Date and Schedule Date must be set.')
 
            # Validate that action_date is at least 1 hour before schedule_date
            if record.action_date >= record.schedule_date:
                raise UserError('The Action Date must be at least 1 hour before the Schedule Date.')
 
            # Update service with schedule and action dates
            record.service_id.write({
                'schedule_date_time': record.schedule_date,
                'requested_date': record.action_date,
            })
       
        return True