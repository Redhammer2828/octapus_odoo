from odoo import api, fields, models, _
from odoo.exceptions import ValidationError , UserError
import datetime
from datetime import timedelta,datetime
import requests
import json
import re
from dotenv import load_dotenv
import os
import logging
from pytz import timezone
import pytz
from dateutil.relativedelta import relativedelta
import pytz
from dateutil.relativedelta import relativedelta
import socket

import base64
import io
import zipfile
from odoo.http import request
from requests.auth import HTTPBasicAuth


load_dotenv()
_logger = logging.getLogger(__name__)
base_url = os.getenv("BASE_URL")
# J PUSH
# J PUSH
class AAAService(models.Model):
    _name = 'aaa.service'
    _description = 'AAA Service'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Number", readonly=True, default=lambda self:('New'))
    color = fields.Char(string="Color")
    type = fields.Selection([('cash', 'Cash'), ('non_cash', 'Non-Cash')], string="Service Type", readonly=True)
    member_type = fields.Selection([('adhoc', 'AD-HOC'), ('policy', 'POLICY'),('credit', 'CREDIT')], string="Member Type", readonly=True)
    card_type = fields.Char(string="Card Type", readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('initiate', 'Initiate'),
        ('dispatch', 'Dispatch'),
        ('start', 'Start'),
        ('reach', 'Reach'),
        ('completed_by_driver', 'Completed by driver'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ('driver_cancel', 'Driver Cancelled'),
        ('change', 'Change' ),
        ('approved','Approved'),
        ('requested','Requested'),
        ('done_cancel', 'Done Cancelled')
    ], string="Status", readonly=True, default='initiate', tracking=True)
    #MANY2ONE-------------------------------------------------------------------------------------------------------
    customer_id = fields.Many2one('res.partner', string="Customer", domain="[('is_company', '=', True) ]")
    credit_customer_co = fields.Char('Customer C/O')
    sequence_id = fields.Many2one('partner.category', string="Customer Category", domain="[('partner_id','=', customer_id),('member_type','=',member_type)]")
    member_id = fields.Many2one(
        'res.partner',
        string="Member",
        domain="[('is_company', '=', False),('member_type','=',member_type)] "
    )

    invoice_ref_date = fields.Date(string='Invoice Reference Date')
      # Fields to track if values came from res.partner
    is_member_from_partner = fields.Boolean(string='Member from Partner', default=False)
    is_customer_from_partner = fields.Boolean(string='Customer from Partner', default=False)
    is_sequence_from_partner = fields.Boolean(string='Sequence from Partner', default=False)

    membership_num = fields.Char('Membership Number')
    created_by = fields.Many2one(
        'res.users',
        string="User",
        default=lambda self: self.env.user,
        compute='_compute_created_by',
        store=False,
        readonly=False
    )

    vehicle_type = fields.Char('Vehicle Type')   #Chaged to char
    vehicle_model = fields.Char('Vehicle Model')  #Changed to char

    product_id = fields.Many2one('product.template', string="Service",domain=[('bundle_product', '=', False)])
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure")
    new_service_id = fields.Many2one('product.template', string="New Service")
    main_product_ids = fields.Many2many('product.template', string="Main Products")
    cancelled_service_id = fields.Many2one('aaa.service', string="Cancelled Service", readonly=True)
    acc_payment_id = fields.Many2one('account.payment', string="Payment")

    # PROVIDER-------------------------------------------------------------------------------------------------------------
    provider_id = fields.Many2one('res.partner', string="Provider" ,domain=[('is_vendor', '=', True)])
    provider_contact = fields.Char(string="Provider Contact")
    provider_num = fields.Char('Provider Num')
    provider_rate = fields.Float(string="Provider Rate")
    provider_rate_invisible = fields.Float(string="Provider Rate Invisible")
    avg_vendor_rating = fields.Float(string="Average Vendor Rating")
    company_vehicle = fields.Boolean(string="Company Vehicle")
    avg_rating= fields.Selection([
        ('0',"0"),
        ('1',"1"),
        ('2',"2"),
        ('3',"3"),
        ('4',"4"),
        ('5', "5")
    ], string='Average Rating')
    route_rate = fields.Float(string="Route Rate")
    driver_name = fields.Char(string="Driver Name")
    driver_num = fields.Char(string="Driver Number")
    # ============================================================================================================================

    # SUMMARY---------------------------------------------------------------------------------------------------------------------
    credit_proforma_number = fields.Char(string="Trip Sheet Number")
    vendor_rating= fields.Selection([
        ('0',"0"),
        ('1',"1"),
        ('2',"2"),
        ('3',"3"),
        ('4',"4"),
        ('5', "5")
    ], string='Rate this service')
    rating_user_id = fields.Many2one('res.users', string="Rating Added By")
    # ============================================================================================================================

    member_contact_no = fields.Char(string="Mobile Number")
    email = fields.Char(string="Email")
    claim_membership = fields.Boolean(string="Claim Membership")
    deposit_amount = fields.Float(string="Deposit Amount")
    schedule_service_check = fields.Boolean(string="Schedule Service Check")
    cancel_service_check = fields.Boolean(string="Cancel Service Check")
    schedule_date_time = fields.Datetime(string="Schedule Date Time")
    # requested_date = fields.Datetime(string="Action Date Time")
    requested_date = fields.Datetime(string="Action Date Time", index=True)
    next_check_time = fields.Datetime(string='Next Check Time', compute='_compute_next_check_time', store=True, index=True)
    driving_license = fields.Char(string="Driving License")
    claim_number = fields.Char(string="Claim Number")
    smarto = fields.Boolean(string="Smarto")
    smarto_id = fields.Char(string="Smarto ID")
    comments = fields.Text(string="Comments")
    import_comments = fields.Text('import_comments')
    vehicle_type_ok = fields.Boolean(string="Vehicle Type OK")
    vehicle_model_ok = fields.Boolean(string="Vehicle Model OK")
    vehicle = fields.Char('vehicle')
    vehicle_type = fields.Char(string="Vehicle Type")

    vehicle_model = fields.Char(string="Vehicle Model")

    vehicle_plate = fields.Char(string="Vehicle Plate")
    vehicle_chasis_no = fields.Char(string="Vehicle Chasis No")
    policy_no = fields.Char(string="Policy No")


    product_type = fields.Selection([
        ('distance', 'Distance'),
        ('location', 'Location'),
        ('location_duration', 'Location Duration'),
        ('duration', 'Duration')
    ], string="Product Type")

    date_time_from = fields.Datetime(string= "From Date time")
    date_time_to = fields.Datetime(string="To Date time")
    quantity = fields.Float(string="Quantity", compute="_compute_quantity", store=True)
    quantity_with_days = fields.Char(string='Quantity with Days', compute="_compute_quantity", store=True)
    service_based = fields.Selection(related='product_id.service_based', store=True, readonly=True)

    old_membership_number = fields.Char('Old Membership Number')


    cash_collected_hidden = fields.Boolean(string="Cash Collected Hidden")
    cash_collected = fields.Float(string="Cash Collected")
    

    addon_ok = fields.Boolean(string="Addon OK")
    waive_off = fields.Boolean(string="Waive Off")

    # One to Many -------------------------------------------------------------------------------------------
    comment_history_ids = fields.One2many('service.comment', 'service_id', string="Comment History")
    service_history_ids = fields.One2many('service.history', 'service_id', string="Service History")
    # user_from_history = fields.Many2one(
    #     'res.users',
    #     string="Agent (From History)",
    #     compute='_compute_user_from_history',
    #     store=True
    # )
    dispatcher_from_history = fields.Many2one(
        'res.users',
        string="Dispatcher",
        compute='_compute_dispatcher_from_history',
        store=True
    )
    enquiry_ids = fields.One2many('aaa.enquiry', 'service_id', string="Enquiries")
    addon_service_ids = fields.One2many(
        'aaa.service.addon',
        'service_id',
        string='Additional Services'
    )
    # =========================================================================================================
    driver_id = fields.Many2one(
        'hr.employee',
        string="Driver",
        domain="[('job_id.name', '=', 'Driver')]"
    )

    is_driver_name_visible = fields.Boolean(string='Display Driver Name',default=True)
    enquiry_ids = fields.One2many('aaa.enquiry','enq_id',string="Enquiries") # IN aaa.service

    completion_time = fields.Datetime(string="Completion Time")
    member_activate_date = fields.Date('Member Activate Date')
    member_expiry_date = fields.Date('Member Expiry Date')

    #For disptacher code in AAA.service
    dispatcher_from_history = fields.Many2one(
        'res.users',
        string="Dispatcher",
        compute='_compute_dispatcher_from_history',
        store=True
    )
