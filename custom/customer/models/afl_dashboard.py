from odoo import models, fields, api
from datetime import datetime, time

class AFLServiceDashboard(models.Model):
    _name = 'afl.dashboard'
    _description = 'AFL Service Dashboard'

    job_ref = fields.Char(string="Job Ref No")
    ser_id = fields.Char(string="Service ID")
    state = fields.Selection([
        ('open', 'Open'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ('initiate', 'Initiated'),
        ('progress', 'In Progress'),
        ('driver_cancel_reach', 'Driver Reached and Cancelled')
    ], string="State")
    comment_text = fields.Text(compute='_compute_comment_text', string="Comments")
    initiate_date = fields.Datetime(string="Initiation Date")
    driver_reach_date = fields.Datetime(string="Driver Reached Date")

    # Computed fields for counting various states
    total_count = fields.Integer(string="Total Services", compute='_compute_service_counts')
    done_count = fields.Integer(string="Services Completed", compute='_compute_service_counts')
    cancelled_count = fields.Integer(string="Services Cancelled", compute='_compute_service_counts')
    driver_cancel_reach_count = fields.Integer(string="Driver Reached & Cancelled", compute='_compute_service_counts')
    open_count = fields.Integer(string="Open Services", compute='_compute_service_counts')
    initiate_count = fields.Integer(string="Services Initiated", compute='_compute_service_counts')
    progress_count = fields.Integer(string="Services in Progress", compute='_compute_service_counts')

    start_today = datetime.combine(fields.Date.today(), time.min)
    end_today = datetime.combine(fields.Date.today(), time.max)

    @api.depends('state')
    def _compute_service_counts(self):
        Service = self.env['aaa.service']  # Reference to the 'aaa.service' model
        # Define the additional filter for 'customer_id'
        # customer_filter = [('customer_id', '=', 'AL FUTTAIM LOGISTICS AUTOMOTIVE COMPANY L.L.C')]
        customer_filter = [('customer_id', '=', 'AL FUTTAIM LOGISTICS AUTOMOTIVE COMPANY L.L.C'), ('service_time', '>=', self.start_today), ('service_time', '<=', self.end_today)]

        # Apply the new filter along with existing conditions in search_count
        self.total_count = Service.search_count(customer_filter)
        self.done_count = Service.search_count(customer_filter + [('state', '=', 'done')])
        self.cancelled_count = Service.search_count(customer_filter + [('state', '=', 'cancel')])
        self.driver_cancel_reach_count = Service.search_count(customer_filter + [('state', '=', 'driver_cancel_reach')])
        self.open_count = Service.search_count(customer_filter + [('state', '=', 'open')])
        self.initiate_count = Service.search_count(customer_filter + [('state', '=', 'initiate')])
        self.progress_count = Service.search_count(customer_filter + [('state', '=', 'progress')])


    @api.depends('job_ref', 'ser_id', 'state')
    def _compute_comment_text(self):
        for record in self:
            record.comment_text = f"Service {record.ser_id} - {record.job_ref}: {dict(self._fields['state'].selection).get(record.state, 'Unknown')}"


    def action_afl_dashboard_total(self):

        return {
            'type': 'ir.actions.act_window',
            'name': "Today's Services",
            'res_model': 'aaa.service',
            'view_mode': 'tree',
            'view_id': self.env.ref('customer.view_aaa_service_tree').id,
            'domain': [
                ('customer_id', '=', 'AL FUTTAIM LOGISTICS AUTOMOTIVE COMPANY L.L.C'),
                ('service_time', '>=', self.start_today),
                ('service_time', '<=', self.end_today)
            ],
            'context': {
                'create': False,
                'edit': False
            }
        }
    
    def action_afl_dashboard_completed(self):

        return {
            'type': 'ir.actions.act_window',
            'name': "Today's Services",
            'res_model': 'aaa.service',
            'view_mode': 'tree',
            'view_id': self.env.ref('customer.view_aaa_service_tree').id,
            'domain': [
                ('customer_id', '=', 'AL FUTTAIM LOGISTICS AUTOMOTIVE COMPANY L.L.C'),
                ('service_time', '>=', self.start_today),
                ('service_time', '<=', self.end_today),
                ('state', '=', 'done'),

            ],
            'context': {
                'create': False,
                'edit': False
            }
        }
    
    def action_afl_dashboard_cancelled(self):

        return {
            'type': 'ir.actions.act_window',
            'name': "Today's Services",
            'res_model': 'aaa.service',
            'view_mode': 'tree',
            'view_id': self.env.ref('customer.view_aaa_service_tree').id,
            'domain': [
                ('customer_id', '=', 'AL FUTTAIM LOGISTICS AUTOMOTIVE COMPANY L.L.C'),
                ('service_time', '>=', self.start_today),
                ('service_time', '<=', self.end_today),
                ('state', '=', 'cancel'),
            ],
            'context': {
                'create': False,
                'edit': False
            }
        }
    
    def action_afl_dashboard_driver_cancel_reach(self):

        return {
            'type': 'ir.actions.act_window',
            'name': "Today's Services",
            'res_model': 'aaa.service',
            'view_mode': 'tree',
            'view_id': self.env.ref('customer.view_aaa_service_tree').id,
            'domain': [
                ('customer_id', '=', 'AL FUTTAIM LOGISTICS AUTOMOTIVE COMPANY L.L.C'),
                ('service_time', '>=', self.start_today),
                ('service_time', '<=', self.end_today),
                ('state', '=', 'driver_cancel_reach'),
            ],
            'context': {
                'create': False,
                'edit': False
            }
        }
    
    def action_afl_dashboard_initiated(self):

        return {
            'type': 'ir.actions.act_window',
            'name': "Today's Services",
            'res_model': 'aaa.service',
            'view_mode': 'tree',
            'view_id': self.env.ref('customer.view_aaa_service_tree').id,
            'domain': [
                ('customer_id', '=', 'AL FUTTAIM LOGISTICS AUTOMOTIVE COMPANY L.L.C'),
                ('service_time', '>=', self.start_today),
                ('service_time', '<=', self.end_today),
                ('state', '=', 'initiate'),
            ],
            'context': {
                'create': False,
                'edit': False
            }
        }
    