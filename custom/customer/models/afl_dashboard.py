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
        Service = self.env['aaa.service']  # Reference to the 'aaa.service' model
        # Define the additional filter for 'customer_id'
        start_utc_str, end_utc_str = self.today_utc_bounds()
        print(f"Start of day {start_utc_str}")
        print(f"End of day {end_utc_str}")
        # customer_filter = [('customer_id', '=', 'AL FUTTAIM LOGISTICS AUTOMOTIVE COMPANY L.L.C'), ('service_time', '>=', start_utc_str), ('service_time', '<=', end_utc_str)]
        customer_filter = [('is_whatsapp_service', '=', True), ('service_time', '>=', start_utc_str), ('service_time', '<=', end_utc_str)]
        self.today_whatsapp_count = Service.search_count(customer_filter)
        self.whatsapp_done_count = Service.search_count(customer_filter + [('state', '=', 'done')])
        self.whatsapp_cancel_count = Service.search_count(customer_filter + [('state', 'in',['cancel','done_cancel'] )])

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