# --------JAFZA SERVICE-----------------------------
    is_jafza_service = fields.Boolean(string='Is Jafza Service', default=False)
    is_aditional_duty = fields.Boolean(string='Is Additional Duty', default=False)
    jafza_provider_id = fields.Many2one('res.partner', string="Jafza Provider" ,domain=[('is_vendor', '=', True)])
    jafza_driver_id = fields.Many2one(
        'hr.employee',
        string="Driver",
        domain="[('job_id.name', '=', 'Driver')]"
    )
    jafza_driver_name = fields.Char(string="Driver Name")

    # # -----------LOCATION- API TESTINGs--------------------------------------------------

    search_query = fields.Char(string='Search Locations')
    search_results = fields.Many2many('location.suggestion', string='Search Results', compute='_fetch_location_suggestions')
    selected_from_location = fields.Many2one('location.suggestion', string='From Location', compute='compute_location_suggestion_from', store=True)
    selected_to_location = fields.Many2one('location.suggestion', string='To Location', compute='compute_location_suggestion_to', store=True)
    from_location = fields.Many2one('aaa.location', string='From Location') #For Data IMPORT as well as CREDIT SERVICE PRICE LIST
    to_location = fields.Many2one('aaa.location', string='To Location') #For Data IMPORT as well as CREDIT SERVICE PRICE LIST
    is_imported = fields.Boolean('Is Imported', default=False)
    amount = fields.Integer(string='Amount', compute='_compute_amount', store=True)  # Dynamically computed amount
    credit_cash = fields.Integer(string="Credit cash")

    from_location_emirate = fields.Char(string='Emirate')
    to_location_emirate = fields.Char(string='Emirate')
    # quantity_with_days = fields.Char(string='Quantity with Days')
    orgin_no = fields.Text('Orgin')
    origin_no = fields.Many2one('aaa.service', string='Origin Service', help='References the original service before changes were made.', readonly=True)

    service_quantity = fields.Float(string="Service Quantity", default="1.00")
    hide_selected_locations = fields.Boolean(
        compute="_compute_hide_selected_locations",
        store=True
    )
    is_today = fields.Boolean(
        string="Is Today",
        compute="_compute_is_today",
        store=True
    )
    # BOOLEAN CHECKS FOR ROLE BASED VISIBILTY 
    is_logged_in_user_agent = fields.Boolean(compute='_compute_is_logged_in_user_agent', store=False)
    is_agent_user = fields.Boolean(string="Is Agent User", compute='_compute_is_agent_user', store=False)
    is_dispatch_user = fields.Boolean(string="Is Dispatcher User", compute='_compute_is_dispatch_user', store=False)
    is_manager_or_admin = fields.Boolean(compute='_compute_is_manager_or_admin', string="Is Manager or Admin", store=False)
    #is_dispatcher_or_manager_or_admin = fields.Boolean(compute='_compute_is_dispatcher_or_manager_or_admin', string="Is Dispatcher or Manager or Admin", store=False)
    is_dispatcher_or_manager_or_lead_or_admin = fields.Boolean(compute='_compute_is_dispatcher_or_manager_or_lead_or_admin', string="Is Dispatcher or Manager or Admin", store=False)
    service_time = fields.Datetime(string="Service Date Time", default=fields.Datetime.now)
    is_today = fields.Boolean(
        string='Is Today',
        compute='_compute_is_today',
        search='_search_today'
    )
    driver_pickup = fields.Char('Driver Pickup Location')
    driver_dropoff = fields.Char('Driver Dropoff Location')

    ##########    FIELDS #############################
    job_ref= fields .Char(string= "JobRefNo")
    ser_id = fields.Char(string="SerId")
    comment_text = fields.Text(compute='_compute_comment_text', string="Comments")
    initate_date =fields.Datetime(string="InitDt") 
    driver_reach_date = fields.Datetime(string="DrivReachDt")
    current_time = fields.Datetime(string='Current Time', compute='_compute_current_time')
    time_difference = fields.Float(string='Time Difference (minutes)', compute='_compute_time_difference', store=False)
    is_afl_application = fields.Boolean('Is AFL Application')
        
    show_new_change_button = fields.Boolean(
        compute="_compute_show_new_change_button",
        store=False
    )

    original_values = fields.Text(string='Original Values', readonly=True, 
                                 help="Temporary storage of original values for change tracking")
    dispatch_done_by = fields.Many2one('res.users', string="Dispatch Completed By")
    reach_done_by = fields.Many2one('res.users', string="Reach Completed By")
    done_done_by = fields.Many2one('res.users', string="Done Completed By")

    def _target_model_on_change(self):
        return ["afl.dashboard", "aaa.service"]
 
    @api.depends('state', 'product_id', 'location_from_external', 'location_to_external', 'from_location', 'to_location')
    def _compute_show_new_change_button(self):
        for record in self:
            # Check if any of the fields have changed by comparing with the previous values
            has_changed = any(
                record._origin[field] != record[field]
                for field in ['product_id', 'location_from_external', 'location_to_external', 'from_location', 'to_location']
            )
            # Make the button visible if state is 'change' AND any tracked field has changed
            record.show_new_change_button = record.state == 'change' and has_changed

# ----------API FOR DRIBER CANCEL ------------------------------------------------------------
    def action_approve_cancel_service(self):
        order_number = self.name
        # base_url = "https://gioapi-gy-dev.kirkos.ae"  # Ensure this is correct
        _logger.info("SERVICE NUMBER: %s", order_number)
        api_url = f"{base_url}/carhire-order/order/service/consumers/orders/cancel/order"
        # Define query parameters
        params = {
            "status": "APPROVED",
            "serviceNumber": order_number
        }
        try:
            # Send request with query parameters
            requests.put(api_url, params=params, timeout=10)
        except requests.exceptions.RequestException as e:
            _logger.error("API Request Failed: %s", str(e))
            raise UserError(f"API request failed: {str(e)}")
        # Change state after API call
        self.env['service.history'].create({
                'service_id': self.id,  # Assuming service_id is a Many2one field
                'user': self.env.user.id,
                'time': fields.Datetime.now(),
                'status': 'Driver Cancel Request Approved',
                'timeline_status': self.state,
        })
        self.state = 'cancel'

    @api.depends('service_time')
    def _compute_current_time(self):
        for record in self:
            # Getting current time in UTC
            record.current_time = fields.Datetime.now()

    @api.depends('current_time', 'service_time')
    def _compute_time_difference(self):
        for record in self:
            if record.service_time and record.current_time:
                delta = record.current_time - record.service_time
                # Convert time difference to minutes
                record.time_difference = delta.total_seconds() / 60
            else:
                record.time_difference = 0

    vehicle_type_id = fields.Many2one('member.vehicle.type', string='Vehicle type')
    vehicle_model_id = fields.Many2one('member.vehicle.model', string='Vehicle model', domain="[('type_id','=',vehicle_type_id)]")

    # -----------------------------------------------VEHICEL TYPE VEHICLE MODEL CODE -------------------
    @api.onchange('vehicle_type_id')
    def _onchange_vehicle_type_id(self):
        """ Updates the char field vehicle_type whenever vehicle_type_id is selected. """
        if self.vehicle_type_id:
            self.vehicle_type = self.vehicle_type_id.name
        else:
            self.vehicle_type = False  # Clear field if no selection

    @api.onchange('vehicle_model_id')
    def _onchange_vehicle_model_id(self):
        """ Updates the char field vehicle_model whenever vehicle_model_id is selected. """
        if self.vehicle_model_id:
            self.vehicle_model = self.vehicle_model_id.name
        else:
            self.vehicle_model = False  # Clear field if no selection

    @api.depends('state')
    def _compute_comment_text(self):
        for record in self:
            comments = self.env['service.comment'].search([('comment_status', '=', record.state)])
            record.comment_text = "\n".join(comments.mapped('comment'))  # Assuming 'content' is the field with comment text
# -----------------------------------------------------------------------------------------------------------------
    @api.model
    def _get_timezone_start_end_times(self):
        """Get UTC start/end times based on user timezone"""
        # Get user's timezone or default to UTC
        user_tz = pytz.timezone(self.env.user.tz or 'UTC')
        utc_tz = pytz.UTC

        # Get current date in user's timezone
        now = datetime.now()
        user_today = now.astimezone(user_tz).date()

        # Create datetime objects for start and end of user's day
        local_start = datetime.combine(user_today, datetime.min.time())
        local_end = datetime.combine(user_today, datetime.max.time())

        # Convert to UTC
        utc_start = user_tz.localize(local_start).astimezone(utc_tz)
        utc_end = user_tz.localize(local_end).astimezone(utc_tz)

        return utc_start, utc_end

    def _search_today(self, operator, value):
        """Dynamic domain for today's records based on user timezone"""
        if operator == '=' and value:
            utc_start, utc_end = self._get_timezone_start_end_times()
            return [
                ('service_time', '>=', utc_start.strftime('%Y-%m-%d %H:%M:%S')),
                ('service_time', '<=', utc_end.strftime('%Y-%m-%d %H:%M:%S'))
            ]
        return []

    @api.depends('service_time')
    def _compute_is_today(self):
        """Compute method for is_today field"""
        utc_start, utc_end = self._get_timezone_start_end_times()
        for record in self:
            if record.service_time:
                record.is_today = utc_start <= record.service_time <= utc_end
            else:
                record.is_today = False
# ----------------------------DELETE RESTRICTION-------------------------------------------------------------------
    def unlink(self):
        """Restrict deletion for users in groups named 'Agent' or 'Dispatcher'."""
        current_user = self.env.user  # Get the currently logged-in user
        user_groups = current_user.groups_id  # Get all groups of the current user
        restricted_groups = ['Agent', 'Dispatcher']

        if any(group.name in restricted_groups for group in user_groups):
            raise UserError(
                "You cannot delete this record"
            )
        return super(AAAService, self).unlink()

    @api.depends('created_by')
    def _compute_is_agent_user(self):
        """Compute is_agent_user based on the created_by user's group membership."""
        for record in self:
            # Default to False if no `created_by` is set
            record.is_agent_user = False
            if record.created_by:
                # Check if `created_by` belongs to the 'new_agents' group
                user_groups = record.created_by.groups_id
                record.is_agent_user = any(group.name == 'Agent' for group in user_groups)
        
    # ----------------------------Identifying Agent-------------------------------------------------------------------
    def _compute_is_logged_in_user_agent(self):
        agent_group = self.env['res.groups'].search([('name', '=', 'Agent')], limit=1)
        is_agent = agent_group and agent_group in self.env.user.groups_id
        for record in self:
            record.is_logged_in_user_agent = is_agent

    @api.depends('created_by')
    def _compute_is_dispatch_user(self):
        """Compute is_dispatch_user based on the created_by user's group membership."""
        for record in self:
            # Default to False if no `created_by` is set
            record.is_dispatch_user = False
            if record.created_by:
                # Check if `created_by` belongs to the 'new_agents' group
                user_groups = record.created_by.groups_id
                record.is_dispatch_user = any(group.name == 'Dispatcher' for group in user_groups)

    @api.depends()  # Remove created_by dependency since we want current user
    def _compute_is_manager_or_admin(self):
        """Compute is_manager_or_admin based on the current user's group membership."""
        for record in self:
            # Get the current user's groups
            user_groups = self.env.user.groups_id

            # Check if the user belongs to the 'Manager' group
            is_manager = any(group.name == 'Manager' for group in user_groups)

            # Check if the user is an Admin
            is_admin = any(group.name == 'IT Group' for group in user_groups)

            # Set the field to True if the user is either a Manager or an Admin
            record.is_manager_or_admin = is_manager or is_admin

    @api.depends()  # Remove created_by dependency since we want current user
    def _compute_is_dispatcher_or_manager_or_lead_or_admin(self):
        """Compute is_dispatcher_or_manager_or_admin based on the current user's group membership."""
        for record in self:
            # Get the current user's groups
            user_groups = self.env.user.groups_id
            is_dispatcher = any(group.name == 'Dispatcher' for group in user_groups)
            # Check if the user belongs to the 'Manager' group
            is_manager = any(group.name == 'Manager' for group in user_groups)
            #check if the user belongs to the 'team lead' group
            is_lead = any(group.name == 'team lead' for group in user_groups)

            # Check if the user is an Admin
            is_admin = any(group.name == 'IT Group' for group in user_groups)

            # Set the field to True if the user is either a Manager or an Admin
            record.is_dispatcher_or_manager_or_lead_or_admin = is_dispatcher or is_manager or is_lead or is_admin 

    #computing the dispatcher in AAA.SERVICE
    @api.depends('state', 'service_history_ids.user')
    def _compute_dispatcher_from_history(self):
        """Fetch the exact user from the related service.history."""
        for service in self:
            # Find the first related service.history record with a matching state
            relevant_history = service.service_history_ids.filtered(
                lambda history: history.status == 'dispatch'
            )
            # Get the `user` from the first relevant service.history record, if any
            service.dispatcher_from_history = relevant_history[:1].user if relevant_history else False
            print("DISPATCHER",relevant_history)

    # FOR TREE VIEW
    @api.depends('member_type')
    def _compute_hide_selected_locations(self):
        for record in self:
            record.hide_selected_locations = record.member_type == 'credit'

