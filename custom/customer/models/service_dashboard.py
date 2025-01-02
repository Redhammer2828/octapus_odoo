from odoo import models, fields, api
from datetime import timedelta

class ServiceDashboard(models.Model):
    _name = 'service.dashboard'
    _description = 'Service Dashboard'

    employee_id = fields.Many2one('hr.employee', string='Driver')
    driver_name = fields.Char(related='employee_id.name', string='Driver Name', readonly=True)
    completed_today = fields.Integer(string='Completed Today', compute='_compute_service_data')
    cancelled_today = fields.Integer(string='Cancelled Today', compute='_compute_service_data')
    completed_week = fields.Integer(string='Completed This Week', compute='_compute_service_data')
    cancelled_week = fields.Integer(string='Cancelled This Week', compute='_compute_service_data')
    completed_month = fields.Integer(string='Completed This Month', compute='_compute_service_data')
    cancelled_month = fields.Integer(string='Cancelled This Month', compute='_compute_service_data')
    completed_year = fields.Integer(string='Completed This Year', compute='_compute_service_data')
    cancelled_year = fields.Integer(string='Cancelled This Year', compute='_compute_service_data')
    total_today = fields.Integer(string='Total Today', compute='_compute_total_service_data')
    total_week = fields.Integer(string='Total This Week', compute='_compute_total_service_data')
    total_month = fields.Integer(string='Total This Month', compute='_compute_total_service_data')
    total_year = fields.Integer(string='Total This Year', compute='_compute_total_service_data')

    @api.depends('employee_id')
    def _compute_service_data(self):
        for record in self:
            if not record.employee_id:
                record.completed_today = record.cancelled_today = 0
                record.completed_week = record.cancelled_week = 0
                record.completed_month = record.cancelled_month = 0
                record.completed_year = record.cancelled_year = 0
                continue

            domain = [('driver_id', '=', record.employee_id.id)]
            today = fields.Datetime.now()

            # Compute Today
            domain_today = domain + [
                ('service_time', '>=', today.replace(hour=0, minute=0, second=0)),
                ('service_time', '<=', today.replace(hour=23, minute=59, second=59))
            ]
            record.completed_today = self.env['aaa.service'].search_count(domain_today + [('state', '=', 'done')])
            record.cancelled_today = self.env['aaa.service'].search_count(domain_today + [('state', '=', 'cancel')])

            # Compute This Week
            start_week = today - timedelta(days=today.weekday())
            end_week = start_week + timedelta(days=6)
            domain_week = domain + [
                ('service_time', '>=', start_week),
                ('service_time', '<=', end_week)
            ]
            record.completed_week = self.env['aaa.service'].search_count(domain_week + [('state', '=', 'done')])
            record.cancelled_week = self.env['aaa.service'].search_count(domain_week + [('state', '=', 'cancel')])

            # Compute This Month
            start_month = today.replace(day=1)
            next_month = start_month + timedelta(days=32)
            end_month = next_month.replace(day=1) - timedelta(days=1)
            domain_month = domain + [
                ('service_time', '>=', start_month),
                ('service_time', '<=', end_month)
            ]
            record.completed_month = self.env['aaa.service'].search_count(domain_month + [('state', '=', 'done')])
            record.cancelled_month = self.env['aaa.service'].search_count(domain_month + [('state', '=', 'cancel')])

            # Compute This Year
            start_year = today.replace(month=1, day=1)
            end_year = today.replace(month=12, day=31, hour=23, minute=59, second=59)
            domain_year = domain + [
                ('service_time', '>=', start_year),
                ('service_time', '<=', end_year)
            ]
            record.completed_year = self.env['aaa.service'].search_count(domain_year + [('state', '=', 'done')])
            record.cancelled_year = self.env['aaa.service'].search_count(domain_year + [('state', '=', 'cancel')])

    @api.depends('completed_today', 'cancelled_today', 'completed_week', 'cancelled_week', 'completed_month', 'cancelled_month', 'completed_year', 'cancelled_year')
    def _compute_total_service_data(self):
        for record in self:
            record.total_today = record.completed_today + record.cancelled_today
            record.total_week = record.completed_week + record.cancelled_week
            record.total_month = record.completed_month + record.cancelled_month
            record.total_year = record.completed_year + record.cancelled_year
