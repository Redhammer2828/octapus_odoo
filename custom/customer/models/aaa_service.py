from odoo import api, fields, models, _
from odoo.exceptions import ValidationError , UserError
import datetime
from datetime import timedelta,datetime
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
        ('change', 'Changed' ),
        ('approved','Approved'),
        ('requested','Requeted')
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
    membership_num = fields.Char('Membership Number')
    created_by = fields.Many2one('res.users', string="Agent", default=lambda self: self.env.user, readonly=True)
    
    vehicle_type = fields.Char('Vehicle Type')   #Chaged to char
    vehicle_model = fields.Char('Vehicle Model')  #Changed to char
    
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
    quantity = fields.Float(string="Quantity")
    service_based = fields.Selection(related='product_id.service_based', store=True, readonly=True)
    
    old_membership_number = fields.Char('Old Membership Number')
    
    service_time = fields.Datetime(string="Service Date", default=fields.Datetime.now)
    cash_collected_hidden = fields.Boolean(string="Cash Collected Hidden")
    cash_collected = fields.Float(string="Cash Collected")     
    
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

    # # -----------LOCATION- API TESTINGs--------------------------------------------------
    
    search_query = fields.Char(string='Search Locations')
    search_results = fields.Many2many('location.suggestion', string='Search Results', compute='_fetch_location_suggestions')
    selected_from_location = fields.Many2one('location.suggestion', string='From Location')
    selected_to_location = fields.Many2one('location.suggestion', string='To Location')
    from_location = fields.Many2one('aaa.location', string='From Location') #For Data IMPORT as well as CREDIT SERVICE PRICE LIST
    to_location = fields.Many2one('aaa.location', string='To Location') #For Data IMPORT as well as CREDIT SERVICE PRICE LIST
    is_imported = fields.Boolean('Is Imported', default=False)
    amount = fields.Integer(string='Amount', compute='_compute_amount', store=True)  # Dynamically computed amount

    from_location_emirate = fields.Char(string='Emirate', compute='_compute_emirates', store=True)
    to_location_emirate = fields.Char(string='Emirate', compute='_compute_emirates', store=True)
    quantity_with_days = fields.Char(string='Quantity with Days') 
    orgin_no = fields.Char('Orgin')

    service_quantity = fields.Float(string="Service Quantity", default="1.00")

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

    @api.onchange('date_time_from', 'date_time_to')
    def _onchange_from_to_date(self):
        for record in self:
            if record.date_time_from and record.date_time_to:
                delta = record.date_time_to - record.date_time_from
                record.quantity = delta.days
                record.quantity_with_days = f"{delta.days} Days"  # Set quantity_with_days here
            else:
                record.quantity = 0
                record.quantity_with_days = "0 Days"
   
    @api.depends('selected_from_location', 'selected_to_location')
    def _compute_amount(self):
        for record in self:
            if record.selected_from_location and record.selected_to_location:
                # Fetch lat/long from selected locations
                from_lat = record.selected_from_location.latitude
                from_lon = record.selected_from_location.longitude
                to_lat = record.selected_to_location.latitude
                to_lon = record.selected_to_location.longitude

                print("FROM LATITUDE", from_lat)
                print("FROM LONGITUDE", from_lon)
                print("TO LATITUDE ", to_lat)
                print("TO LONGITUDE ", to_lon)

                # Prepare API payload
                payload = {
                    "merchant_longitude": from_lon,
                    "merchant_latitude": from_lat,
                    "customer_longitude": to_lon,
                    "customer_latitude": to_lat
                }

                # API URL
                url = 'https://gioapi-gy-dev.kirkos.ae/carhire-order/order/service/deliveryfee/aaa/delivery-fee'
                
                try:
                    # Make the POST request
                    headers = {'Content-Type': 'application/json'}
                    response = requests.post(url, headers=headers, data=json.dumps(payload))

                    # Check if the request was successful
                    if response.status_code == 200:
                        print("API Response:", response.json())  # Print JSON response
                    else:
                        print(f"Failed to fetch data. Status code: {response.status_code}, Response: {response.text}")
                
                except Exception as e:
                    print(f"Error occurred while making the API request: {str(e)}")


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
        
    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        context = self.env.context
        for record in self:
            if not record.customer_id:
                # Clear fields if customer_id is empty
                record.sequence_id = False
                record.member_id = False
                continue
 
            member_type = context.get('default_member_type')
            member_type_conditions = ['credit', 'adhoc']
            type_conditions = ['non_cash', 'cash']
 
            # Ensure the context has a valid combination of 'default_member_type' and 'default_type'
            if (
                member_type in member_type_conditions
                and context.get('default_type') in type_conditions
            ):
                # Fetch the sequence associated with the customer_id
                sequence = self.env['partner.category'].search(
                    [
                        ('partner_id', '=', record.customer_id.id),
                        ('member_type', '=', member_type),
                    ],
                    limit=1,
                )
                if sequence:
                    record.sequence_id = sequence.id
                    # Update member_id based on the sequence's default_member
                    record.member_id = sequence.default_member.id if sequence.default_member else False
                else:
                    # If no sequence is found, directly fetch member_id
                    record.sequence_id = False
                    member = self.env['res.partner'].search(
                        [
                            ('parent_customer_id', '=', record.customer_id.id),
                            ('member_type', '=', member_type),
                        ],
                        limit=1,
                    )
                    record.member_id = member.id if member else False
 
    @api.onchange('sequence_id')
    def _onchange_sequence_id(self):
        for record in self:
            if record.sequence_id:
                # Update member_id based on the selected sequence_id
                sequence = self.env['partner.category'].browse(record.sequence_id.id)
                record.member_id = sequence.default_member.id if sequence.default_member else False
            else:
                # Clear member_id if sequence_id is cleared
                record.member_id = False

    @api.model
    def create(self, vals):
        # Ensure the name field is set using a specific format if not provided
        if vals.get('name', _('New')) == _('New'):
            # Get the current month and year for formatting
            current_month = datetime.now().strftime('%m')  # 2-digit month
            current_year = datetime.now().strftime('%Y')   # 4-digit year
 
            # Get the next sequence number (without the prefix)
            sequence_number = self.env['ir.sequence'].next_by_code('aaa.service')
 
            # Extract only the numeric part of the sequence number
            numeric_part = sequence_number.split('-')[-1]  # Get the part after the last dash
            sequence_number = f"{int(numeric_part):08d}"  # Ensure it's zero-padded to 8 digits
            # Format the service name
            vals['name'] = f"SER/{current_month}/{current_year}/{sequence_number}"
 
        # Create the aaa.service record
        service = super(AAAService, self).create(vals)
 
        # Create the service.history record
        self.env['service.history'].create({
            'service_id': service.id,
            'user': self.env.user.id,
            'time': fields.Datetime.now(),
            'status': service.state,
        })
        return service  

    def write(self, vals):
        """Override the write method to ensure comments are saved every time the comments field is updated"""
        if 'comments' in vals and vals['comments']:
            # Ensure the comment is appended
            existing_comments = self.comments or ""
            new_comment = f"{existing_comments}\n{vals['comments']}" if existing_comments else vals['comments']
           
            # Update the comments field in the service model
            vals['comments'] = new_comment
 
            # Create the service.comment record for each new comment
            self.env['service.comment'].create({
                'service_id': self.id,
                'comment': vals['comments'],
                'comment_date_and_time': fields.Datetime.now(),
                'comment_user': self.env.user.id,
                'comment_status': self.state,
            })
 
            # Clear the comments field after saving
            vals['comments'] = ''  # Clear the comment field
 
        # Call the super method to handle the actual update of the service
        return super(AAAService, self).write(vals)
    
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
   
        if self.service_based != 'location_duration':
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
           
       
        if self.service_based == 'location_duration':
            period_start = fields.Datetime.now() - timedelta(days=validity_period_days)
            print("START OF LOCATION DURATION SERVICE PERIOD:", period_start)
 
            total_days = 0
            # Fetch all services in the same category within the validity period
            member_services_in_category = self.env['aaa.service'].search([
                ('member_id', '=', self.member_id.id),
                ('product_id.categ_id', '=', parent_category_id),
                ('state', 'in', ['dispatch', 'start', 'reach', 'completed_by_driver', 'done']),
                ('date_time_to', '>=', period_start),
            ])
            print("MEMBER SERVICES IN CATEGORY:", member_services_in_category)
 
            # Calculate the total days accessed in the category
            for service in member_services_in_category:
                if service.service_based == 'location_duration' and service.date_time_to and service.date_time_from:
                    service_duration = (service.date_time_to - service.date_time_from).total_seconds() / (3600 * 24)
                    print("SERVICE DURATION FOR LOCATION DURATION SERVICE:", service_duration)
                    total_days += service_duration
                    print("TOTAL SERVICE DAYS ACCESSED:", total_days)
 
            # Calculate remaining days from the quantity limit
            remaining_days = quantity_limit - total_days
            print("REMAINING SERVICE DAYS ALLOWED:", remaining_days)
 
            # Update the 'quantity' field with the remaining days
            # self.quantity = remaining_days
            # print("UPDATED QUANTITY FIELD WITH REMAINING DAYS:", self.quantity)
 
            # If remaining_days is less than or equal to 0, trigger the cash service wizard
            if remaining_days <= 0:
                print("SERVICE LIMIT EXCEEDED - TRIGGERING CASH WIZARD")
                return False
 
            # Check if the new service duration exceeds the remaining days
            new_service_duration = (self.date_time_to - self.date_time_from).total_seconds() / (3600 * 24)
            if new_service_duration > remaining_days:
                raise ValidationError(
                    _("The service can only be accessed for the remaining %d days. Please adjust the service duration.") % remaining_days
                )
 
            # Ensure that even if 24 hours have passed, the service is not dispatchable if the total service days exceed the limit
            # if not self._is_service_accessible_in_24_hours(parent_category_id):
            #     print("SERVICE DISPATCHED WITHIN 24 HOURS - BLOCKING SERVICE DISPATCH")
            #     raise ValidationError(
            #         _("A service of type 'location_duration' can only be initiated after 24 hours of the last dispatch. Remaining quantity (days): %d") % remaining_days
            #     )
 
             # Step 2: Update and persist `quantity_with_days`
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
        recent_services = self.env['aaa.service'].search_count([
            ('member_id', '=', self.member_id.id),
            ('product_id.categ_id', '=', parent_category_id),
            # ('state', '=', 'dispatch'),
            ('state', 'in', ['dispatch','start', 'reach', 'completed_by_driver', 'done']),
            ('create_date', '>=', last_dispatch_time),
        ])
        return recent_services == 0
 
    def _count_services_in_category(self, parent_category_id):
        return self.env['aaa.service'].search_count([
            ('member_id', '=', self.member_id.id),
            ('product_id.categ_id', '=', parent_category_id),
            # ('state', '=', 'dispatch'),
            ('state', 'in', ['dispatch','start', 'reach','completed_by_driver', 'done']),
        ])
 
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
        self.state = 'dispatch'
        self.message_post(body=_("Service dispatched successfully."))
        self.env['service.history'].create({
            'service_id': self.id,
            'user': self.env.user.id,
            'time': fields.Datetime.now(),
            'status': self.state,
        })
 
     
        for service in self:
            # Define the comment content based on whether a manual comment is provided
            comment_content = service.comments or 'DISPATCHED'
           
            # Create the service.comment record
            self.env['service.comment'].create({
                'service_id': service.id,
                'comment': comment_content,
                'comment_date_and_time': fields.Datetime.now(),
                'comment_user': self.env.user.id,
                'comment_status': service.state,
            })
 
            # Clear the comments field if it was manually provided
            if service.comments:
                service.comments = False  # Clear the comments field
 
        return True
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
        comment_content = service.comments or 'START'
 
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
 
        return True
    
    def action_completed_rac(self):
        #pass
        self.state = 'completed_by_driver'
        for service in self:
           
                self.env['service.history'].create({
                    'service_id': service.id,
                    'user': self.env.user.id,
                    'time': fields.Datetime.now(),
                    'status': service.state,  
                })
 
        comment_content = service.comments or 'COMPLETED BY DRIVER'
 
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
 
        comment_content = service.comments or 'COMPLETED'
 
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
                'status': 'cancel',  # Explicitly set the status
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
           
                self.env['service.history'].create({
                    'service_id': service.id,
                    'user': self.env.user.id,
                    'time': fields.Datetime.now(),
                    'status': service.state,  
                })
                comment_content = service.comments or 'CHANGED'
 
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
 
        return True

    def action_custom_cancel_service(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'history_back',
        }

    def action_create_enquiry(self):
        # Create a new enquiry record linked to the current service
        new_enquiry = self.env['aaa.enquiry'].create({
            # 'name': self.name,
            'customer_id': self.customer_id.id,
            'member_id': self.member_id.id,
            'service_id': self.product_id.id,
            'membership': self.member_type,
            'mem_name': self.member_id.name,
            'vehicle_chasis_no': self.vehicle_chasis_no,
            'vehicle_plate_no': self.vehicle_plate,
            'policy_no': self.policy_no,
            'enq_id': self.id,  # Link the enquiry to the current service
            'date': fields.Datetime.now(),
            'mobile': self.member_contact_no,
            'email': self.email,
            'comment': self.comments or 'Enquiry',
            'created_by': self.env.user.id,
            'enquiry': self.comments,
            'enquiry_type_id': self.env['enquiry.config'].search([], limit=1).id,
            'enquiries_id': self.env['enquiry.subtype'].search([], limit=1).id,
            'complaint_type_id': self.env['complaint.config'].search([], limit=1).id,
            'complaints_id': self.env['complaint.subtype'].search([], limit=1).id,
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
                'default_enq_cm_id': new_enquiry.id,
                'default_customer_id': self.customer_id.id,
                'default_member_id': self.member_id.id,
                'default_service_id': self.product_id.id,
                'default_mem_name': self.member_id.name,
                'default_membership': self.member_type,
                'default_mobile': self.member_contact_no,
                'default_comment': self.comments,
                'default_vehicle_chasis_no': self.vehicle_chasis_no,
                'default_vehicle_plate_no': self.vehicle_plate,
                'default_policy_no': self.policy_no,
                'default_email': self.email,
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
        new_service = False  # Initialize variable to avoid unbound error in case of multiple records
        for service in self:
            # Fetch the previous service's name field, which is the sequence number
            previous_service_sequence = service.name  # Assuming 'name' contains the sequence number
            print("PREVIOUS SERVICE SEQUENCE NO:", previous_service_sequence)
            # Debugging: Ensure the service object is correct
            print("SERVICE ID:", service.id)
            # Try creating the new service record
            try:
                new_service = self.env['aaa.service'].create({
                    'state': 'initiate',  # Set the state of the new service to 'initiate'
                    'orgin_no': previous_service_sequence,  # Copy the name (sequence number) to the origin_no field
                    'customer_id': service.customer_id.id,  # Copy the customer ID
                    'sequence_id': service.sequence_id.id,
                    'member_id': service.member_id.id,
                    'vehicle_type': service.vehicle_type,
                    'vehicle_model': service.vehicle_model,
                    'vehicle_plate': service.vehicle_plate,
                    'vehicle_chasis_no': service.vehicle_chasis_no,
                    'policy_no': service.policy_no,
                })
                # Debugging: Ensure the new service is created
                print("NEW SERVICE ID:", new_service.id)
            except Exception as e:
                print("ERROR CREATING NEW SERVICE:", str(e))
                raise UserError(_("Failed to create a new service: %s") % str(e))  # Raise an error with a meaningful message
        # Ensure the new service was created
        if not new_service:
            raise UserError(_("No new service record was created."))
        # Ensure the view_id reference is correct
        try:
            view_id = self.env.ref('customer.call_center_service_form').id  # Make sure this reference is correct
            print("VIEW ID:", view_id)
        except Exception as e:
            print("ERROR FETCHING VIEW ID:", str(e))
            raise UserError(_("Failed to fetch the form view: %s") % str(e))
        # Open the newly created service form in edit mode (editable)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'aaa.service',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': new_service.id,  # Pass the ID of the newly created service record
            'view_id': view_id,  # Ensure correct view reference
            'target': 'current',  # Open in the current window
            'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}},  # Make sure the form is in edit mode
        }
    
    def action_request_service(self):
        self.state='requested'
        for service in self:
           
                self.env['service.history'].create({
                    'service_id': service.id,
                    'user': self.env.user.id,
                    'time': fields.Datetime.now(),
                    'status': service.state,  
                })
                comment_content = service.comments or 'REQUESTED'
 
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
 
        return True

    def action_approve_service(self):
        self.state='initiate'
        for service in self:
            self.env['service.history'].create({
                'service_id': service.id,
                'user': self.env.user.id,
                'time': fields.Datetime.now(),
                'status': service.state,  
                })
            self .env['service.comment'].create({
                'service_id': service.id,
                'comment' : service.comments or 'APPROVED',
                'comment_date_and_time' : fields.Datetime.now(),
                'comment_user': self.env.user.id,
                'comment_status' : service.state,
        })
 

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
    product_id = fields.Many2one(
        'product.template',
        string="Service",
        domain=[('name', 'in', ['GATE PASS', 'KEY COLLECTION CHARGES', 'MECHANICAL ASSISTANCE', 'WAITING CHARGES'])]
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