# --------------------------------------------API SEARCH LOCATION-------------------------------------------------------------------
    @api.depends('search_query')
    def _fetch_location_suggestions(self):
        for record in self:
            record.search_results = [(5, 0, 0)]  # Clear existing results
            if record.search_query:
                try:
                    url = "https://nominatim.kirkos.ae/search.php"
                    params = {
                        'q': record.search_query,
                        'format': 'geocodejson',
                        'addressdetails': 1,
                    }
                    headers = {
                        'Accept-Language': 'en'
                    }
                    response = requests.post(url, params=params, headers=headers)
                    response.raise_for_status()

                    if response.status_code == 200:
                        data = response.json()
                        if 'features' in data:
                            Suggestion = self.env['location.suggestion']
                            for feature in data['features']:
                                label = feature['properties']['geocoding']['label']
                                coordinates = feature['geometry']['coordinates']
                                suggestion = Suggestion.create({
                                    'name': label,
                                    'feature_data': str(feature),
                                    'longitude': coordinates[0],
                                    'latitude': coordinates[1]  # Store full feature data for later use if needed
                                })
                                record.search_results = [(4, suggestion.id)]
                        else:
                            # Create a "No results" suggestion
                            no_result = Suggestion.create({'name': 'No results found'})
                            record.search_results = [(4, no_result.id)]
                    else:
                        error_msg = Suggestion.create({'name': f'API error: {response.status_code}'})
                        record.search_results = [(4, error_msg.id)]
                except Exception as e:
                    error_msg = Suggestion.create({'name': f'Error fetching location: {str(e)}'})
                    record.search_results = [(4, error_msg.id)]

    @api.onchange('selected_from_location', 'selected_to_location')
    def _onchange_selected_locations(self):
        # Clear the search_query and search_results when a location is selected
        if self.selected_from_location:
            self.search_query = ''
            self.search_results = [(5, 0, 0)]  # Clear existing results
        if self.selected_to_location:
            self.search_query = ''
            self.search_results = [(5, 0, 0)]  # Clear existing results
        # Trigger computation of the amount when locations are selected
        self._compute_amount()

    @api.depends('date_time_from', 'date_time_to', 'member_type')
    def _compute_quantity(self):
        for record in self:
            if record.date_time_from and record.date_time_to:
                delta = record.date_time_to - record.date_time_from
                total_hours = delta.total_seconds() / 3600  # Convert seconds to hours
                days = int(total_hours // 24)  # Full days
                if total_hours % 24 > 1:  # Count extra hour into the next day if exceeds 25 hours
                    days += 1
                record.quantity = days
                record.quantity_with_days = f"{days} Day{'s' if days != 1 else ''}"
            else:
                record.quantity = 0
                record.quantity_with_days = "0 Days"

    @api.onchange('date_time_from', 'date_time_to')
    def _onchange_from_to_date(self):
        for record in self:
            if record.member_type in ['credit', 'adhoc']:
                if record.date_time_from and record.date_time_to:
                    delta = record.date_time_to - record.date_time_from
                    total_hours = delta.total_seconds() / 3600  # Convert seconds to hours
                    days = int(total_hours // 24)  # Full days
                    if total_hours % 24 > 1:  # Count extra hour into the next day if exceeds 25 hours
                        days += 1
                    record.quantity = days
                    record.quantity_with_days = f"{days} Day{'s' if days != 1 else ''}"
                else:
                    record.quantity = 0
                    record.quantity_with_days = "0 Days"
# --------ALREADY EXISTED WRITE Till 17/04/2025----------------
    # def write(self, vals):
    #     res = super(AAAService, self).write(vals)
    #     for record in self:
    #         if record.member_type in ['credit', 'adhoc'] and 'date_time_to' in vals:
    #             if record.date_time_from and record.date_time_to:
    #                 delta = record.date_time_to - record.date_time_from
    #                 total_hours = delta.total_seconds() / 3600  # Convert seconds to hours
    #                 days = int(total_hours // 24)  # Full days
    #                 if total_hours % 24 > 1:  # Count extra hour into the next day if exceeds 25 hours
    #                     days += 1
    #                 record.quantity = days
    #                 record.quantity_with_days = f"{days} Day{'s' if days != 1 else ''}"
    #             else:
    #                 record.quantity = 0
    #                 record.quantity_with_days = "0 Days"
    #     return res
# -----------------------------------------------------------------------------------------------------------
# ---------------API Added Write function---------------------------------------------------------------------
    def write(self, vals):
        _logger.info("=== WRITE METHOD ENTERED ===")
        _logger.info("Input values: %s", vals)
        _logger.info("Records being updated: %s", [(r.id, r.name) for r in self])

        # Capture old chassis numbers
        old_chassis_map = {}
        afl_old_info_map = {}
        alf_old_driver_info_map = {}

        for record in self:
            if record.is_afl_application:
                afl_old_info_map[record.id] = {
                    'vehicle_chasis_no': record.vehicle_chasis_no,
                    'vehicle_plate': record.vehicle_plate,
                    'vehicle_model_name': record.vehicle_model_id.name,
                    'phone_number': record.member_contact_no,
                    'customer_email': record.email,
                    'policy_number': record.policy_no,
                    'provider_name': record.provider_id.name,
                    # 'service_name': record.product_id.name,
                    # 'service_based': record.service_based,
                    # 'to_location_name': record.to_location.name,
                    # 'to_latitude': record.to_location.latitude,
                    # 'to_longitude': record.to_location.longitude,
                }
                alf_old_driver_info_map[record.id] = {
                    'driver_name': record.driver_id.name,
                    'driver_phone': record.driver_num,
                }
            else:
                old_chassis_map[record.id] = record.vehicle_chasis_no


        # Track relationship field changes
        if 'member_id' in vals:
            vals['is_member_from_partner'] = bool(vals['member_id'])
        if 'customer_id' in vals:
            vals['is_customer_from_partner'] = bool(vals['customer_id'])
        if 'sequence_id' in vals:
            vals['is_sequence_from_partner'] = bool(vals['sequence_id'])

        # Set created_by if in dispatch state and not explicitly set
        if self.state == 'dispatch' and not vals.get('created_by'):
            vals['created_by'] = self.env.user.id

        # Handle comment logic
        if 'comments' in vals and vals['comments']:
            existing_comments = self.comments or ""
            new_comment = f"{existing_comments}\n{vals['comments']}" if existing_comments else vals['comments']

            # Update comment field for display
            vals['comments'] = new_comment

            # Create new comment record
            self.env['service.comment'].create({
                'service_id': self.id,
                'comment': vals['comments'],
                'comment_date_and_time': fields.Datetime.now(),
                'comment_user': self.env.user.id,
                'comment_status': self.state,
            })

            # Clear input field (optional, depending on your UX)
            vals['comments'] = ''

        # Perform the write
        try:
            res = super(AAAService, self).write(vals)
            _logger.info("Super write completed.")
        except Exception as e:
            _logger.exception("Write failed.")
            raise

        # Post-write logic
        for record in self:
            # Recalculate quantity
            if record.member_type in ['credit', 'adhoc'] and 'date_time_to' in vals:
                if record.date_time_from and record.date_time_to:
                    delta = record.date_time_to - record.date_time_from
                    total_hours = delta.total_seconds() / 3600
                    days = int(total_hours // 24)
                    if total_hours % 24 > 1:
                        days += 1
                    record.quantity = days
                    record.quantity_with_days = f"{days} Day{'s' if days != 1 else ''}"
                else:
                    record.quantity = 0
                    record.quantity_with_days = "0 Days"

            # Check if chassis number changed
            if record.is_afl_application == False:
                old_chassis = old_chassis_map.get(record.id)
                if old_chassis != record.vehicle_chasis_no:
                    _logger.info("Chassis changed from %s to %s", old_chassis, record.vehicle_chasis_no)
                    record._trigger_chassis_update_api()

            if record.is_afl_application == True:
                old_info = afl_old_info_map.get(record.id, {})
                old_driver_info = alf_old_driver_info_map.get(record.id, {})
                new_info = {
                    'vehicle_chasis_no': record.vehicle_chasis_no,
                    'vehicle_plate': record.vehicle_plate,
                    'vehicle_model_name': record.vehicle_model_id.name,
                    'phone_number': record.member_contact_no,
                    'customer_email': record.email,
                    'policy_number': record.policy_no,
                    'provider_name': record.provider_id.name,
                    # 'service_name': record.product_id.name,
                    # 'service_based': record.service_based,
                    # 'to_location_name': record.to_location.name,
                    # 'to_latitude': record.to_location.latitude,
                    # 'to_longitude': record.to_location.longitude,
                }
                new_driver_info = {
                    'driver_name': record.driver_id.name,
                    'driver_phone': record.driver_num,
                }

                info_changed = any(old_info.get(key) != new_info[key] for key in new_info)
                driver_info_changed = any(old_driver_info.get(key) != new_driver_info[key] for key in new_driver_info)

                if info_changed or driver_info_changed:
                    _logger.info("Info changed for target customer %s. Triggering API.", record.id)
                    if driver_info_changed:
                        record._trigger_afl_info_update_api(driver_info_changed=True)
                    else:
                        record._trigger_afl_info_update_api()

        _logger.info("=== WRITE METHOD COMPLETED ===")
        return res
# -------------------------------------------------------------------------------------------------------------

    def _trigger_afl_info_update_api(self, driver_info_changed=False):
        for record in self:
            base_url = os.getenv('BASE_URL')
            if not record.name or not record.vehicle_chasis_no:
                _logger.warning("Skipping API call: Missing service number or chassis number for record ID %s", record.id)
                continue

            base_url = f"{base_url}/carhire-order/order/service/afl-order/update/order-details"
            params = {
                'erp_order_number': record.name,
                'chassis_number': record.vehicle_chasis_no,
                "plate_number": record.vehicle_plate,
                "vehicle_model" : record.vehicle_model_id.name,
                "phone_number": record.member_contact_no,
                "customer_email": record.email,
                "policy_number": record.policy_no,
                "provider_name": record.provider_id.name,
                "driver_name": record.driver_id.name if driver_info_changed else None,
                "driver_phone": record.driver_num if driver_info_changed else None,
                "service_name": None,
                "service_based": None,
                "location_to": None,
            }
            headers = {'Content-Type': 'application/json'}

            _logger.info("Sending PUT API Request", params)
            try:
                response = requests.put(base_url, json=params, headers=headers)

                _logger.info("API Response: %s - %s", response.status_code, response.text)

                if response.status_code == 200:
                    _logger.info("AFL info updated via external API.")
                else:
                    _logger.warning("API call returned non-200 status. Status: %s, Response: %s",
                                    response.status_code, response.text)

            except requests.exceptions.RequestException:
                _logger.exception("API request failed for record ID %s", record.id)


    def _trigger_chassis_update_api(self):
        for record in self:
            base_url = os.getenv('BASE_URL')
            if not record.name or not record.vehicle_chasis_no:
                _logger.warning("Skipping API call: Missing service number or chassis number for record ID %s", record.id)
                continue

            base_url = f"{base_url}/carhire-order/order/service/consumers/orders/update/chassis-number"
            params = {
                'chassisNumber': record.vehicle_chasis_no,
                'serviceNumber': record.name,
            }

            full_url = f"{base_url}?chassisNumber={params['chassisNumber']}&serviceNumber={params['serviceNumber']}"
            _logger.info("Sending PUT to %s", full_url)

            try:
                response = requests.put(full_url)

                _logger.info("API Response: %s - %s", response.status_code, response.text)

                if response.status_code == 200:
                    _logger.info("Chassis number updated via external API.")
                else:
                    _logger.warning("API call returned non-200 status. Status: %s, Response: %s",
                                    response.status_code, response.text)

            except requests.exceptions.RequestException:
                _logger.exception("API request failed for record ID %s", record.id)


# ----------------------------------------------------------------------------------------------------------

    @api.depends('selected_from_location', 'selected_to_location')
    def _compute_amount(self):
        pass

    # @api.depends('selected_from_location', 'selected_to_location')
    # def _compute_emirates(self):
    #     for record in self:
    #         if record.selected_from_location:
    #             record.from_location_emirate = self._extract_emirate_from_feature_data(record.selected_from_location.feature_data)
    #         else:
    #             record.from_location_emirate = ''

    #         if record.selected_to_location:
    #             record.to_location_emirate = self._extract_emirate_from_feature_data(record.selected_to_location.feature_data)
    #         else:
    #             record.to_location_emirate = ''

    def _extract_emirate_from_feature_data(self, feature_data):
        """
        Extracts the emirate from the feature data JSON string and appends 'Emirate' with bold tags.
        """
        known_emirates = ['Abu Dhabi', 'Ajman', 'Dubai', 'Fujairah', 'Ras Al Khaimah', 'Sharjah', 'Umm Al-Quwain']

        if feature_data:
            try:
                feature_data = feature_data.replace("'", '"')  # Ensure JSON is valid
                feature = json.loads(feature_data)  # Parse the JSON

                geocoding = feature.get('properties', {}).get('geocoding', {})
                label = geocoding.get('label', '').lower()  # Convert label to lowercase

                # Remove "emirate" from the label if present
                label = label.replace('emirate', '').strip()

                parts = [part.strip() for part in label.split(',')]  # Clean label

                for emirate in known_emirates:
                    # Case-insensitive match, ignoring the "Emirate" postfix
                    if emirate.lower() in [part.lower() for part in parts]:
                        # Return the emirate with 'Emirate' and wrapped in bold tags
                        return f"{emirate} Emirate"

                return 'Unknown Emirate'  # Default if no emirate is found
            except Exception as e:
                print(f"Debug - Exception: {e}")
                return 'Unknown Emirate'
        return ''

# -------------------------------------------------------------------------
    @api.onchange('provider_id','jafza_provider_id')
    def _onchange_provider_id(self):
            """
            Dynamically show/hide driver_name or driver_id based on the provider's name.
            If provider's name is 'Arabian Automobile Association', hide driver_name and show driver_id.
            Otherwise, show driver_name and hide driver_id.
            """
            if self.provider_id and self.provider_id.name.strip().lower() == 'arabian automobile association':
                self.is_driver_name_visible = False  # Hide driver_name and show driver_id
            else:
                self.is_driver_name_visible = True  # Show driver_name and hide driver_id
#--------------------------------------------------BACKUP CODE OF ON CATEGORY FETCHING-----------------------------

    @api.onchange('customer_id', 'member_type')
    def _onchange_customer_id_member_type(self):
        for record in self:
            if not record.customer_id:
                record.member_id = False
                record.sequence_id = False
                continue

            if record.member_type == 'credit':
                partner_categories = self.env['partner.category'].search([
                    ('partner_id', '=', record.customer_id.id),
                    ('member_type', '=', 'credit'),
                ], order='id')  # Order by ID or another field as required

                if partner_categories:
                    record.sequence_id = partner_categories[0].id
                    # Fetch member linked to the fetched sequence_id
                    member = self.env['res.partner'].search([
                        ('member_partner_category_id', '=', partner_categories[0].id),
                        ('member_type', '=', 'credit'),
                    ], order='id', limit=1)  # Limit to 1 member, ordered by ID

                    record.member_id = member.id if member else False
                else:
                    record.sequence_id = False
                    record.member_id = False

            elif record.member_type == 'adhoc':
                # Fetch 'adhoc' member categories ordered by ID
                partner_categories = self.env['partner.category'].search([
                    ('partner_id', '=', record.customer_id.id),
                    ('member_type', '=', 'adhoc'),
                ], order='id')  # Order by ID or another field as required

                if partner_categories:
                    record.sequence_id = partner_categories[0].id
                    # Fetch member linked to the fetched sequence_id
                    member = self.env['res.partner'].search([
                        ('member_partner_category_id', '=', partner_categories[0].id),
                        ('member_type', '=', 'adhoc'),
                    ], order='id', limit=1)  # Limit to 1 member, ordered by ID

                    record.member_id = member.id if member else False
                else:
                    record.sequence_id = False
                    record.member_id = False

    @api.onchange('sequence_id')
    def _onchange_sequence_id(self):
        for record in self:
            if not record.sequence_id:
                record.member_id = False
                continue

            if record.member_type == 'credit':
                member = self.env['res.partner'].search([
                    ('member_partner_category_id', '=', record.sequence_id.id),
                    ('member_type', '=', 'credit'),
                ], order='id', limit=1)  # Order can be specified as needed

                record.member_id = member.id if member else False

            elif record.member_type == 'adhoc':
                member = self.env['res.partner'].search([
                    ('member_partner_category_id', '=', record.sequence_id.id),
                    ('member_type', '=', 'adhoc'),
                ], order='id', limit=1)  # Order can be specified as needed

                record.member_id = member.id if member else False

    @api.model
    def create(self, vals):
        """Override create method to set the name field and dynamically update created_by field."""
        # Set the tracking fields for readonly behavior
        if vals.get('member_id'):
            vals['is_member_from_partner'] = True
        if vals.get('customer_id'):
            vals['is_customer_from_partner'] = True
        if vals.get('sequence_id'):
            vals['is_sequence_from_partner'] = True

        # Ensure the name field is set using a specific format if not provided
        if vals.get('name', _('New')) == _('New'):
            current_month = datetime.now().strftime('%m')  # 2-digit month
            current_year = datetime.now().strftime('%Y')   # 4-digit year

            # Get the next sequence number (without the prefix)
            sequence_number = self.env['ir.sequence'].next_by_code('aaa.service')

            # Extract only the numeric part of the sequence number
            numeric_part = ''.join(filter(str.isdigit, sequence_number))
            sequence_number = f"{int(numeric_part):08d}"  # Ensure it's zero-padded to 8 digits

            # Format the service name
            vals['name'] = f"SER/{current_month}/{current_year}/{sequence_number}"

        # Dynamically set the created_by field if not set already
        if not vals.get('created_by'):
            vals['created_by'] = self.env.user.id
        if self.state == 'change':
            raise UserError("You cannot modify this record while in 'Change' state.")
        # Create the aaa.service record
        service = super(AAAService, self).create(vals)

        # Create the service.history record
        self.env['service.history'].create({
            'service_id': service.id,
            'user': self.env.user.id,
            'time': fields.Datetime.now(),
            'status': 'Initiated',
            'timeline_status': 'initiate',
        })
        return service          

    @api.depends('state')
    def _compute_created_by(self):
        """Dynamically update created_by when the record is in specified states."""
        for record in self:
            if record.state in {'initiate','dispatch', 'start', 'reach', 'completed_by_driver_done'} and record.created_by != self.env.user:
                record.created_by = self.env.user

    @api.depends('state', 'service_history_ids.user')
    def _compute_dispatcher_from_history(self):
        """Fetch the exact user from the related service.history."""
        for service in self:
            # Find the first related service.history record with a matching state
            relevant_history = service.service_history_ids.filtered(
                lambda history: history.status == 'dispatch'
            )
            # Get the `user` from the first relevant service.history record, if any
            service.dispatcher_from_history = relevant_history[:1].user if relevant_history else False
            print("DISPATCHER",relevant_history)

    # def write(self, vals):
    #     """Override the write method to ensure comments are saved and created_by is updated."""
    #     # Update tracking fields if values are being changed
    #     if 'member_id' in vals:
    #         vals['is_member_from_partner'] = bool(vals['member_id'])
    #     if 'customer_id' in vals:
    #         vals['is_customer_from_partner'] = bool(vals['customer_id'])
    #     if 'sequence_id' in vals:
    #         vals['is_sequence_from_partner'] = bool(vals['sequence_id'])

    #     # If the record is in dispatch state, dynamically update created_by
    #     if self.state == 'dispatch' and not vals.get('created_by'):
    #         vals['created_by'] = self.env.user.id

    #     # Handle comment appending and record creation
    #     if 'comments' in vals and vals['comments']:
    #         existing_comments = self.comments or ""
    #         new_comment = f"{existing_comments}\n{vals['comments']}" if existing_comments else vals['comments']

    #         # Update the comments field in the service model
    #         vals['comments'] = new_comment

    #         # Create the service.comment record for each new comment
    #         self.env['service.comment'].create({
    #             'service_id': self.id,
    #             'comment': vals['comments'],
    #             'comment_date_and_time': fields.Datetime.now(),
    #             'comment_user': self.env.user.id,
    #             'comment_status': self.state,
    #         })

    #         # Clear the comments field after saving
    #         vals['comments'] = ''  # Clear the comment field

    #     # Call the super method to handle the actual update of the service
    #     return super(AAAService, self).write(vals)

    @api.onchange('state')
    def _onchange_state(self):
        """Dynamically update created_by when state changes to specific values."""
        if self.state in {'initiate','dispatch', 'start', 'reach', 'completed_by_driver_done'} and self.created_by != self.env.user:
            self.created_by = self.env.user

    def action_initiate_service(self):
        self.state = 'initiated'

    def action_order_response(self, order_number, status, phone_number, vehicle_chasis_no):
        url = f"{base_url}/aaa-customer/whatsapp/whatsapp-Notification"
        payload = json.dumps({
            "order_number": order_number,
            "status": status,
            "phone_number": phone_number,
            "vehicle_chasis_no": vehicle_chasis_no
        })

        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(url, headers=headers, data=payload)
            # Debug: Print raw response text
            print("Response Text:", response.text)
            if response.status_code == 200:
                try:
                    response_text = response.json()
                    _logger.info("Notification sent successfully: %s", response_text)
                    print("Response sent successfully")
                except json.JSONDecodeError:
                    # Handle non-JSON response here
                    _logger.info("Non-JSON response received: %s", response.text)
                    print("Non-JSON response received:", response.text)
            else:
                _logger.info("Failed to send notification, status code: %s, message: %s", response.status_code, response.text)
                print("Failed to send, status code:", response.status_code, "message:", response.text)

        except requests.exceptions.RequestException as e:
            _logger.info("Request failed: %s", str(e))
            print("Request failed:", str(e))

    def action_order_create(self, order_number):
        url = f"{base_url}/aaa-customer/consumers/create/road_side_service"
        print('service number on order create',order_number)
        payload = json.dumps({
            "erp_order_number": order_number,
            "is_jafza_service": self.is_jafza_service,
            "is_after_duty": self.is_aditional_duty
        })
        header = {
            'content-type':'application/json'
        }
        response = requests.post(url,data=payload,headers=header)
        if response.status_code == 200:
            print(f"API RESPONSE-ORDER CREATED,{response.text}")
        else:
            print(f"API RESPONSE-ORDER NOT CREATED,{response.text},{response.status_code}")

# ---------------------------------------------------NEW A CODE-----------------------------------------------
# -----------------------------CATEOGRY LIMIT CHECK----------------------------------------------------------------------------------------
    def action_dispatch_service(self):
        print('checking the service create dispatch')
        self.ensure_one()
        # self._generate_service_name()

        if not self.product_id:
            raise UserError(_("Provide the service details."))
         # Determine visible fields based on service_based and member_type
        if self.service_based in ['location', 'location_duration', 'none']:
            # `from_location` and `selected_from_location` are invisible
            from_location_visible = False
            to_location_visible = True
        else:
            # Both `from_location` and `selected_from_location` are visible
            from_location_visible = True
            to_location_visible = True

        # Adjust field visibility based on member_type
        if self.member_type in ['policy', 'adhoc']:
            # Use `selected_from_location` and `selected_to_location`
            from_location_field = self.location_from_external
            to_location_field = self.location_to_external
            print(self.location_from_external, self.location_to_external)
        elif self.member_type == 'credit':
            # Use `from_location` and `to_location`
            from_location_field = self.from_location
            to_location_field = self.to_location
        else:
            raise UserError(_("Invalid member type specified."))

        # Check visibility and raise appropriate errors
        if from_location_visible and not from_location_field:
            if to_location_visible and not to_location_field:
                raise UserError(_("Please provide both From Location and To Location details."))
            else:
                raise UserError(_("Please provide the From Location detail."))
        elif to_location_visible and not to_location_field:
            raise UserError(_("Please provide the To Location detail."))

        # Check for Credit
        if self.member_id.member_type in ['credit', 'adhoc']:
             # Calculate quantity and quantity_with_days without validation
            if self.date_time_from and self.date_time_to:
                delta = self.date_time_to - self.date_time_from
                self.quantity = delta.days
                self.quantity_with_days = f"{self.quantity} Days" if self.quantity else "0 Days"

            # Save the updated values to the database
            self.write({
                'quantity': self.quantity,
                'quantity_with_days': self.quantity_with_days,
            })
            # Directly dispatch service without any validation
            self._dispatch_service()
            return True
        if not self.member_id:
            raise ValidationError(_("Member not found in the service record."))

        member = self.member_id
        print("POLICY MEMBER = res_partner id =", member.id)
        product_template_id = member.product_template_id.id
        print("PACKAGE ID OF POLICY MEMBER = product.package.service", product_template_id)

        if not product_template_id:
            raise ValidationError(_("Package not found for the member."))

        if not self._is_service_in_package(product_template_id):
            print("SERVICE NOT IN PACKAGE - TRIGGERING CASH/CREDIT WIZARD")
            return self._trigger_cash_or_credit_service_wizard()

        if not self._validate_service_limits(product_template_id):
            print("SERVICE VALIDITY REACHED THE CATEGORY LIMITS - TRIGGERING CASH WIZARD")
            return self._trigger_cash_service_wizard()

        self._dispatch_service()
        # self._generate_service_name()

        

        return True

    def _generate_service_name(self):
        if not self.name:
            if not self.service_sequence:
                date_str = datetime.today().strftime('%Y%m%d')
                sequence = self.env['ir.sequence'].next_by_code('aaa.service')
                self.name = f'SERV-{date_str}-{sequence[-4:]}'
        self.schedule_date_time = fields.Datetime.now()
        # -----------API------------------------------------------------------------------------------------
        order_number = self.name
        status = self.state
        phone_number = self.member_contact_no
        vehicle_chasis_no = self.vehicle_chasis_no  # Corrected field name

        self.action_order_response(order_number, status, phone_number, vehicle_chasis_no)
        print('generating order number',order_number)
        self.action_order_create(order_number)
        print(f"checking value of order:{order_number},{status}, {phone_number}, {vehicle_chasis_no}")
        # -----------------------------------------------------------------------------------------------

    def _is_service_in_package(self, product_template_id):
        # Search for services within the package
        package_services = self.env['product.package.service'].search([
            ('product_template_id', '=', product_template_id)
        ])
        print("SERVICES IN THE PACKAGE", package_services)
        print("PRODUCT PACKAGE SERVICE - Service ids", package_services.product_id.ids)

        service_product_id = self.product_id.id  # The service the member is trying to avail
        print("SERVICE TAKEN BY THE MEMBER", service_product_id)

        # Search for matching products in product.product
        matching_products = self.env['product.product'].search([('id', 'in', package_services.product_id.ids)])
        print("MATCHING PRODUCTS", matching_products)

        # Get product_tmpl_id from the matching products
        matching_product_tmpl_ids = matching_products.mapped('product_tmpl_id.id')
        print("MATCHING PRODUCT TEMPLATE IDS", matching_product_tmpl_ids)

        # Check if the service product matches any of the product templates
        if service_product_id in matching_product_tmpl_ids:
            print("SERVICE MATCHES A PRODUCT IN THE PACKAGE")
            return True


    def _validate_service_limits(self, product_template_id):
        parent_category_id = self.product_id.categ_id.id
        print(f"PARENT CATEGORY OF CHOSEN SERVICE IN PACKAGE: {parent_category_id}")
        if not parent_category_id:
            return True
        category_limits = self.env['product.category.limit'].search([
            ('categ_id', '=', parent_category_id),
            ('category_id', '=', product_template_id)
        ])
        print(f"VAL_LIMITS OF PARENT_CAT: {category_limits}")
        if not category_limits:
            return True
        quantity_limit = 10  # Default value
        validity_period_days = 365  # Default value

        for limit in category_limits:
            quantity_limit = float(limit.quantity)
            print(f"NO OF SERVICE ACCESS IN CAT_DURATION: {quantity_limit}")
            # Fix: Correct handling of hours vs. days
            validity_period_days = (
                limit.hours if limit.uom_id.name == 'Days' else limit.hours )
            print(f"CAT_DURATION (validity in hours or days): {validity_period_days}")
        # Logic for 24-hour validation
            if validity_period_days == 24:
                if self.member_activate_date:
                    activate_date = self.member_activate_date
                else:
                 # Default to 395 days before the member_expiry_date if activate_date is null
                    activate_date = self.member_expiry_date - timedelta(days=395)
                # Fetch the last service in the same category
                # Fetch the last service in the same category within the valid date range
                last_service = self.env['aaa.service'].search([
                    ('member_id', '=', self.member_id.id),
                    ('product_id.categ_id', '=', parent_category_id),
                    ('service_time', '>=', activate_date),
                    ('service_time', '<=', self.member_expiry_date),
                    ('state', 'in', ['dispatch', 'start', 'reach', 'completed_by_driver', 'done']),
                ], order='service_time desc', limit=1)

                print(f"LAST SERVICEL:{last_service}")
                print("PRODUCT CATEGORY ID CHOOSES:",self.product_id.categ_id)
                print("MEMBER ACTIVATION DATE",self.member_id.member_expiry_date)
                if last_service and last_service.service_time:

                    time_since_last_service = fields.Datetime.now() - last_service.service_time
                    hours_since_last_service = time_since_last_service.total_seconds() / 3600
                    print(f"HOURS SINCE LAST SERVICE: {hours_since_last_service}")

                    # If less than 24 hours, calculate remaining quantity
                    if hours_since_last_service < 24:
                        remaining_quantity = quantity_limit - self._count_services_in_category(parent_category_id)
                        print(f"REMAINING SERVICE ACCESS IN THE CAT_DURATION (24 hours): {remaining_quantity}")

                        if remaining_quantity > 0:
                            print("SERVICE WITHIN 24 HOURS - TRIGGERING CASH WIZARD")
                            self._trigger_cash_service_wizard()

                            raise ValidationError(
                                _("You can only access a new service 24 hours after the last one. Remaining quantity: %d") % remaining_quantity
                            )
                        elif remaining_quantity <= 0:
                            print("NO REMAINING SERVICE ACCESS - TRIGGERING CASH WIZARD")
                            self._trigger_cash_service_wizard()
                            return False
                else:
                    print("No last service found or missing service_time")
            else:  # Logic for validity_period_days = 365 or other cases
                remaining_quantity = quantity_limit - self._count_services_in_category(parent_category_id)
                print("COUNT AT 365 days ---------------------------",self._count_services_in_category(parent_category_id))
                print(f"REMAINING SERVICE ACCESS IN THE CAT_DURATION ({validity_period_days} days): {remaining_quantity}")

                if remaining_quantity <= 0:
                    print("REMAINING SERVICE ACCESS REACHED ZERO - TRIGGERING CASH WIZARD")
                    self._trigger_cash_service_wizard()
                    return False
                elif remaining_quantity > 0:
                    print(f"Remaining quantity is still available: {remaining_quantity}")

        else:  # Logic for validity_period_days = 365 or other cases
            remaining_quantity = quantity_limit - self._count_services_in_category(parent_category_id)
            print(f"REMAINING SERVICE ACCESS IN THE CAT_DURATION ({validity_period_days} days): {remaining_quantity}")
            if remaining_quantity <= 0:
                print("REMAINING SERVICE ACCESS REACHED ZERO - TRIGGERING CASH WIZARD")
                self._trigger_cash_service_wizard()
                return False

        if self.service_based == 'location_duration':
            period_start = fields.Datetime.now() - timedelta(days=validity_period_days)
            print(f"START OF LOCATION DURATION SERVICE PERIOD: {period_start}")

            total_days = 0

            # Determine the activate date, accounting for a potentially null member_activate_date
            if self.member_activate_date:
                activate_date = self.member_activate_date
            else:
                # Default to 395 days before the member_expiry_date if activate_date is null
                activate_date = self.member_expiry_date - timedelta(days=395)
            # Fetch all services in the same category within the validity period
            # Fetch all services in the same category within the validity period
            member_services_in_category = self.env['aaa.service'].search([
                ('member_id', '=', self.member_id.id),
                ('product_id.categ_id', '=', parent_category_id),
                ('state', 'in', ['dispatch', 'start', 'reach', 'completed_by_driver', 'done']),
                ('service_time', '>=', activate_date),
                ('service_time', '<=', self.member_expiry_date),
                ('date_time_to', '>=', period_start),
            ])
            print(f"MEMBER SERVICES IN CATEGORY: {member_services_in_category}")
            # Calculate the total days accessed in the category
            for service in member_services_in_category:
                if service.service_based == 'location_duration' and service.date_time_to and service.date_time_from:
                    service_duration = (service.date_time_to - service.date_time_from).total_seconds() / (3600 * 24)
                    print(f"SERVICE DURATION FOR LOCATION DURATION SERVICE: {service_duration}")
                    total_days += service_duration
                    print(f"TOTAL SERVICE DAYS ACCESSED: {total_days}")

            # Calculate remaining days from the quantity limit
            remaining_days = quantity_limit - total_days
            print(f"REMAINING SERVICE DAYS ALLOWED: {remaining_days}")

            if remaining_days <= 0:
                print("SERVICE LIMIT EXCEEDED - TRIGGERING CASH WIZARD")
                return False

            # Check if the new service duration exceeds the remaining days
            new_service_duration = (self.date_time_to - self.date_time_from).total_seconds() / (3600 * 24)
            if new_service_duration > remaining_days:
                raise ValidationError(
                    _("The service can only be accessed for the remaining %d days. Please adjust the service duration.") % remaining_days
                )

        if self.date_time_from and self.date_time_to:
            delta = self.date_time_to - self.date_time_from
            self.quantity = delta.days  # This updates `quantity`
            self.quantity_with_days = f"{self.quantity} Days" if self.quantity else "0 Days"

        # Explicitly write `quantity_with_days` to save it in the database
        self.write({
            'quantity': self.quantity,
            'quantity_with_days': self.quantity_with_days,
        })
        return True

    def _is_service_accessible_in_24_hours(self, parent_category_id):
        last_dispatch_time = fields.Datetime.now() - timedelta(hours=24)

        # Determine the activate date, accounting for a potentially null member_activate_date
        if self.member_activate_date:
            activate_date = self.member_activate_date
        else:
            # Default to 395 days before the member_expiry_date if activate_date is null
            activate_date = self.member_expiry_date - timedelta(days=395)

        recent_services = self.env['aaa.service'].search_count([
            ('member_id', '=', self.member_id.id),
            ('product_id.categ_id', '=', parent_category_id),
            ('service_time', '>=', activate_date),
            ('service_time', '<=', self.member_expiry_date),
            ('state', 'in', ['dispatch', 'start', 'reach', 'completed_by_driver', 'done']),
            ('create_date', '>=', last_dispatch_time),
        ])
        return recent_services == 0

    def _count_services_in_category(self, parent_category_id):
        # Determine the activate date, accounting for a potentially null member_activate_date
        if self.member_activate_date:
            activate_date = self.member_activate_date
        else:
            # Default to 395 days before the member_expiry_date if activate_date is null
            activate_date = self.member_expiry_date - timedelta(days=395)

        count = self.env['aaa.service'].search_count([
            ('member_id', '=', self.member_id.id),
            ('product_id.categ_id', '=', parent_category_id),
            ('service_time', '>=', activate_date),
            ('service_time', '<=', self.member_expiry_date),
            ('state', 'in', ['dispatch', 'start', 'reach', 'completed_by_driver', 'done']),
        ])
        return count

    def _trigger_cash_or_credit_service_wizard(self):
        return {
            'name': _('Convert to Cash '),
            'type': 'ir.actions.act_window',
            'res_model': 'service.dispatch.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('customer.view_service_dispatch_wizard_form').id,
            'target': 'new',
            'context': {
                'default_service_id': self.id,
            },
        }

    def _trigger_cash_service_wizard(self):
        return {
            'name': _('Convert to Cash'),
            'type': 'ir.actions.act_window',
            'res_model': 'service.cash.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('customer.view_service_cash_wizard_form').id,
            'target': 'new',
            'context': {
                'default_service_id': self.id,
            },
        }

    def _dispatch_service(self):
        self._generate_service_name()
        self.state = 'dispatch'
        self._trigger_order_notification_api(self.name, self.state)
        _logger.info("Service dispatched successfully.")
        self.env['service.history'].create({
            'service_id': self.id,
            'user': self.env.user.id,
            'time': fields.Datetime.now(),
            'status': 'Dispatched',
            'timeline_status': 'dispatch',
        })
        for service in self:
            comment_content = service.comments or 'DISPATCHED'
            self.env['service.comment'].create({
                'service_id': service.id,
                'comment': comment_content,
                'comment_date_and_time': fields.Datetime.now(),
                'comment_user': self.env.user.id,
                'comment_status': service.state,
            })

            if service.comments:
                service.comments = False

            service.dispatch_done_by = self.env.user.id

        return True
# --------------------------------------------------------------------------------------------------
    @api.depends('requested_date')
    def _compute_next_check_time(self):
        """Compute the next check time when the record should be processed"""
        for record in self:
            if record.requested_date:
                # Round down to the nearest minute
                record.next_check_time = record.requested_date.replace(second=0, microsecond=0)
            else:
                record.next_check_time = False

    def action_schedule_service_check(self):
        self.schedule_service_check = True  
        if self.requested_date:
            # self.schedule_service_check = True
            self.state = 'initiate'
            print("Scheduling the Service - Triggering Wizard")
        else:
            print("Service scheduling failed - schedule_date_time is not set")
    #     self.schedule_service_check = True
    #     self.state = 'initiate'
    #     print("Scheduling the Service - Triggering Wizard")

    
 
        if not self.product_id:
            raise UserError(_("Provide the service details."))
         # Determine visible fields based on service_based and member_type
        if self.service_based in ['location', 'location_duration', 'none']:
            # `from_location` and `selected_from_location` are invisible
            from_location_visible = False
            to_location_visible = True
        else:
            # Both `from_location` and `selected_from_location` are visible
            from_location_visible = True
            to_location_visible = True
 
        # Adjust field visibility based on member_type
        if self.member_type in ['policy', 'adhoc']:
            # Use `selected_from_location` and `selected_to_location`
            from_location_field = self.location_from_external
            to_location_field = self.location_to_external
        elif self.member_type == 'credit':
            # Use `from_location` and `to_location`
            from_location_field = self.from_location
            to_location_field = self.to_location
        else:
            raise UserError(_("Invalid member type specified."))
 
        # Check visibility and raise appropriate errors
        if from_location_visible and not from_location_field:
            if to_location_visible and not to_location_field:
                raise UserError(_("Please provide both From Location and To Location details."))
            else:
                raise UserError(_("Please provide the From Location detail."))
        elif to_location_visible and not to_location_field:
            raise UserError(_("Please provide the To Location detail."))
 
        return {
            'name': _('Schedule Service'),
            'type': 'ir.actions.act_window',
            'res_model': 'schedule.service.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('customer.schedule_service_wizard_view_form').id,
            'target': 'new',
            'context': {
                'default_service_id': self.id,
            },
        }

    @api.model
    def check_and_update_state(self):
        current_minute = fields.Datetime.now().replace(second=0, microsecond=0)
        _logger.info("Running check_and_update_state at %s", current_minute)
        
        # Find records scheduled for the current minute or earlier
        domain = [
            ('state', '=', 'initiate'),
            ('next_check_time', '<=', current_minute),  # Include services scheduled before the current time
            ('requested_date', '<=', fields.Datetime.now())
        ]
        services = self.search(domain)
        _logger.info("Found %d services to update", len(services))
        
        for service in services:
            _logger.info("Processing service: %s", service.name)
            order_number = service.name
            if order_number:
                _logger.info("Creating order for service: %s", order_number)
                self.action_order_create(order_number)
            else:
                _logger.warning("No order number found for service: %s", service.name)
            
            service.write({'state': 'dispatch'})
            _logger.info("Service %s dispatched", service.name)
            
            # Create history entry
            self.env['service.history'].create({
                'service_id': service.id,
                'user': self.env.user.id,
                'time': service.requested_date,  # Use the original requested time
                'status': 'Dispatched by bot',
                'timeline_status': 'dispatch',
            })
            _logger.info("History entry created for service: %s", service.name)
            
            # Create comment entry
            self.env['service.comment'].create({
                'service_id': service.id,
                'comment': service.comments or 'Scheduled to dispatch',
                'comment_date_and_time': service.requested_date,  # Use the original requested time
                'comment_user': self.env.user.id,
                'comment_status': 'dispatch'
            })
            _logger.info("Comment entry created for service: %s", service.name)
        
        return True

    @api.onchange('member_id')
    def _onchange_member_id(self):
        """When member_id is set, automatically update the member_type in res.partner if it's a new member."""
        if self.member_id and not self.member_id.member_type:
            # Automatically set member type based on service form
            self.member_id.member_type = self.member_type  # Set from selection in aaa.service

    def action_start_service(self):
        for service in self:
            # Ensure credit_proforma_number is filled
            if not service.provider_id:
                raise UserError("You must fill the PROVIDER before starting the service.")
            if service.provider_id.name == "ARABIAN AUTOMOBILE ASSOCIATION" and not service.driver_id:
                raise UserError("You must fill the driver before completing the service when the provider is ARABIAN AUTOMOBILE ASSOCIATION.")
            # Proceed with setting the state to 'start'
            service.state = 'start'

            # Create the service.history record
            self.env['service.history'].create({
                'service_id': service.id,
                'user': self.env.user.id,
                'time': fields.Datetime.now(),
                'status': 'Started',
                'timeline_status': service.state,
            })
            # Prepare the comment content
            comment_content = service.comments or 'STARTED'
            # Create the service.comment record
            self.env['service.comment'].create({
                'service_id': service.id,
                'comment': comment_content,
                'comment_date_and_time': fields.Datetime.now(),
                'comment_user': self.env.user.id,
                'comment_status': service.state,
            })
            # Clear the comments field after creating the record
            if service.comments:
                service.comments = False

            if self.is_aditional_duty:
                print('name__',self.name)
                print('self.is_jafza_service___',self.is_jafza_service)
                print('self.is_aditional_duty',self.is_aditional_duty)
                api_url = f'{base_url}/aaa-customer/consumers/update/driver-service-type'
                data_api = json.dumps({
                    "erp_order_number": self.name,
                    "is_jafza_service": self.is_jafza_service,
                    "is_after_duty": self.is_aditional_duty
                })
                api_header = {
                    'content-type' : 'application/json'
                }

                response = requests.put(api_url, data=data_api, headers=api_header)
                if response.status_code == 200:
                    print(f"API RESPONSE- start,{response.text}")
                else:
                    print(f"API RESPONSE-ORDER NOT started,{response.text},{response.status_code}")
                
            self._trigger_order_notification_api(service.name, service.state)

        return True

    def action_reach_service(self):
        self.state = 'reach'
        for service in self:
            if not service.credit_proforma_number:
                raise UserError("You must fill the Trip Sheet Number before completing the service.")

            self.env['service.history'].create({
                'service_id': service.id,
                'user': self.env.user.id,
                'time': fields.Datetime.now(),
                'status': 'Reached',
                'timeline_status': self.state,
            })

            comment_content = service.comments or 'REACHED'

            # Create the service.comment record
            self.env['service.comment'].create({
                'service_id': service.id,
                'comment': comment_content,
                'comment_date_and_time': fields.Datetime.now(),
                'comment_user': self.env.user.id,
                'comment_status': service.state,
            })

            # If a manual comment exists, clear the service.comments field after creating the record
            if service.comments:
                service.comments = False

            service.reach_done_by = self.env.user.id
            
            self._trigger_order_notification_api(service.name, service.state)

        if service.comments:
            service.comments = False
        return True

    def action_completed_rac(self):
        self.state = 'completed_by_driver'
        for service in self:
                self.env['service.history'].create({
                    'service_id': service.id,
                    'user': self.env.user.id,
                    'time': fields.Datetime.now(),
                    'status': 'Completed by Driver',
                    'timeline_status': self.state,})
                self._trigger_order_notification_api(service.name, service.state)
        comment_content = service.comments or 'COMPLETED BY DRIVER'
            # Create the service.comment record
        self.env['service.comment'].create({
            'service_id': service.id,
            'comment': comment_content,
            'comment_date_and_time': fields.Datetime.now(),
            'comment_user': self.env.user.id,
            'comment_status': service.state,})
            # If a manual comment exists, clear the service.comments field after creating the record
        if service.comments:
            service.comments = False
        return True

    def action_done_service(self):
        for service in self:
            if not service.provider_id:
                raise UserError("You must fill the Provider before completing the service.")
            
            # Check if provider_id is 'ARABIAN AUTOMOBILE ASSOCIATION' before validating driver_id
            if service.provider_id.name == "ARABIAN AUTOMOBILE ASSOCIATION" and not service.driver_id:
                raise UserError("You must fill the driver before completing the service when the provider is ARABIAN AUTOMOBILE ASSOCIATION.")
            # Ensure credit_proforma_number is filled
            if not service.credit_proforma_number:
                raise UserError("You must fill the Trip Sheet Number before completing the service.")
            
            if service.is_afl_application == True and service.service_from_app == False:
                base_url = os.getenv('BASE_URL')

                base_url = f"{base_url}/carhire-order/order/service/afl-order/check-service-complete-status"
                params = {
                    'serviceNumber': service.name,
                }
                headers = {'Content-Type': 'application/json'}

                _logger.info("Sending GET API Request")
                try:
                    response = requests.get(base_url, params=params, headers=headers)

                    _logger.info("API Response: %s - %s", response.status_code, response.text)

                    if response.status_code == 200:
                        data = response.json()
                        is_ready = data.get("ready")
                        missing_fields = data.get("missingFields") or []

                        if is_ready == True:
                            service.state = 'done'

                            # Create the service.history record
                            self.env['service.history'].create({
                                'service_id': service.id,
                                'user': self.env.user.id,
                                'time': fields.Datetime.now(),
                                'status': 'Service Completed',
                                'timeline_status': service.state,
                            })

                            # Prepare the comment content
                            comment_content = service.comments or 'COMPLETED'

                            # Create the service.comment record
                            self.env['service.comment'].create({
                                'service_id': service.id,
                                'comment': comment_content,
                                'comment_date_and_time': fields.Datetime.now(),
                                'comment_user': self.env.user.id,
                                'comment_status': service.state,
                            })

                            # Clear the comments field after creating the record
                            if service.comments:
                                service.comments = False

                            service.done_done_by = self.env.user.id
                            
                            self._trigger_order_notification_api(service.name, service.state)

                            _logger.info("AFL service completed")

                        else:
                            _logger.info("AFL service not completed since fields are missing in app")

                            if missing_fields:
                                all_missing_fields = "\n - ".join(missing_fields)
                                raise UserError(f"The following fields are missing in app:\n - {all_missing_fields}")

                    else:
                        _logger.warning("API call returned non-200 status. Status: %s, Response: %s",
                                        response.status_code, response.text)

                except requests.exceptions.RequestException:
                    _logger.exception("API request failed for record ID %s", service.id)

            else:
            # Proceed with setting the state to 'done'
                service.state = 'done'

                # Create the service.history record
                self.env['service.history'].create({
                    'service_id': service.id,
                    'user': self.env.user.id,
                    'time': fields.Datetime.now(),
                    'status': 'Service Completed',
                    'timeline_status': service.state,
                })

                # Prepare the comment content
                comment_content = service.comments or 'COMPLETED'

                # Create the service.comment record
                self.env['service.comment'].create({
                    'service_id': service.id,
                    'comment': comment_content,
                    'comment_date_and_time': fields.Datetime.now(),
                    'comment_user': self.env.user.id,
                    'comment_status': service.state,
                })

                # Clear the comments field after creating the record
                if service.comments:
                    service.comments = False

                service.done_done_by = self.env.user.id
                
                self._trigger_order_notification_api(service.name, service.state)

        return True

    def cash_service(self):
        self.type = 'cash'

    def convert_to_non_cash(self):
        self.type = 'non_cash'

    def action_cancel_service(self):
        for service in self:
            # Force setting the state to 'cancel'
            service.sudo().write({'state': 'cancel'})
            # Create a service history record
            self.env['service.history'].sudo().create({
                'service_id': service.id,
                'user': self.env.user.id,
                'time': fields.Datetime.now(),
                'status': 'Cancelled',  # Explicitly set the status
            })

            # Use a default comment if no comment exists
            comment_content = service.comments or 'CANCELLED'

            # Create a service comment record
            self.env['service.comment'].sudo().create({
                'service_id': service.id,
                'comment': comment_content,
                'comment_date_and_time': fields.Datetime.now(),
                'comment_user': self.env.user.id,
                'comment_status': 'cancel',  # Explicitly set the status
            })

            # Clear the comments field if it had a manual comment
            if service.comments:
                service.sudo().write({'comments': False})

        return True

    def action_discard(self):
        self.state = 'discard'

    def action_change(self):
        self.state = 'change'
        for service in self:
                # Prepare the origin_no content based on member_type
            if service.member_type == 'credit':
                origin_info = (
                    f"Service: {service.product_id.name if service.product_id else 'N/A'}\n"
                    f"From location: {service.from_location.name if service.from_location else 'N/A'}\n"
                    f"To location: {service.to_location.name if service.to_location else 'N/A'}"
                )
            elif service.member_type in ['policy', 'adhoc']:
                origin_info = (
                    f"Service: {service.product_id.name if service.product_id else 'N/A'}\n"
                    f"From location: {service.location_from_external if service.location_from_external else 'N/A'}\n"
                    f"To location: {service.location_to_external if service.location_to_external else 'N/A'}"
                )
            else:
                origin_info = "Not applicable"

            service.orgin_no = origin_info
            self.env['service.history'].create({
                    'service_id': service.id,
                    'user': self.env.user.id,
                    'time': fields.Datetime.now(),
                    'status': 'Change',
                    'timeline_status': self.state,
                })
            comment_content = service.comments or 'Change'

        # If a manual comment exists, clear the service.comments field after creating the record
        if service.comments:
            service.comments = False

        return True

    def action_custom_cancel_service(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'history_back',
        }

    def action_create_enquiry(self):
        # Create a new enquiry record linked to the current service
        new_enquiry = self.env['aaa.enquiry'].write({
            #'name': self.name,
            'customer_id': self.customer_id.id,
            'member_id': self.member_id.id,
            'service_id': self.product_id.id,
            'enq_id': self.id,
            'membership': self.member_type,
            'mem_name': self.member_id.name,
            'vehicle_chasis_no': self.vehicle_chasis_no,
            'vehicle_plate_no': self.vehicle_plate,
            'policy_no': self.policy_no,
            'enq_id': self.id,  # Link the enquiry to the current service
            'date': fields.Datetime.now(),
            'mobile': self.member_contact_no,
            'email': self.email,
            'comment': self.comments ,
            'created_by': self.env.user.id,
            'enquiry': self.comments,
            'enquiry_type_id': self.env['enquiry.config'].search([], limit=1).id,
            'enquiries_id': self.env['enquiry.subtype'].search([], limit=1).id,
            'complaint_type_id': self.env['complaint.config'].search([], limit=1).id,
            'complaints_id': self.env['complaint.subtype'].search([], limit=1).id,
            #'enquiry_state': self.state
        })

        # Open the Enquiry/Complaint wizard
        view_id = self.env.ref('customer.view_enquiry_complaint_wizard_form').id
        return {
            'name': 'Select Enquiry or Complaint',
            'type': 'ir.actions.act_window',
            'res_model': 'enquiry.complaint.wizard',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
            'context': {
                #'default_enq_cm_id': new_enquiry.id,
                'default_customer_id': self.customer_id.id,
                'default_member_id': self.member_id.id,
                'default_service_id': self.product_id.id,
                'default_enq_id': self.id,
                'default_mem_name': self.member_id.name,
                'default_membership': self.member_type,
                'default_mobile': self.member_contact_no,
                'default_comment': self.comments,
                'default_vehicle_chasis_no': self.vehicle_chasis_no,
                'default_vehicle_plate_no': self.vehicle_plate,
                'default_policy_no': self.policy_no,
                'default_email': self.email,
                #'default_enquiry_state': self.state
            }
        }

    def action_waive_off(self):
        # self.waive_off = True
        pass

    def action_new(self):
        pass

    def history(self):
        pass

    def action_new_change(self):
        """Update existing service record, change state, and store previous names of fields."""

        for service in self:
            print("product_name:", service.product_id.name)
            print("service_type", service.product_id.service_based)
            print("SERVICE SEQUENCE NO:", service.name)
            # Set up the API call
            url = f"{base_url}/carhire-order/order/service/consumers/orders/update/order-service-change"
            headers = {'Content-Type': 'application/json'}

            # Map the service_based value to the appropriate API parameter
            service_based_mapping = {
                'location': 'LOCATION_BASED',
                'distance': 'DISTANCE_BASED'
            }
            new_service_type = service_based_mapping.get(service.product_id.service_based, service.product_id.service_based)

            payload = {
                "erp_order_number": service.name,
                "new_service_name": service.product_id.name,
                "new_service_type": new_service_type
            }

            response = requests.put(url, json=payload, headers=headers)

            try:
                service.write({
                    'state': 'initiate',  # Update the state to 'initiate'
                    'customer_id': service.customer_id.id,
                    'sequence_id': service.sequence_id.id,
                    'member_id': service.member_id.id,
                    'vehicle_type': service.vehicle_type,
                    'vehicle_model': service.vehicle_model,
                    'vehicle_plate': service.vehicle_plate,
                    'vehicle_chasis_no': service.vehicle_chasis_no,
                    'policy_no': service.policy_no,
                    'member_type': service.member_type,
                    'type': service.type,
                    'card_type': service.card_type,
                    'product_id': service.product_id.id,
                    'location_from_external': service.location_from_external,
                    'location_to_external': service.location_to_external,
                    'from_location': service.from_location.id,
                    'to_location': service.to_location.id,
                })
                print("SERVICE UPDATED, NEW STATE:", service.state)
            except Exception as e:
                print("ERROR UPDATING SERVICE:", str(e))
                # raise UserError(_("Failed to update the service: %s") % str(e))
        # for service in self:
            self.env['service.history'].create({
                'service_id': service.id,
                'user': self.env.user.id,
                'time': fields.Datetime.now(),
                'status': 'Applied Changes',
                'timeline_status': self.state,
            })

                        # Use a default comment if no comment exists
            comment_content = service.comments or 'CHANGED'

            # # Create a service comment record
            self.env['service.comment'].sudo().create({
                'service_id': service.id,
                'comment': comment_content,
                'comment_date_and_time': fields.Datetime.now(),
                'comment_user': self.env.user.id,
                'comment_status': 'Applied Changes',  
            })

            # Clear the comments field if it had a manual comment
            if service.comments:
                service.sudo().write({'comments': False})
        # Optionally, refresh the view to show changes
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_request_service(self):
        self.state='requested'
        for service in self:
            self.env['service.history'].create({
                'service_id': service.id,
                'user': self.env.user.id,
                'time': fields.Datetime.now(),
                'status': 'Requested to Change Cancellation State',
                'timeline_status': service.state,
            })
            comment_content = service.comments or 'Requested to Change Cancellation State'

        if service.comments:
            service.comments = False
        return True

    def action_approve_service(self):
        self.state='initiate'
        for service in self:
            # TIMELINE TREE
            self.env['service.history'].create({
                'service_id': service.id,
                'user': self.env.user.id,
                'time': fields.Datetime.now(),
                'status': 'Request to Change Cancelled State Approved',
                'timeline_status': self.state,
                })
            # COMMENTS TREE
            self .env['service.comment'].create({
                'service_id': service.id,
                'comment' : service.comments or 'Request to Change Cancelled State Approved',
                'comment_date_and_time' : fields.Datetime.now(),
                'comment_user': self.env.user.id,
                'comment_status' : service.state,
        })
    ###############  CANCELLING DONE SERVICES ACTION###################        
    def action_cancel_done_service(self):
        self.state='done_cancel'
        for service in self:
            # TIMELINE TREE
            self.env['service.history'].create({
                'service_id': service.id,
                'user': self.env.user.id,
                'time': fields.Datetime.now(),
                'status': 'CANCELLED DONE SERVICES',
                'timeline_status': self.state,
                })
            # COMMENTS TREE
            self .env['service.comment'].create({
                'service_id': service.id,
                'comment' : service.comments or 'CANCELLED DONE SERVICES',
                'comment_date_and_time' : fields.Datetime.now(),
                'comment_user': self.env.user.id,
                'comment_status' : service.state,
        })

            


    def download_service_attachments_zip(self):
        # Create a binary stream to write the zip data
        zip_stream = io.BytesIO()

        with zipfile.ZipFile(zip_stream, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for record in self:
                folder_name = f"{'service'}_{record.id}"
                attachments = self.env['ir.attachment'].search([
                    ('res_model', '=', 'aaa.service'),
                    ('res_id', '=', record.id),
                    ('type', '=', 'binary')
                ])

                for attachment in attachments:
                    filename = attachment.name or f"file_{attachment.id}"
                    if attachment.datas:
                        decoded = base64.b64decode(attachment.datas)
                        zip_path = f"{folder_name}/{filename}"
                        zipf.writestr(zip_path, decoded)

        zip_stream.seek(0)

        # Create a download response using ir.actions.act_url
        base64_zip = base64.b64encode(zip_stream.read()).decode()

        # Save in ir.attachment temporarily
        attachment = self.env['ir.attachment'].create({
            'name': 'service_attachments.zip',
            'type': 'binary',
            'datas': base64_zip,
            'mimetype': 'application/zip'
        })

        # Redirect to download the file
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

   ################## Base api tocken gereration code ############################## 
    
    # def get_auth_token_for_client(self):
    #     base_url_client = os.getenv("BASE_URL_CLIENT")
    #     client_username = os.getenv("CLIENT_USERNAME")
    #     client_password = os.getenv("CLIENT_PASSWORD") 

    #     url = f'{base_url_client}/am/carhire/oauth/token?grant_type=client_credentials'
 
    #     auth = HTTPBasicAuth(client_username, client_password)
    #     response = requests.post(url, auth=auth)

    #     if response.status_code == 200:
    #         data = response.json()
    #         return data["access_token"]
        

    def _trigger_order_notification_api(self, order_number, status):
        for record in self:
            # auth_token = record.get_auth_token_for_client()
            url = 'https://gioapi-gy-dev.kirkos.ae/aaa-customer/consumers/order-notification'
            
            headers = {'Content-Type': 'application/json',
                       'Accept': '*/*'
                       }
            
            payload = {
                            "order_number": order_number,
                            "status": status,
                        }
            
            try:
                response = requests.post(url, headers=headers, json=payload)
                print("Response Text:", response.text)
                print(f"status code: {response.status_code}")
                if response.status_code == 200:
                    try:
                        response_text = response.json()
                        _logger.info("Notification sent successfully: %s", response_text)
                        print("Response sent successfully")
                    except json.JSONDecodeError:
                        _logger.info("Non-JSON response received: %s", response.text)
                        print("Non-JSON response received:", response.text)
                else:
                    _logger.info("Failed to send notification, status code: %s, message: %s", response.status_code, response.text)
                    print("Failed to send, status code:", response.status_code, "message:", response.text)

            except requests.exceptions.RequestException as e:
                _logger.info("Request failed: %s", str(e))
                print("Request failed:", str(e))
            



class ServiceComment(models.Model):
    _name = 'service.comment'
    _description = 'Service Comment'

    comment = fields.Text(string="Comment")
    comment_date_and_time = fields.Datetime(string="Comment Date and Time")
    comment_user = fields.Many2one('res.users', string="Comment User")
    comment_status = fields.Char(string="Comment Status")
    service_id = fields.Many2one('aaa.service', string="Service")

class ServiceHistory(models.Model):
    _name = 'service.history'
    _description = 'Service History'

    user = fields.Many2one('res.users', string="User")
    time = fields.Datetime(string="Time")
    status = fields.Char(string="Status")
    # timeline_status = fields.Text(string="Timeline Status")
    timeline_status = fields.Selection([
        ('draft', 'Draft'),
        ('initiate', 'Initiate'),
        ('dispatch', 'Dispatch'),
        ('start', 'Start'),
        ('reach', 'Reach'),
        ('completed_by_driver', 'Completed by driver'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ('driver_cancel', 'Driver Cancelled'),
        ('change', 'Change' ),
        ('approved','Approved'),
        ('requested','Requested'),
        ('done_cancel', 'Done Cancelled')
    ], string="Timeline Status", readonly=True, default='initiate', tracking=True)
    service_id = fields.Many2one('aaa.service', string="Service")

class AaaServiceAddon(models.Model):
    _name = 'aaa.service.addon'
    _description = 'Additional Service'

    service_id = fields.Many2one('aaa.service', string='Service')
    product_id = fields.Many2one(
        'product.template',
        string="Service",
        domain=[('name', 'in', ['GATE PASS', 'KEY COLLECTION CHARGES', 'MECHANICAL ASSISTANCE', 'WAITING CHARGES', 'REACHED AND CANCELLED'])]
    )

    provider_from_location_id = fields.Many2one('location.internal', string="From Location")
    provider_to_location_id = fields.Many2one('location.internal', string="To Location")

    from_date= fields.Datetime(string="From Date")
    to_date= fields.Datetime(string="To Date")
    quantity= fields.Float(string="Quantity")
    description = fields.Char(' Description')
    uom= fields.Many2one('uom.uom', string="UoM")
    price_subtotal = fields.Float('Price Subtotal')

    @api.onchange('from_date', 'to_date', 'uom')
    def _compute_quantity_based_on_dates(self):
        """
        This method computes the quantity based on the difference between the `from_date`
        and `to_date` and the `uom` (unit of measurement).
        """
        if self.from_date and self.to_date:
            # Calculate the difference between the two dates
            delta = fields.Datetime.from_string(self.to_date) - fields.Datetime.from_string(self.from_date)

            # Check if UoM is set and it is in days or hours (you can adjust this to your needs)
            if self.uom:
                # Example calculation: if UoM is "hours", quantity will be the difference in hours
                if self.uom.name.lower() in ['hours', 'hr']:  # Assuming your UoM names contain 'hours'
                    self.quantity = delta.total_seconds() / 3600  # Convert seconds to hours
                elif self.uom.name.lower() in ['days', 'day']:  # Assuming your UoM names contain 'days'
                    self.quantity = delta.total_seconds() / (3600 * 24)  # Convert seconds to days
                else:
                    # For other UoM types, you can define custom logic based on your requirements
                    self.quantity = delta.total_seconds()  # In seconds (or any other unit you want)
            else:
                # Default quantity calculation in hours if UoM is not specified
                self.quantity = delta.total_seconds() / 3600

              # Update the 'description' field with the date range in dd/mm/yy format
            from_date_str = fields.Datetime.to_string(self.from_date) if self.from_date else ''
            to_date_str = fields.Datetime.to_string(self.to_date) if self.to_date else ''

            if from_date_str and to_date_str:
                # Convert to dd/mm/yy format
                from_date_formatted = fields.Datetime.from_string(self.from_date).strftime('%d/%m/%y')
                to_date_formatted = fields.Datetime.from_string(self.to_date).strftime('%d/%m/%y')

                self.description = f"{from_date_formatted} to {to_date_formatted}"
            else:
                self.description = ""
