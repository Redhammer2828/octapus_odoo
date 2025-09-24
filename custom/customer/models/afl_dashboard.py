from odoo import models, fields, api
from datetime import datetime, time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from pytz import timezone, UTC  # pytz is available in Odoo

class AFLServiceDashboard(models.Model):
    _name = 'afl.dashboard'
    _description = 'AFL Service Dashboard'

    name = fields.Char(string="Name", default="Service Dashboard")
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
    assigned_sla_count = fields.Float(string="Assigned SLA %", compute='_compute_assigned_sla_count')
    reached_sla_count = fields.Float(string="Reached SLA %", compute='_compute_reached_sla_count')  # Placeholder, implement if needed


    # What'sApp related fields
    today_whatsapp_count = fields.Integer(string="Today's WhatsApp Services", compute='_compute_whatsapp_service_counts')
    whatsapp_done_count = fields.Integer(string="Whatsapp Services Completed", compute='_compute_whatsapp_service_counts')
    whatsapp_cancel_count = fields.Integer(string="Whatsapp Services Completed", compute='_compute_whatsapp_service_counts')

    
    def today_utc_bounds(self):
        # Get user's timezone or fallback to UTC
        tz_name = self.env.user.tz or 'UTC'
        tz = timezone(tz_name)
        # Today's date in that timezone
        today_local_date = datetime.now(tz).date() 
        # Start and end of local day
        start_local = tz.localize(datetime.combine(today_local_date, time.min))
        end_local = tz.localize(datetime.combine(today_local_date, time(23, 59, 59)))

        # Convert to UTC-aware datetimes
        start_utc = start_local.astimezone(UTC)
        end_utc = end_local.astimezone(UTC)

        # If you need strings in server format for search domains:
        return (
            start_utc.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            end_utc.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
        )

    @api.depends('state')
    def _compute_service_counts(self):
        Service = self.env['aaa.service']  # Reference to the 'aaa.service' model
        # Define the additional filter for 'customer_id'
        # customer_filter = [('customer_id', '=', 'AL FUTTAIM LOGISTICS AUTOMOTIVE COMPANY L.L.C')].
        start_utc_str, end_utc_str = self.today_utc_bounds()
        print(f"Start of day {start_utc_str}")
        print(f"End of day {end_utc_str}")
        # customer_filter = [('customer_id', '=', 'AL FUTTAIM LOGISTICS AUTOMOTIVE COMPANY L.L.C'), ('service_time', '>=', start_utc_str), ('service_time', '<=', end_utc_str)]
        customer_filter = [('is_afl_application', '=', True), ('service_time', '>=', start_utc_str), ('service_time', '<=', end_utc_str)]

        # Apply the new filter along with existing conditions in search_count
        self.total_count = Service.search_count(customer_filter)
        self.done_count = Service.search_count(customer_filter + [('state', '=', 'done')])
        self.cancelled_count = Service.search_count(customer_filter + [('state', '=', 'cancel')])
        self.driver_cancel_reach_count = Service.search_count(customer_filter + [('state', '=', 'driver_cancel_reach')])
        self.open_count = Service.search_count(customer_filter + [('state', '=', 'open')])
        self.initiate_count = Service.search_count(customer_filter + [('state', '=', 'initiate')])
        self.progress_count = Service.search_count(customer_filter + [('state', '=', 'start')])


    @api.depends('state')
    def _compute_whatsapp_service_counts(self):
        Service = self.env['aaa.service']     # Reference to the 'aaa.service' model
        # Define the additional filter for 'customer_id'
        start_utc_str, end_utc_str = self.today_utc_bounds()
        print(f"Start of day {start_utc_str}")
        print(f"End of day {end_utc_str}")
        # customer_filter = [('customer_id', '=', 'AL FUTTAIM LOGISTICS AUTOMOTIVE COMPANY L.L.C'), ('service_time', '>=', start_utc_str), ('service_time', '<=', end_utc_str)]
        customer_filter = [('is_whatsapp_service', '=', True), ('service_time', '>=', start_utc_str), ('service_time', '<=', end_utc_str)]
        self.today_whatsapp_count = Service.search_count(customer_filter)
        self.whatsapp_done_count = Service.search_count(customer_filter + [('state', '=', 'done')])
        self.whatsapp_cancel_count = Service.search_count(customer_filter + [('state', 'in',['cancel','done_cancel'] )])

    @api.depends('state')
    def _compute_assigned_sla_count(self):
        Service = self.env['aaa.service']
        start_utc_str, end_utc_str = self.today_utc_bounds()

        # Get services with valid dispatched_time and create_date
        services = Service.search([
            ('is_afl_application', '=', True),
            ('service_time', '>=', start_utc_str),
            ('service_time', '<=', end_utc_str),
            ('dispatched_time', '!=', False),
            ('create_date', '!=', False),
        ]) 
        # Count services that met the SLA (dispatched within 10 minutes)
        met_service_count = 0
        total_services_count = len(services)

        for service in services:
            if service.dispatched_time and service.create_date:
                diff = service.dispatched_time - service.create_date
                if diff.total_seconds() <= 600:  # 10 minutes = 600 seconds
                    met_service_count += 1

        # Calculate SLA percentage using existing total_count field
        if self.total_count > 0 and total_services_count > 0:
            self.assigned_sla_count = (met_service_count / total_services_count) * 100
        else:
            self.assigned_sla_count = 0.0

    @api.depends('state')
    def _compute_reached_sla_count(self):
        Service = self.env['aaa.service']
        start_utc_str, end_utc_str = self.today_utc_bounds()

        # Get services with valid create_date and reached_time
        services = Service.search([
            ('is_afl_application', '=', True),
            ('service_time', '>=', start_utc_str),
            ('service_time', '<=', end_utc_str),
            ('create_date', '!=', False),
            ('reached_time', '!=', False),
        ])

        met_reached_count = 0
        total_reached_count = len(services)

        for service in services:
            if service.create_date and service.reached_time:
                # Calculate time difference
                diff = service.reached_time - service.create_date
                # Check if difference is less than or equal to 1 hour (3600 seconds)
                if diff.total_seconds() <= 3600:
                    met_reached_count += 1

        # Calculate SLA percentage: (met reached count / total reached count) * 100
        if total_reached_count > 0:
            self.reached_sla_count = (met_reached_count / total_reached_count) * 100
        else:
            self.reached_sla_count = 0.0

    @api.depends('job_ref', 'ser_id', 'state')
    def _compute_comment_text(self):
        for record in self:
            record.comment_text = f"Service {record.ser_id} - {record.job_ref}: {dict(self._fields['state'].selection).get(record.state, 'Unknown')}"
 
    def action_afl_dashboard_total(self):
        start_utc_str, end_utc_str = self.today_utc_bounds()
        return {
            'type': 'ir.actions.act_window',
            'name': "Today's Services",
            'res_model': 'aaa.service',
            'view_mode': 'tree',
            'view_id': self.env.ref('customer.view_aaa_service_tree').id,
            'domain': [
                ('is_afl_application', '=', True),
                ('service_time', '>=', start_utc_str),
                ('service_time', '<=', end_utc_str)
            ],
            'context': {
                'create': False,
                'edit': False
            }
        }
    
    def action_afl_dashboard_completed(self):
        start_utc_str, end_utc_str = self.today_utc_bounds()
        return {
            'type': 'ir.actions.act_window',
            'name': "Today's Services",
            'res_model': 'aaa.service',
            'view_mode': 'tree',
            'view_id': self.env.ref('customer.view_aaa_service_tree').id,
            'domain': [
                ('is_afl_application', '=', True),
                ('service_time', '>=', start_utc_str),
                ('service_time', '<=', end_utc_str),
                ('state', '=', 'done'),
            ],
            'context': {
                'create': False,
                'edit': False
            }
        }
    
    def action_afl_dashboard_cancelled(self):
        start_utc_str, end_utc_str = self.today_utc_bounds()
        return {
            'type': 'ir.actions.act_window',
            'name': "Today's Services",
            'res_model': 'aaa.service',
            'view_mode': 'tree',
            'view_id': self.env.ref('customer.view_aaa_service_tree').id,
            'domain': [
                ('is_afl_application', '=', True),
                ('service_time', '>=', start_utc_str),
                ('service_time', '<=', end_utc_str),
                ('state', '=', 'cancel'),
            ],
            'context': {
                'create': False,
                'edit': False
            }
        }
    
    def action_afl_dashboard_driver_cancel_reach(self):
        start_utc_str, end_utc_str = self.today_utc_bounds()
        return {
            'type': 'ir.actions.act_window',
            'name': "Today's Services",
            'res_model': 'aaa.service',
            'view_mode': 'tree',
            'view_id': self.env.ref('customer.view_aaa_service_tree').id,
            'domain': [
                ('is_afl_application', '=', True),
                ('service_time', '>=', start_utc_str),
                ('service_time', '<=', end_utc_str),
                ('state', '=', 'driver_cancel_reach'),
            ],
            'context': {
                'create': False,
                'edit': False
            }
        }
    
    def action_afl_dashboard_initiated(self):
        start_utc_str, end_utc_str = self.today_utc_bounds()
        return {
            'type': 'ir.actions.act_window',
            'name': "Today's Services",
            'res_model': 'aaa.service',
            'view_mode': 'tree',
            'view_id': self.env.ref('customer.view_aaa_service_tree').id,
            'domain': [
                ('is_afl_application', '=', True),
                ('service_time', '>=', start_utc_str),
                ('service_time', '<=', end_utc_str),
                ('state', '=', 'initiate'),
            ],
            'context': {
                'create': False,
                'edit': False
            }
        }
    def action_afl_dashboard_inprogress(self):
        start_utc_str, end_utc_str = self.today_utc_bounds()
        return {
            'type': 'ir.actions.act_window',
            'name': "Today's Services",
            'res_model': 'aaa.service',
            'view_mode': 'tree',
            'view_id': self.env.ref('customer.view_aaa_service_tree').id,
            'domain': [
                ('is_afl_application', '=', True),
                ('service_time', '>=', start_utc_str),
                ('service_time', '<=', end_utc_str),
                ('state', '=', 'start'),
            ],
            'context': {
                'create': False,
                'edit': False
            }
        }
    
    #What'sApp related action 
    def action_dashboard_todays_whatsapp(self):
        start_utc_str, end_utc_str = self.today_utc_bounds()
        return {
            'type': 'ir.actions.act_window',
            'name': "Today's Whatsapp Services",
            'res_model': 'aaa.service',
            'view_mode': 'tree',
            'view_id': self.env.ref('customer.view_aaa_service_tree').id,
            'domain': [
                ('is_whatsapp_service', '=', True),
                ('service_time', '>=', start_utc_str),
                ('service_time', '<=', end_utc_str)
            ],
            'context': {
                'create': False,
                'edit': False
            }
        }
    
    def action_whatsaspp_service_completed(self):
        start_utc_str, end_utc_str = self.today_utc_bounds()
        return {
            'type': 'ir.actions.act_window',
            'name': "Today's Services",
            'res_model': 'aaa.service',
            'view_mode': 'tree',
            'view_id': self.env.ref('customer.view_aaa_service_tree').id,
            'domain': [
                ('is_whatsapp_service', '=', True),
                ('service_time', '>=', start_utc_str),
                ('service_time', '<=', end_utc_str),
                ('state', '=', 'done'),
            ],
            'context': {
                'create': False,
                'edit': False
            }
        }
    
    def action_whatsapp_cancelled(self):
        start_utc_str, end_utc_str = self.today_utc_bounds()
        return {
            'type': 'ir.actions.act_window',
            'name': "Today's Services",
            'res_model': 'aaa.service',
            'view_mode': 'tree',
            'view_id': self.env.ref('customer.view_aaa_service_tree').id,
            'domain': [
                ('is_whatsapp_service', '=', True),
                ('service_time', '>=', start_utc_str),
                ('service_time', '<=', end_utc_str),
                ('state', '=', 'cancel'),
            ],
            'context': {
                'create': False,
                'edit': False
            }
        }
    
    def action_afl_dashboard_assigned_sla(self):
        start_utc_str, end_utc_str = self.today_utc_bounds()
        return {
            'type': 'ir.actions.act_window',
            'name': "Today's Assigned SLA Services",
            'res_model': 'aaa.service',
            'view_mode': 'tree',
            'view_id': self.env.ref('customer.view_aaa_service_tree').id,
            'domain': [
                ('is_afl_application', '=', True),
                ('service_time', '>=', start_utc_str),
                ('service_time', '<=', end_utc_str),
            ],
            'context': {
                'create': False,
                'edit': False
            }
        }
    def action_afl_dashboard_reached_sla(self):
        start_utc_str, end_utc_str = self.today_utc_bounds()
        return {
            'type': 'ir.actions.act_window',
            'name': "Today's Assigned SLA Services",
            'res_model': 'aaa.service',
            'view_mode': 'tree',
            'view_id': self.env.ref('customer.view_aaa_service_tree').id,
            'domain': [
                ('is_afl_application', '=', True),
                ('service_time', '>=', start_utc_str),
                ('service_time', '<=', end_utc_str),
            ],
            'context': {
                'create': False,
                'edit': False
            }
        }