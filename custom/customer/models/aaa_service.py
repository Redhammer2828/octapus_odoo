from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import datetime
from datetime import timedelta
import requests
import json

class AAAService(models.Model):
    _name = 'aaa.service'
    _description = 'AAA Service'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Number", readonly=True, default=lambda self:('New'))
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
        ('change', 'Changed' )
    ], string="Status", readonly=True, default='initiate', tracking=True)
 
    
    #MANY2ONE-------------------------------------------------------------------------------------------------------
    customer_id = fields.Many2one('res.partner', string="Customer", domain="[('is_company', '=', True)]")
    credit_customer_co = fields.Char('Customer C/O')
    sequence_id = fields.Many2one('partner.category', string="Customer Category", domain="[('partner_id','=', customer_id)]")
    member_id = fields.Many2one(
        'res.partner', 
        string="Member", 
        domain=[('is_company', '=', False)] 
    )
    created_by = fields.Many2one('res.users', string="Agent", default=lambda self: self.env.user, readonly=True)
    
    # vehicle_type_id = fields.Many2one('member.vehicle.type', string="Vehicle Type")
    # vehicle_model_id = fields.Many2one('member.vehicle.model', string="Vehicle Model")
    vehicle_type_id = fields.Char('Vehicle Type')   #Chaged to char
    vehicle_model_id = fields.Char('Vehicle Model')  #Changed to char
    
    product_id = fields.Many2one('product.template', string="Service",domain=[('bundle_product', '=', False)])  
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure")
    new_service_id = fields.Many2one('product.template', string="New Service")
    main_product_ids = fields.Many2many('product.template', string="Main Products")
    cancelled_service_id = fields.Many2one('aaa.service', string="Cancelled Service", readonly=True)
    acc_payment_id = fields.Many2one('account.payment', string="Payment")
   
    # PROVIDER-------------------------------------------------------------------------------------------------------------
    provider_id = fields.Many2one('res.partner', string="Provider" ,domain=[('is_vendor', '=', True)]) #  domain="[('supplier', '=', True)]"
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
    # driver_id = fields.Many2one('hr.employee', string="Driver", domain=[('job_title', '=', 'Driver')])
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
    schedule_date_time = fields.Datetime(string="Schedule Date Time")
    requested_date = fields.Datetime(string="Requested Date")
    driving_license = fields.Char(string="Driving License")
    claim_number = fields.Char(string="Claim Number")
    smarto = fields.Boolean(string="Smarto")
    smarto_id = fields.Char(string="Smarto ID")
    comments = fields.Text(string="Comments")
    vehicle_type_ok = fields.Boolean(string="Vehicle Type OK")
    vehicle_model_ok = fields.Boolean(string="Vehicle Model OK")
    vehicle = fields.Char('vehicle')
    #  domain="[('id', '=', vehicle_type_id)]"
    vehicle_type = fields.Char(string="Vehicle Type")
    
    # , domain="[('type_id', '=', vehicle_type_id)]"
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
    
    # datetime_from = fields.Datetime(string="Datetime From")
    # datetime_to = fields.Datetime(string="Datetime To")
    date_time_from = fields.Datetime(string= "From Date time") 
    date_time_to = fields.Datetime(string="To Date time")
    quantity = fields.Float(string="Quantity")
    service_type = fields.Selection(related='product_id.service_type', store=True, readonly=True)
    
    
    service_time = fields.Datetime(string="Service Time")
    cash_collected_hidden = fields.Boolean(string="Cash Collected Hidden")
    cash_collected = fields.Float(string="Cash Collected")
    # amount=fields.Float(compute='_compute_location_amount',string="Cash To Be Collected")      
    
    addon_ok = fields.Boolean(string="Addon OK")
    waive_off = fields.Boolean(string="Waive Off")
    
    # One to Many -------------------------------------------------------------------------------------------
    comment_history_ids = fields.One2many('service.comment', 'service_id', string="Comment History")
    service_history_ids = fields.One2many('service.history', 'service_id', string="Service History")
    enquiry_ids = fields.One2many('aaa.enquiry', 'service_id', string="Enquiries")
    addon_service_ids = fields.One2many(
        'aaa.service.addon',
        'service_id',
        string='Additional Services'
    )
    # =========================================================================================================
   
    driver_id = fields.Many2one('hr.employee', string="Driver")
    is_driver_name_visible = fields.Boolean(string='Display Driver Name',default=True)
    enquiry_ids = fields.One2many('aaa.enquiry','enq_id',string="Enquiries") # IN aaa.service  
    
    completion_time = fields.Datetime(string="Completion Time")
    member_activate_date = fields.Date('Member Activate Date')
    member_expiry_date = fields.Date('Member Expiry Date')

    # # -----------LOCATION- API TESTINGs--------------------------------------------------
    
    search_query = fields.Char(string='Search Locations')
    search_results = fields.Many2many('location.suggestion', string='Search Results', compute='_fetch_location_suggestions')
    selected_from_location = fields.Many2one('location.suggestion', string='From Location')
    selected_to_location = fields.Many2one('location.suggestion', string='To Location')
    amount = fields.Integer(string='Amount', compute='_compute_amount', store=True)  # Dynamically computed amount

    from_location_emirate = fields.Char(string='Emirate', compute='_compute_emirates', store=True)
    to_location_emirate = fields.Char(string='Emirate', compute='_compute_emirates', store=True)

    @api.depends('search_query')
    def _fetch_location_suggestions(self):
        for record in self:
            record.search_results = [(5, 0, 0)]  # Clear existing results
            if record.search_query:
                try:
                    url = "https://nominatim-carhire-dev.livelocal.delivery/search.php"
                    params = {
                        'q': record.search_query,
                        'format': 'geocodejson',
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

    @api.depends('selected_from_location', 'selected_to_location')
    def _compute_amount(self):
        for record in self:
            if record.selected_from_location and record.selected_to_location:
                # Fetch lat/long from selected locations
                from_lat = record.selected_from_location.latitude
                from_lon = record.selected_from_location.longitude
                to_lat = record.selected_to_location.latitude
                to_lon = record.selected_to_location.longitude

                # Search for matching LocationService
                location_service = self.env['location.service'].search([
                    ('from_latitude', '=', from_lat),
                    ('from_longitude', '=', from_lon),
                    ('to_latitude', '=', to_lat),
                    ('to_longitude', '=', to_lon)
                ], limit=1)

                if location_service:
                    record.amount = location_service.amount
                else:
                    record.amount = 0  # No matching service found, set to 0
            else:
                record.amount = 0  # If locations are not selected, set amount to 0


    @api.depends('selected_from_location', 'selected_to_location')
    def _compute_emirates(self):
        for record in self:
            if record.selected_from_location:
                record.from_location_emirate = self._extract_emirate_from_feature_data(record.selected_from_location.feature_data)
            else:
                record.from_location_emirate = ''

            if record.selected_to_location:
                record.to_location_emirate = self._extract_emirate_from_feature_data(record.selected_to_location.feature_data)
            else:
                record.to_location_emirate = ''

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
    @api.onchange('provider_id')
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
    
    @api.onchange('customer_id','sequence_id')
    def _onchange_customer_id_sequence_id(self):
        context = self.env.context
        # Check if the specific context keys match the expected values
        if context.get('default_member_type') == 'credit' and context.get('default_type') == 'non_cash':
            for record in self:
                if record.customer_id:
                    # Search for the sequence that matches the criteria
                    sequence = self.env['partner.category'].search([
                        ('partner_id', '=', record.customer_id.id),
                        ('member_type', '=', 'credit'),
                        ('name', '=', record.sequence_id.name)
                    ], limit=1)
                   
                    # Set the sequence_id to the found sequence
                    record.sequence_id = sequence.id if sequence else False
 
                    # If sequence is found, set default_member from the category
                    if sequence:
                         # Assign the `default_member` from the `sequence` (partner.category) to `record.member_id`
                        record.member_id = sequence.default_member.id if sequence.default_member else False
                   
    @api.model
    def create(self, vals):
        # Ensure the name field is set using a sequence if not provided
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('aaa.service') or _('New')
       
        # Create the aaa.service record
        service = super(AAAService, self).create(vals)
       
        # Create the service.history record
        self.env['service.history'].create({
            'service_id': service.id,
            'user': self.env.user.id,
            'time': fields.Datetime.now(),
            'status': service.state,
        })

        self .env['service.comment'].create({
            'service_id': service.id,
            'comment' : service.comments,
            'comment_date_and_time' : fields.Datetime.now(),
            'comment_user': self.env.user.id,
            'comment_status' : service.state,
           
        })
       
        return service
    
    def action_initiate_service(self):
        self.state = 'initiated'
   
    def action_order_response(self, order_number, status, phone_number, vehicle_chasis_no):
        url = "https://gioapi-gy-dev.kirkos.ae/aaa-customer/whatsapp/whatsapp-Notification"
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
                    self.message_post(body=_("Notification sent successfully: %s") % response_text)
                    print("Response sent successfully")
                except json.JSONDecodeError:
                    # Handle non-JSON response here
                    self.message_post(body=_("Non-JSON response received: %s") % response.text)
                    print("Non-JSON response received:", response.text)
            else:
                self.message_post(body=_("Failed to send notification, status code: %s, message: %s") % (response.status_code, response.text))
                print("Failed to send, status code:", response.status_code, "message:", response.text)
                
        except requests.exceptions.RequestException as e:
            self.message_post(body=_("Request failed: %s") % str(e))
            print("Request failed:", str(e))

    def action_order_create(self, order_number):
        url = f"https://gioapi-gy-dev.kirkos.ae/aaa-customer/consumers/create/road_side_service/{order_number}"

        response = requests.post(url)

        print("API RESPONSE-ORDER CREATED",response.text)
        
# ---------------------------------------------------NEW A CODE-----------------------------------------------
    def action_dispatch_service(self):
        self.ensure_one()
        self._generate_service_name()
        
        # Check for Credit
        if self.member_id.member_type in ['credit', 'adhoc']:
            # Directly dispatch service without any validation
            self._dispatch_service()
            return True
        if not self.member_id:
            raise ValidationError(_("Member not found in the service record."))
 
        member = self.member_id
        print("POLICY MEMBER = res_partner id =", member.id)
        product_template_id = member.product_template_id.id
        print("PACKAGE ID OF POLICY MEMBER = product.package.servide", product_template_id)
 
        if not product_template_id:
            raise ValidationError(_("Package not found for the member."))
 
        if not self._is_service_in_package(product_template_id):
            print("SERVICE NOT IN PACKAGE - TRIGGERING CASH/CREDIT WIZARD")
            return self._trigger_cash_or_credit_service_wizard()
 
        if not self._validate_service_limits(product_template_id):
            print("SERVICE VALIDITY REACHED THE CATEGORY LIMITS - TRIGGERING CASH WIZARD")
            return self._trigger_cash_service_wizard()
 
        self._dispatch_service()
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
        print("PARENT CATEGORY OF CHOSEN SERVICE  IN PACKAGE", parent_category_id)
 
        if not parent_category_id:
            return True
 
        category_limits = self.env['product.category.limit'].search([
            ('categ_id', '=', parent_category_id),
            ('category_id', '=', product_template_id)
        ])
        print("VAL_LIMITS OF PARENT_CAT", category_limits)
 
        if not category_limits:
            return True
 
        quantity_limit = 10  # Default value
        validity_period_days = 365  # Default value
 
        for limit in category_limits:
            quantity_limit = float(limit.quantity)
            print("NO OF SERVICE_ACCESS IN CAT_DURATION",quantity_limit)
            validity_period_days = limit.hours if limit.uom_id.name == 'Days' else (limit.hours * 24)
            print("CAT_DURATION", validity_period_days)
 
        # Check for services that need to adhere to the 24-hour rule
        if any(limit.hours == 24 and limit.quantity == 1 for limit in category_limits):
            if not self._is_service_accessible_in_24_hours(parent_category_id):
                print("SERVICE DISPATCHED BEFORE 24 HOURS - TRIGGERING CASH WIZARD")
                return False # Trigger the cash service wizard
            else:
                return True
   
        if self.service_type != 'location_duration':
            if not self._is_service_accessible_in_24_hours(parent_category_id):
                remaining_quantity = quantity_limit - self._count_services_in_category(parent_category_id)
                print("REMAINING SERVICE ACCESS in the CAT_DURATION", remaining_quantity)
                if remaining_quantity <= 0:
                    print("REMAINING SERVICE ACCESS REACHED ZERO - TRIGGERING CASH WIZARD")
                    return False  # Trigger the cash service wizard
                raise ValidationError(
                    _("A service can only be initiated after 24 hours of the last dispatch. Remaining quantity: %d") % remaining_quantity
                )
             # Additional validation to check if the service is within the category limits, even if more than 24 hours have passed
            remaining_quantity = quantity_limit - self._count_services_in_category(parent_category_id)
            if remaining_quantity <= 0:
                print("REMAINING SERVICE ACCESS REACHED ZERO AFTER 24 HOURS - TRIGGERING CASH WIZARD")
                return False  # Trigger the cash service wizard
           
       
        if self.service_type == 'location_duration':
            period_start = fields.Datetime.now() - timedelta(days=validity_period_days)
            print("START OF RAC_CAT SERVICE", period_start)
 
            total_days = 0
            member_services_in_category = self.env['aaa.service'].search([
                ('member_id', '=', self.member_id.id),
                ('product_id.categ_id', '=', parent_category_id),
                # ('state', '=', 'dispatch'),
                ('state', 'in', ['dispatch', 'inprogress', 'start', 'reach', 'done']),
                ('date_time_to', '>=', period_start),
            ])
            print("MEMBER SERVICES IN PARENT_CAT", member_services_in_category)
 
            for service in member_services_in_category:
                if service.service_type == 'location_duration' and service.date_time_to and service.date_time_from:
                    service_duration = (service.date_time_to - service.date_time_from).total_seconds() / (3600 * 24)
                    print("SERVICE DURATION FOR RAC_CAT SERVICE", service_duration)
                    total_days += service_duration
 
                    print("TOTAL DAYS OF RAC_CAT SERVICE ACCESS", total_days)
 
            # if total_days >= quantity_limit:
            #     return False
 
                # Check if remaining service days exceed the quantity limit
            remaining_days = quantity_limit - total_days
            print("REMAINING SERVICE DAYS ALLOWED:", remaining_days)
 
            if remaining_days <= 0:
                return False
           
            # Check if the new service exceeds the remaining days
            new_service_duration = (self.date_time_to - self.date_time_from).total_seconds() / (3600 * 24)
            if new_service_duration > remaining_days:
                    raise ValidationError(
                        _("The service can only be accessed for the remaining %d days. Please adjust the service duration.") % remaining_days
                    )
 
 
 
            if not self._is_service_accessible_in_24_hours(parent_category_id):
                remaining_quantity = quantity_limit - total_days
                print("REMAINING RAC_CAT SERVICE", remaining_quantity)
                raise ValidationError(
                    _("A service of type 'location_duration' can only be initiated after 24 hours of the last dispatch. Remaining quantity (days): %d") % remaining_quantity
                )
 
        return True
 
    def _is_service_accessible_in_24_hours(self, parent_category_id):
        last_dispatch_time = fields.Datetime.now() - timedelta(hours=24)
        recent_services = self.env['aaa.service'].search_count([
            ('member_id', '=', self.member_id.id),
            ('product_id.categ_id', '=', parent_category_id),
            # ('state', '=', 'dispatch'),
            ('state', 'in', ['dispatch', 'inprogress', 'start', 'reach', 'done']),
            ('create_date', '>=', last_dispatch_time),
        ])
        return recent_services == 0
 
    def _count_services_in_category(self, parent_category_id):
        return self.env['aaa.service'].search_count([
            ('member_id', '=', self.member_id.id),
            ('product_id.categ_id', '=', parent_category_id),
            # ('state', '=', 'dispatch'),
            ('state', 'in', ['dispatch', 'inprogress', 'start', 'reach', 'done']),
        ])
 
    def _trigger_cash_or_credit_service_wizard(self):
        return {
            'name': _('Convert to Cash or Credit Service'),
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
        self.state = 'dispatch'
        self.message_post(body=_("Service dispatched successfully."))
        self.env['service.history'].create({
            'service_id': self.id,
            'user': self.env.user.id,
            'time': fields.Datetime.now(),
            'status': self.state,
        })

        self .env['service.comment'].create({
            'service_id': self.id,
            'comment' : self.comments or 'DISPATCHED',
            'comment_date_and_time' : fields.Datetime.now(),
            'comment_user': self.env.user.id,
            'comment_status' : self.state,
           
         })
# --------------------------------------------------------------------------------------------------
    def action_schedule_service_check(self):
        self.schedule_service_check = True
        self.state= 'initiate'
        print("Scheduling the Service - Triggering Wizard")
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
        now=fields.Datetime.now()
        records= self.search([('state', '=', 'initiate'),('requested_date', '<=', now)])
        records.write({'state':'dispatch'})
    
        for record in records:
            self.env['service.history'].create({
                'service_id': record.id,
                'user': self.env.user.id,
                'time': fields.Datetime.now(),
                'status': record.state,
            })
            self .env['service.comment'].create({
                'service_id': record.id,
                'comment' : record.comments or 'Scheduled to dispatch',
                'comment_date_and_time' : fields.Datetime.now(),
                'comment_user': self.env.user.id,
                'comment_status' : record.state,
           
        })

    @api.onchange('member_id')
    def _onchange_member_id(self):
        """When member_id is set, automatically update the member_type in res.partner if it's a new member."""
        if self.member_id and not self.member_id.member_type:
            # Automatically set member type based on service form
            self.member_id.member_type = self.member_type  # Set from selection in aaa.service
    
    def action_start_service(self):
        self.state = 'start'
        for service in self:
            
                self.env['service.history'].create({
                    'service_id': service.id,
                    'user': self.env.user.id,
                    'time': fields.Datetime.now(),
                    'status': service.state,  
                })
                self .env['service.comment'].create({
                    'service_id': service.id,
                    'comment' : service.comments or 'STARTED',
                    'comment_date_and_time' : fields.Datetime.now(),
                    'comment_user': self.env.user.id,
                    'comment_status' : service.state,
                
        })
        return True
    
    def action_reach_service(self):
        self.state = 'reach'
        for service in self:
            
                self.env['service.history'].create({
                    'service_id': service.id,
                    'user': self.env.user.id,
                    'time': fields.Datetime.now(),
                    'status': service.state,  
                })

                self .env['service.comment'].create({
                    'service_id': service.id,
                    'comment' : service.comments or 'REACHED',
                    'comment_date_and_time' : fields.Datetime.now(),
                    'comment_user': self.env.user.id,
                    'comment_status' : service.state,
           
        })
        return True

    def action_done_service(self):
        self.state = 'done'
        for service in self:
            
                self.env['service.history'].create({
                    'service_id': service.id,
                    'user': self.env.user.id,
                    'time': fields.Datetime.now(),
                    'status': service.state,  
                })

                self .env['service.comment'].create({
                    'service_id': service.id,
                    'comment' : service.comments or 'COMPLETED',
                    'comment_date_and_time' : fields.Datetime.now(),
                    'comment_user': self.env.user.id,
                    'comment_status' : service.state,
           
        })
        return True

    def cash_service(self):
        self.type = 'cash'

    def convert_to_non_cash(self):
        self.type = 'non_cash'

    def action_cancel_service(self):
        self.state = 'cancel'
        for service in self:
            
                self.env['service.history'].create({
                    'service_id': service.id,
                    'user': self.env.user.id,
                    'time': fields.Datetime.now(),
                    'status': service.state,  
                })
                self .env['service.comment'].create({
                    'service_id': service.id,
                    'comment' : service.comments or 'CANCELLED',
                    'comment_date_and_time' : fields.Datetime.now(),
                    'comment_user': self.env.user.id,
                    'comment_status' : service.state,
                
        })
        return True

    def action_discard(self):
        self.state = 'discard'
    
    def action_change(self):
        self.state = 'change'
        for service in self:
            
                self.env['service.history'].create({
                    'service_id': service.id,
                    'user': self.env.user.id,
                    'time': fields.Datetime.now(),
                    'status': service.state,  
                })
                self .env['service.comment'].create({
                    'service_id': service.id,
                    'comment' : service.comments or 'CHANGED',
                    'comment_date_and_time' : fields.Datetime.now(),
                    'comment_user': self.env.user.id,
                    'comment_status' : service.state,
                
        })
        return True

    def action_custom_cancel_service(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'history_back',
        }

    def action_create_enquiry(self):
        # Create a new enquiry linked to the current service
        new_enquiry = self.env['aaa.enquiry'].create({
            'name': 'New Enquiry',  # Default or dynamic name for the enquiry
            'enq_id': self.id,  # Link the enquiry to the current service
            'date': fields.Datetime.now(),
            'mobile':self.member_contact_no,
            'email': self.email,
            'comment': self.state or 'Enquiry',
            'created_by': self.env.user.id
                    })
        view_id = self.env.ref('customer.call_center_enquiry_view_form').id
        return{
            'name': 'Service Policy',
            'type': 'ir.actions.act_window',
            'res_model':'aaa.enquiry',
            'view_mode':'form',
            'view_id': view_id,
            #'target': 'new',
            'context': {
                'default_customer_id': self.customer_id.id,
                'default_member_id': self.member_id.id,
            }  
        }
    
    def action_waive_off(self):
        # self.waive_off = True
        pass

    def action_new(self):
        pass

    def history(self):
        pass


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
    service_id = fields.Many2one('aaa.service', string="Service")

class AaaServiceAddon(models.Model):
    _name = 'aaa.service.addon'
    _description = 'Additional Service'

    service_id = fields.Many2one('aaa.service', string='Service')
    product_id = fields.Many2one('product.template', string="Service",domain=[('bundle_product', '=', False)])
    provider_from_location_id = fields.Many2one('location.internal', string="From Location")
    provider_to_location_id = fields.Many2one('location.internal', string="To Location")
    description = fields.Char(' Description')
    price_subtotal = fields.Float('Price Subtotal')
