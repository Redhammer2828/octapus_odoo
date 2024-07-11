from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

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
        ('discard', 'Discarded')
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
    rating_user_id = fields.Many2one('res.users', string="Rating User")
    new_service_id = fields.Many2one('product.template', string="New Service")
    main_product_ids = fields.Many2many('product.template', string="Main Products")
    cancelled_service_id = fields.Many2one('aaa.service', string="Cancelled Service", readonly=True)
    acc_payment_id = fields.Many2one('account.payment', string="Payment")
    provider_id = fields.Many2one('res.partner', string="Provider") #  domain="[('supplier', '=', True)]"
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
    provider_contact = fields.Char(string="Provider Contact")
    provider_rate = fields.Float(string="Provider Rate")
    provider_rate_invisible = fields.Float(string="Provider Rate Invisible")
    avg_vendor_rating = fields.Float(string="Average Vendor Rating")
    company_vehicle = fields.Boolean(string="Company Vehicle")
   
   
    # driver_job_id = fields.Many2one('hr.job', string="Driver Job ID")
    # driver_id = fields.Many2one('hr.employee', string="Driver", domain="[('job_id', '=', driver_job_id)]")
    
    # vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    # vehicle = fields.Char(string="Vehicle")
    
    driver_name = fields.Char(string="Driver Name")
    driver_num = fields.Char(string="Driver Number")
    credit_proforma_number = fields.Char(string="Credit Proforma Number")
    vendor_rating = fields.Float(string="Vendor Rating")
    
    
    completion_time = fields.Datetime(string="Completion Time")
    
    
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
       
        return service

    def action_initiate_service(self):
        self.state = 'initiate'

    def action_dispatch_service(self):
        # Search for the member in res.partner
        # member = self.env['res.partner'].search([('id', '=', self.member_id.id)], limit=1)
        
        # print("Services:",member.service_ids)
        # if not member:
        #     raise ValidationError(_("Member not found."))

        # # Get the service_ids from the member
        # service_ids = member.service_ids

        # # Check if the selected product_id is present in the service_ids
        # if self.product_id.id not in service_ids.ids:
        #     raise ValidationError(_("This selected service is not listed in selected package"))
        # ------------------------------------------------------------------------------
        # If validation passes, update the state to 'dispatch'
        # self.state = 'dispatch'
        # ---------------------------------------------------------------------
        # Fetch member_id from aaa.service
        service_record = self.env['aaa.service'].search([('id', '=', self.id)], limit=1)
        print("Member:",service_record)
        member_id = service_record.member_id.id
        print("Member ID:",member_id)
        if not member_id:
            raise ValidationError(_("Member not found in the service record."))
        
        # Get all service lines for the member
        if self.member_type == 'policy':
            service_lines = self.env['aaa.service'].search([('member_id', '=', member_id)])
            print("Service Lines:",service_lines)
            service_lines_info = [(line.product_id.id, line.create_date) for line in service_lines]
            print("Service Lines Info:",service_lines_info)

            # Get product_template_id from res.partner
            member = self.env['res.partner'].browse(member_id)
            product_template_id = member.product_template_id.id
            if not product_template_id:
                raise ValidationError(_("Package not found for the member."))
            
            # Match product_template_id with product_template_id in product.package.service
            package_services = self.env['product.package.service'].search([('product_template_id', '=', product_template_id)])
            print("Packages Services:",package_services)

            # Check each service line against the package service validity
            for package_service in package_services:
                product_id = package_service.product_id.id
                validity_days = package_service.quantity

                for service_product_id, create_date in service_lines_info:
                    if service_product_id == product_id:
                        service_date = fields.Datetime.from_string(create_date)
                        current_date = fields.Datetime.now()
                        days_difference = (current_date - service_date).days

                        if validity_days == 1 and days_difference < 1:
                            raise ValidationError(_("This service can only be used once per day."))
                        elif days_difference < validity_days:
                            raise ValidationError(_("Service limit reached for this period."))
        else:
        # If validation passes, update the state to 'dispatch'
            self.state = 'dispatch'
            self.message_post(body=_("Service dispatched successfully."))
            for service in self:
                self.env['service.history'].create({
                        'service_id': service.id,
                        'user': self.env.user.id,
                        'time': fields.Datetime.now(),
                        'status': service.state,  
                    })
                return True

    def action_schedule_service_check(self):
        self.schedule_service_check = True

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
