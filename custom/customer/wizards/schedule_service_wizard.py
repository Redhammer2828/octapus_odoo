from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta

class ScheduleServiceWizard(models.TransientModel):
    _name = 'schedule.service.wizard'
    _description = 'Schedule Service Wizard'

    service_id = fields.Many2one('aaa.service', string="Service")
    schedule_date = fields.Datetime(string='Schedule Date')
    action_date = fields.Datetime(string='Action Date')

    def action_schedule(self):
      
        for record in self:
            if not record.action_date or not record.schedule_date:
                raise UserError('Both action_date and schedule_date must be set.')
            if record.action_date == record.schedule_date:
                time_difference= record.schedule_date - record.action_date
                if time_difference <= timedelta(hours = 2):
                    raise UserError('The action_date must be at least 2 hours before the schedule_date.')
            if record.action_date > record.schedule_date:
                raise UserError('The action_date must be less than the schedule_date.')
            else:
                self.service_id.write({
                'schedule_date_time': self.schedule_date,
                'requested_date': self.action_date
        })
            return True
           

