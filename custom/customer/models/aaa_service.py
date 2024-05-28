from odoo import fields,models

class ServiceCredit(models.Model):
    _name = 'aaa.service'
    _description = "Service Credit"

    # # General Information
    # category_id = fields.Many2one('res.partner', string='category')
    # credit_customer_co = fields.Char('Credit CUstomer Co')
    # sequence_id = fields.Many2one('partner.category', string='Customer Category')
    # member_id = fields.Many2one('res.partner', string='Member')
    # member_contact_no = fields.Char('Mobile Number')
    # email = fields.Char('Email')
    # driving_license = fields.Char('Driving License')
    # requested_date = fields.Datetime('Service Date')  #Read-only
    # claim_number = fields.Char('Claim Number')
    # smarto = fields.Boolean('Smart-Tow')
    # comments = fields.Text('Comments')

    # # Vehicle Details
    # vehicle_type_id = fields.Many2one('member.vehicle.type', string='Vehicle Type')
    # vehicle_model_id = fields.Many2one('member.vehicle.model', string='Vehicle Model')
    # vehicle_plate = fields.Char('Vehicle Plate')
    # vehicle_chasis_no = fields.Char('Vehicle Chasis No')
    # vehicle_emirate_id = fields.Many2one('res.country.state', string='Vehicle Emirate')
    # policy_no = fields.Char('Policy No')
    # member_activate_date = fields.Date('Member Activate Date')
    # member_expiry_date = fields.Date('Member Expiry Date')

    # # Service Details
    # product_id = fields.Many2one('product.template', string='product')

    # # aaaSERVICE addons

    # # Page
    # service_history_ids = fields.One2many('comodel_name', 'inverse_field_name', string='Service History')
# --------------------------------------------------------------------------------------
    # STATUS BAR
    name = fields.Char(string='Number', readonly=True)
    
    type = fields.Selection([
        ('cash', 'CASH'),
        ('non_cash', 'NON-CASH'),
    ], string='Service Type', required=True, readonly=True)
    
    member_type = fields.Selection([        
        ('policy', 'POLICY'),
        ('credit', 'CREDIT'),
        ('adhoc', 'AD-HOC'),], string='Member Type', readonly=True)
    created_by = fields.Many2one('res.users', string='Agent', readonly=True)
    
    # General Information--------------------------------------------------------------
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    credit_customer_co = fields.Char(string='Credit Customer CO')
    sequence_id = fields.Many2one('ir.sequence', string='Customer Category')
    member_id = fields.Many2one('res.partner', string='Member', required=True)
    member_contact_no = fields.Char(string='Mobile Number')
    email = fields.Char()
    driving_license = fields.Char(string='Driving License')
    schedule_date_time = fields.Datetime(string='Schedule Date Time', readonly=True)
    requested_date = fields.Datetime(string='Requested Date', required=True, readonly=True)
    schedule_service_check = fields.Boolean(string='Schedule Service Check', readonly=True)
    claim_number = fields.Char(string='Claim Number')
    smarto = fields.Boolean(string='Smarto')
    # doubt------------------------------------------------------------------------------
    smarto_id = fields.Many2one('smarto.model', string='Smarto ID')  

    comments = fields.Text(string='Comments')
    # Vehicle details
    vehicle_type_id = fields.Many2one('vehicle.type', string='Vehicle Type')
    vehicle_type = fields.Char(string='Vehicle Type')
    vehicle_model_id = fields.Many2one('vehicle.model', string='Vehicle Model')
    vehicle_model = fields.Char(string='Vehicle Model')
    vehicle_plate = fields.Char(string='Vehicle Plate')
    vehicle_chasis_no = fields.Char(string='Vehicle Chasis No')
    vehicle_emirate_id = fields.Many2one('res.partner', string='Vehicle Emirate')
    policy_no = fields.Char(string='Policy No')
    member_activate_date = fields.Datetime(string='Member Activate Date', readonly=True)
    member_expiry_date = fields.Datetime(string='Member Expiry Date', readonly=True)
    # Service details
    product_id = fields.Many2one('product.product', string='Service', required=True)
    product_type = fields.Selection([...], string='Product Type', required=True)
    provider_from_location_coordinates = fields.Char(string='Requested Location')
    provider_from_location_id = fields.Many2one('stock.location', string='From Location')
    provider_to_location_id = fields.Many2one('stock.location', string='To Location')
    datetime_from = fields.Datetime(string='Datetime From')
    datetime_to = fields.Datetime(string='Datetime To')
    quantity = fields.Float(string='Quantity')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', readonly=True)
    addon_service_ids = fields.One2many('addon.service', 'service_id', string='Addon Services')
    service_time = fields.Datetime(string='Service Time', readonly=True, required=True)
    # Provider details
    provider_id = fields.Many2one('res.partner', string='Provider')
    provider_contact = fields.Char(string='Provider Contact')
    provider_rate = fields.Float(string='Rate', readonly=True)
    avg_vendor_rating = fields.Float(string='Average Vendor Rating', readonly=True)
    company_vehicle = fields.Boolean(string='Company Vehicle')
    driver_job_id = fields.Many2one('hr.job', string='Driver Job')
    driver_id = fields.Many2one('hr.employee', string='Driver')
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    vehicle = fields.Char(string='Vehicle')
    driver_name = fields.Char(string='Driver Name')
    driver_num = fields.Char(string='Driver Contact Number')
    credit_proforma_number = fields.Char(string='Credit Proforma Number')
    vendor_rating = fields.Selection([...], string='Rate this service')
    rating_user_id = fields.Many2one('res.users', string='Rating User', readonly=True)
    completion_time = fields.Datetime(string='Completion Time', readonly=True)
    comment_history_ids = fields.One2many('comment.history', 'service_id', string='Comment History')
    service_history_ids = fields.One2many('service.history', 'service_id', string='Service History')
    enquiry_ids = fields.One2many('service.enquiry', 'service_id', string='Enquiries')
    new_service_id = fields.Many2one('aaa.service', string='New Service')
    cancelled_service_id = fields.Many2one('aaa.service', string='Origin')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('initiate', 'Initiate'),
        ('dispatch', 'Dispatch'),
        ('inprogress', 'In Progress'),
        ('start', 'Start'),
        ('reach', 'Reach'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
        ('discard', 'Discard')
    ], string='Status', default='draft')

    def action_initiate_service(self):
        self.state = 'initiate'

    def action_dispatch_service(self):
        self.state = 'dispatch'

    def action_schedule_service_check(self):
        self.schedule_service_check = True

    def action_inprogress_service(self):
        self.state = 'inprogress'

    def action_start_service(self):
        self.state = 'start'

    def action_reach_service(self):
        self.state = 'reach'

    def action_done_service(self):
        self.state = 'done'

    def action_cancel_service(self):
        self.state = 'cancel'

    def action_discard(self):
        self.state = 'discard'

    def action_create_enquiry(self):
        # Logic to create an enquiry
        pass

    def action_new(self):
        # Logic to create a new service
        pass