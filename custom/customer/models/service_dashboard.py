from odoo import models, fields, api
from datetime import datetime, timedelta

class ServiceDashboard(models.Model):
    _name = 'service.dashboard'
    _description = 'Service Dashboard'

    employee_id = fields.Many2one('hr.employee', string='Driver', help="Select a driver from registered employees.")
    input_driver_name = fields.Char(string='Search Driver Name', help="Input a driver's name to filter service records.")
    completed_today = fields.Integer(string='Completed Today', default=0, compute='_compute_service_data')
    cancelled_today = fields.Integer(string='Cancelled Today', default=0, compute='_compute_service_data')
    completed_week = fields.Integer(string='Completed This Week', default=0, compute='_compute_service_data')
    cancelled_week = fields.Integer(string='Cancelled This Week', default=0, compute='_compute_service_data')
    completed_month = fields.Integer(string='Completed This Month', default=0, compute='_compute_service_data')
    cancelled_month = fields.Integer(string='Cancelled This Month', default=0, compute='_compute_service_data')
    completed_year = fields.Integer(string='Completed This Year', default=0, compute='_compute_service_data')
    cancelled_year = fields.Integer(string='Cancelled This Year', default=0, compute='_compute_service_data')
    total_today = fields.Integer(string='Total Today', compute='_compute_total_service_data')
    total_week = fields.Integer(string='Total This Week', compute='_compute_total_service_data')
    total_month = fields.Integer(string='Total This Month', compute='_compute_total_service_data')
    total_year = fields.Integer(string='Total This Year', compute='_compute_total_service_data')

    @api.depends('employee_id', 'input_driver_name')
    def _compute_service_data(self):
        today = fields.Datetime.now()
        start_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_day = today.replace(hour=23, minute=59, second=59, microsecond=999999)

        start_week = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        end_week = (start_week + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=999999)

        start_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_month = (start_month + timedelta(days=(32 - start_month.day))).replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)

        start_year = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_year = today.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)

        for record in self:
            domain = []
            if record.employee_id:
                domain += [('driver_id', '=', record.employee_id.id)]
            if record.input_driver_name:
                domain += [('driver_name', 'ilike', record.input_driver_name)]

            domain_today = domain + [('service_time', '>=', start_day), ('service_time', '<=', end_day)]
            domain_week = domain + [('service_time', '>=', start_week), ('service_time', '<=', end_week)]
            domain_month = domain + [('service_time', '>=', start_month), ('service_time', '<=', end_month)]
            domain_year = domain + [('service_time', '>=', start_year), ('service_time', '<=', end_year)]

            service_model = self.env['aaa.service']
            record.completed_today = service_model.search_count(domain_today + [('state', '=', 'done')])
            record.cancelled_today = service_model.search_count(domain_today + [('state', '=', 'cancel')])
            record.completed_week = service_model.search_count(domain_week + [('state', '=', 'done')])
            record.cancelled_week = service_model.search_count(domain_week + [('state', '=', 'cancel')])
            record.completed_month = service_model.search_count(domain_month + [('state', '=', 'done')])
            record.cancelled_month = service_model.search_count(domain_month + [('state', '=', 'cancel')])
            record.completed_year = service_model.search_count(domain_year + [('state', '=', 'done')])
            record.cancelled_year = service_model.search_count(domain_year + [('state', '=', 'cancel')])

    @api.depends('completed_today', 'cancelled_today', 'completed_week', 'cancelled_week', 'completed_month', 'cancelled_month', 'completed_year', 'cancelled_year')
    def _compute_total_service_data(self):
        for record in self:
            record.total_today = record.completed_today + record.cancelled_today
            record.total_week = record.completed_week + record.cancelled_week
            record.total_month = record.completed_month + record.cancelled_month
            record.total_year = record.completed_year + record.cancelled_year

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """Clear the manual input if a driver is selected from the list."""
        if self.employee_id:
            self.input_driver_name = False

    @api.onchange('input_driver_name')
    def _onchange_input_driver_name(self):
        """Clear the dropdown selection if a name is manually typed into the search."""
        if self.input_driver_name:
            self.employee_id = False


