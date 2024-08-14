from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import datetime
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
        ('inprogress', 'In Progress'),
        ('start', 'Start'),
        ('reach', 'Reach'),
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
    
    vehicle_type_id = fields.Many2one('member.vehicle.type', string="Vehicle Type")
    vehicle_model_id = fields.Many2one('member.vehicle.model', string="Vehicle Model")
    
    product_id = fields.Many2one('product.template', string="Service",domain=[('bundle_product', '=', False)])
    # vehicle_emirate_id = fields.Many2one('emirate', string="Vehicle Emirate ID")
    provider_from_location_id = fields.Many2one('location.internal', string="From Location")
    provider_to_location_id = fields.Many2one('location.internal', string="To Location")
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure")
    # rating_user_id = fields.Many2one('res.users', string="Rating User")
    new_service_id = fields.Many2one('product.template', string="New Service")
    main_product_ids = fields.Many2many('product.template', string="Main Products")
    cancelled_service_id = fields.Many2one('aaa.service', string="Cancelled Service", readonly=True)
    acc_payment_id = fields.Many2one('account.payment', string="Payment")
   
   
    # PROVIDER-------------------------------------------------------------------------------------------------------------
    provider_id = fields.Many2one('res.partner', string="Provider") #  domain="[('supplier', '=', True)]"
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
    
    datetime_from = fields.Datetime(string="Datetime From")
    datetime_to = fields.Datetime(string="Datetime To")
    quantity = fields.Float(string="Quantity")
    
    
    service_time = fields.Datetime(string="Service Time")
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
   
   
    # driver_job_id = fields.Many2one('hr.job', string="Driver Job ID")
    # driver_id = fields.Many2one('hr.employee', string="Driver", domain="[('job_id', '=', driver_job_id)]")
    
    # vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    # vehicle = fields.Char(string="Vehicle")
    
    driver_name = fields.Char(string="Driver Name")
    driver_num = fields.Char(string="Driver Number")
    # credit_proforma_number = fields.Char(string="Credit Proforma Number")
    # vendor_rating = fields.Float(string="Vendor Rating")
    
    
    completion_time = fields.Datetime(string="Completion Time")
    member_activate_date = fields.Date('Member Activate Date')
    member_expiry_date = fields.Date('Member Expiry Date')
    
    
    # @api.onchange('customer_id')
    # def _onchange_customer_id(self):
    #     for record in self:
    #         if record.customer_id:
    #             # Search for the sequence that matches the criteria
    #             sequence = self.env['partner.category'].search([
    #                 ('partner_id', '=', record.customer_id.id),
    #                 ('member_type', '=', 'credit')
    #             ], limit=1)
                
    #             # Set the sequence_id to the found sequence
    #             record.sequence_id = sequence.id if sequence else False
                
    #             # Search for the member that matches the criteria
    #             member = self.env['res.partner'].search([
    #                 ('parent_customer_id', '=', record.customer_id.id),
    #                 ('member_type', '=', 'credit')
    #             ], limit=1)
    #             print("MEMBERRRR",member)
    #             # Set the member_id to the found member
    #             record.member_id = member.id if member else False

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        context = self.env.context
        # Check if the specific context keys match the expected values
        if context.get('default_member_type') == 'credit' and context.get('default_type') == 'non_cash':
            for record in self:
                if record.customer_id:
                    # Search for the sequence that matches the criteria
                    sequence = self.env['partner.category'].search([
                        ('partner_id', '=', record.customer_id.id),
                        ('member_type', '=', 'credit')
                    ], limit=1)
                    
                    # Set the sequence_id to the found sequence
                    record.sequence_id = sequence.id if sequence else False
                    
                    # Search for the member that matches the criteria
                    member = self.env['res.partner'].search([
                        ('parent_customer_id', '=', record.customer_id.id),
                        ('member_type', '=', 'credit')
                    ], limit=1)
                    print("MEMBERRRR", member)
                    # Set the member_id to the found member
                    record.member_id = member.id if member else False

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
        url = "https://gioapi-gy-dev.livelocal.delivery/aaa-customer/whatsapp/whatsapp-Notification"
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

    # def action_dispatch_service(self):
    #     # Ensure we're working with a single record
    #     self.ensure_one()
        
    #     # ----------------------------------------------------------------------------
    #     for record in self:
    #         if not record.name:
    #             if not record.service_sequence:
    #                 date_str = datetime.today().strftime('%Y%m%d')
    #                 sequence = self.env['ir.sequence'].next_by_code('aaa.service')
    #                 record.name = f'SERV-{date_str}-{sequence[-4:]}'
    #     service_record = self
    #     # -----------------------------------------------------------------------------

    #     member_id = service_record.member_id.id
    #     print("ID of Service that User is in:", service_record.id)
    #     print("ID of MEMBER From SERVICE REC:", member_id)

    #     if not member_id:
    #         raise ValidationError(_("Member not found in the service record."))

    #     if self.member_type == 'policy':
    #         # Get all service lines for the member
    #         service_lines = self.env['aaa.service'].search([
    #             ('member_id', '=', member_id),
    #             ('state', '!=', 'initiate'),
    #             ('member_type', '=', 'policy')
    #         ])
    #         print("All services Taken by Member, Service Lines:", service_lines.ids)
    #         service_lines_info = [(line.product_id.id, line.create_date) for line in service_lines]
    #         print("Service Lines Info:", service_lines_info)

    #         # Get product_template_id from res.partner
    #         member = self.env['res.partner'].browse(member_id)
    #         product_template_id = member.product_template_id.id
    #         print("Package ID:", product_template_id)

    #         if not product_template_id:
    #             raise ValidationError(_("Package not found for the member."))

    #         # Match product_template_id with product_template_id in product.package.service
    #         package_services = self.env['product.package.service'].search([
    #             ('product_template_id', '=', product_template_id)
    #         ])
    #         package_service_product_ids = package_services.mapped('product_id.id')
    #         print("Packages Services Product IDs:", package_service_product_ids)

    #         service_product_id = self.product_id.id  # Assuming `self.product_id` refers to the current service's product

    #          # -------------------------------------------------------------------------------------------------- 
    #         order_number = self.name
    #         status = self.state
    #         phone_number = self.member_contact_no
    #         vehicle_chasis_no = self.vehicle_chasis_no  # Corrected field name

    #         self.action_order_response(order_number, status, phone_number, vehicle_chasis_no)
    #         print(f"checking value of order:{order_number},{status}, {phone_number}, {vehicle_chasis_no}")
    #     # -------------------------------------------------------------------------------------------------- 
    #         if service_product_id not in package_service_product_ids:
    #             # The service is not part of the package; trigger the wizard
    #             print("SERVICE NOT FOUND IN PACKAGE - Triggering Wizard")
    #             return {
    #                 'name': _('Convert to Cash or Credit Service'),
    #                 'type': 'ir.actions.act_window',
    #                 'res_model': 'service.dispatch.wizard',
    #                 'view_mode': 'form',
    #                 'view_id': self.env.ref('customer.view_service_dispatch_wizard_form').id,
    #                 'target': 'new',
    #                 'context': {
    #                     'default_service_id': self.id,
    #                 },
    #             }

    #         if not service_lines_info:
    #             # No existing services found. Proceeding with dispatch.
    #             print("No existing services found. Proceeding with dispatch.")
    #             self.state = 'dispatch'
    #             self.message_post(body=_("Service dispatched successfully."))
    #             self.env['service.history'].create({
    #                 'service_id': self.id,
    #                 'user': self.env.user.id,
    #                 'time': fields.Datetime.now(),
    #                 'status': self.state,
    #             })

    #             return True
    #         else:
    #             # Case: Existing services - check validity against the package
    #             service_found = False
    #             validation_error_message = None

    #             # Check each service line against the package service validity
    #             for service_product_id, create_date in service_lines_info:
    #                 print("Checking SERVICE PRODUCT_ID:", service_product_id)
    #                 print("Created Date:", create_date)

    #                 if service_product_id in package_service_product_ids:
    #                     service_found = True
    #                     # Find the corresponding package service to get validity_days
    #                     package_service = package_services.filtered(lambda s: s.product_id.id == service_product_id)
    #                     if package_service:
    #                         validity_days = package_service.quantity
    #                         print("Package service validity:", validity_days)
 
    #                         service_date = fields.Datetime.from_string(create_date)
    #                         print("SERVICE DATE:", service_date)
    #                         current_date = fields.Datetime.now()
    #                         print("CURRENT DATE:", current_date)
    #                         days_difference = (current_date - service_date).days
    #                         print("Days Difference:", days_difference)
 
    #                         if validity_days == 1 and days_difference < 1:
    #                             # validation_error_message = _("This service can only be used once per day.")
    #                             print("This service can only be used once per day.")
    #                         elif days_difference < validity_days:
    #                             # validation_error_message = _("Service limit reached for this period.")
    #                                print("SERVICE LIMIT REACHED FOR THIS PERIOD - Triggering Wizard")
    #                                return {
    #                                     'name': _('Convert to Cash'),
    #                                     'type': 'ir.actions.act_window',
    #                                     'res_model': 'service.cash.wizard',
    #                                     'view_mode': 'form',
    #                                     'view_id': self.env.ref('customer.view_service_cash_wizard_form').id,
    #                                     'target': 'new',
    #                                     'context': {
    #                                         'default_service_id': self.id,
    #                                     },
    #                                 }
    #                         else:
    #                             # Valid service found; no need to trigger wizard
    #                             print("Valid service found. Skipping wizard.")
    #                             break
 
    #                         if validity_days == 365 and days_difference < 365:
    #                             # validation_error_message = _("This service can only be used once per year.")
    #                             print("This service can only be used once per year.")
    #                         elif days_difference < validity_days:
    #                             # validation_error_message = _("Service limit reached for this period.")
    #                             print("Service limit reached for this period.")
    #                             return {
    #                                     'name': _('Convert to Cash'),
    #                                     'type': 'ir.actions.act_window',
    #                                     'res_model': 'service.cash.wizard',
    #                                     'view_mode': 'form',
    #                                     'view_id': self.env.ref('customer.view_service_cash_wizard_form').id,
    #                                     'target': 'new',
    #                                     'context': {
    #                                         'default_service_id': self.id,
    #                                     },
    #                                 }
    #                         else:
    #                             # Valid service found; no need to trigger wizard
    #                             print("Valid service found. Skipping wizard.")
    #                             break
 
    #                     if validation_error_message:
    #                         raise ValidationError(validation_error_message)
        
    #     # -------------------------------------------------------------------------------------------------- 
    #     order_number = self.name
    #     status = self.state
    #     phone_number = self.member_contact_no
    #     vehicle_chasis_no = self.vehicle_chasis_no  # Corrected field name

    #     self.action_order_response(order_number, status, phone_number, vehicle_chasis_no)
    #     print(f"checking value of order:{order_number},{status}, {phone_number}, {vehicle_chasis_no}")
    #     # -------------------------------------------------------------------------------------------------- 


    #     self.state = 'dispatch'
    #     print("DISPATCHEDDDD",self.state)
    #     self.requested_date = fields.Datetime.now()
    #     self.message_post(body=_("Service dispatched successfully."))
    #     self.env['service.history'].create({
    #         'service_id': self.id,
    #         'user': self.env.user.id,
    #         'time': fields.Datetime.now(),
    #         'status': self.state,
    #     })
    #     return True

    def action_dispatch_service(self):
        for record in self:
            if not record.name:
                if not record.service_sequence:
                    date_str = datetime.today().strftime('%Y%m%d')
                    sequence = self.env['ir.sequence'].next_by_code('aaa.service')
                    record.name = f'SERV-{date_str}-{sequence[-4:]}'
                   
        self.ensure_one()
        self.schedule_date_time = fields.Datetime.now()
 
        service_record = self
        member_id = service_record.member_id.id
 
        if not member_id:
            raise ValidationError(_("Member not found in the service record."))
 
        if self.member_type == 'policy':
            service_lines = self.env['aaa.service'].search([
                ('member_id', '=', member_id),
                ('state', '!=', 'initiate'),
                ('member_type', '=', 'policy')
            ])
 
            service_lines_info = [(line.product_id.id, line.create_date) for line in service_lines]
 
            member = self.env['res.partner'].browse(member_id)
            product_template_id = member.product_template_id.id
            policy_period = (member.member_expiry_date - member.member_activate_date).days
 
            if not product_template_id:
                raise ValidationError(_("Package not found for the member."))
 
            package_services = self.env['product.package.service'].search([
                ('product_template_id', '=', product_template_id)
            ])
           
            package_service_product_ids = package_services.mapped('product_id.id')
 
            service_product_id = self.product_id.id
 
            if service_product_id not in package_service_product_ids:
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
 
            if not service_lines_info:
                self.state = 'dispatch'
                self.message_post(body=_("Service dispatched successfully."))
                self.env['service.history'].create({
                    'service_id': self.id,
                    'user': self.env.user.id,
                    'time': fields.Datetime.now(),
                    'status': self.state,
                })
                return True
            else:
                service_found = False
                validation_error_message = None
 
                # Fetching the parent category (categ_id) from product.template
                package_category = self.product_id.categ_id
                parent_package_id = package_category.id
 
                # Searching for services under the specific categ_id in product.category.limit
                category_services = self.env['product.category.limit'].search([
                    ('category_id', '=', parent_package_id)
                ])
 
                # List the services under this category taken by the member
                for service_product_id, create_date in service_lines_info:
                    if service_product_id in package_service_product_ids:
                        service_found = True
                       
                        matching_service = category_services.filtered(lambda s: s.product_id.id == service_product_id)
                       
                        if matching_service:
                            quantity = matching_service.quantity
                            validity_hours = matching_service.hours
 
                            current_time = fields.Datetime.now()
                            service_time = fields.Datetime.from_string(create_date)
                            hours_difference = (current_time - service_time).total_seconds() / 3600
 
                            if validity_hours and hours_difference < validity_hours:
                                validation_error_message = _("This service can only be used once every %d hours." % validity_hours)
                                break
                            elif hours_difference < 24 and quantity == 1:
                                validation_error_message = _("This service can only be used once per day.")
                                break
                            elif hours_difference < 8760 and quantity == 365:
                                validation_error_message = _("This service can only be used once per year.")
                                break
 
                if validation_error_message:
                    raise ValidationError(validation_error_message)
 
        self.state = 'dispatch'
        self.message_post(body=_("Service dispatched successfully."))
        self.env['service.history'].create({
            'service_id': self.id,
            'user': self.env.user.id,
            'time': fields.Datetime.now(),
            'status': self.state,
        })
        return True

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

    def action_inprogress_service(self):
            self.state = 'inprogress'
            for service in self:
            
                self.env['service.history'].create({
                    'service_id': service.id,
                    'user': self.env.user.id,
                    'time': fields.Datetime.now(),
                    'status': service.state,  
                })
            return True

    def action_start_service(self):
        self.state = 'start'

    def action_reach_service(self):
        self.state = 'reach'

    def action_done_service(self):
        self.state = 'done'

    def cash_service(self):
        self.type = 'cash'

    def convert_to_non_cash(self):
        self.type = 'non_cash'

    def action_cancel_service(self):
        self.state = 'cancel'

    def action_discard(self):
        self.state = 'discard'
    
    def action_change(self):
        self.state = 'change'

    def action_custom_cancel_service(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'history_back',
        }

    def action_create_enquiry(self):
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
