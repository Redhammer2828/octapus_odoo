from odoo import api, fields, models, _

class AAAService(models.Model):
    _name = 'aaa.service'
    _description = 'AAA Service'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Number", readonly=True, default=lambda self: _('New'))
    type = fields.Selection([('cash', 'Cash'), ('non_cash', 'Non-Cash')], string="Service Type", required=True, readonly=True, default='non_cash')
    member_type = fields.Selection([('adhoc', 'Adhoc'), ('policy', 'Policy')], string="Member Type", readonly=True, default='adhoc')
    card_type = fields.Char(string="Card Type", readonly=True)
    created_by = fields.Many2one('res.users', string="Agent", default=lambda self: self.env.user, readonly=True)
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
    ], string="Status", readonly=True, default='draft', tracking=True)
    customer_id = fields.Many2one('res.partner', string="Customer", domain="[('is_company', '=', True)")
    
    sequence_id = fields.Many2one('partner.category', string="Customer Category")
    member_id = fields.Many2one('res.partner', string="Member")
    
    member_contact_no = fields.Char(string="Mobile Number")
    email = fields.Char(string="Email")
    claim_membership = fields.Boolean(string="Claim Membership")
    deposit_amount = fields.Float(string="Deposit Amount")
    schedule_service_check = fields.Boolean(string="Schedule Service Check")
    schedule_date_time = fields.Datetime(string="Schedule Date Time")
    requested_date = fields.Datetime(string="Requested Date", required=True)
    driving_license = fields.Char(string="Driving License")
    claim_number = fields.Char(string="Claim Number")
    smarto = fields.Boolean(string="Smarto")
    smarto_id = fields.Char(string="Smarto ID")
    comments = fields.Text(string="Comments")
    vehicle_type_ok = fields.Boolean(string="Vehicle Type OK")
    vehicle_model_ok = fields.Boolean(string="Vehicle Model OK")
    
    vehicle_type_id = fields.Many2one('member.vehicle.type', string="Vehicle Type")
    #  domain="[('id', '=', vehicle_type_id)]"
    vehicle_type = fields.Char(string="Vehicle Type")
    
    vehicle_model_id = fields.Many2one('member.vehicle.model', string="Vehicle Model")
    # , domain="[('type_id', '=', vehicle_type_id)]"
    vehicle_model = fields.Char(string="Vehicle Model")
    
    vehicle_plate = fields.Char(string="Vehicle Plate")
    vehicle_chasis_no = fields.Char(string="Vehicle Chasis No")
    
    vehicle_emirate_id = fields.Many2one('emirate', string="Vehicle Emirate ID")
   
    policy_no = fields.Char(string="Policy No")
    
    product_id = fields.Many2one('product.template', string="Service", domain="[('bundle_product', '=', False), ('type', '=', 'service')]", required=True)
    
    product_type = fields.Selection([
        ('distance', 'Distance'),
        ('location', 'Location'),
        ('location_duration', 'Location Duration'),
        ('duration', 'Duration')
    ], string="Product Type", required=True)
    
    provider_from_location_id = fields.Many2one('location.internal', string="From Location")
    provider_to_location_id = fields.Many2one('location.internal', string="To Location")
    
    datetime_from = fields.Datetime(string="Datetime From")
    datetime_to = fields.Datetime(string="Datetime To")
    quantity = fields.Float(string="Quantity")
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure")
    addon_ok = fields.Boolean(string="Addon OK")
    
    main_product_ids = fields.Many2many('product.product', string="Main Products")
    
    service_time = fields.Datetime(string="Service Time", required=True)
    cash_collected_hidden = fields.Boolean(string="Cash Collected Hidden")
    cash_collected = fields.Float(string="Cash Collected")
    
    acc_payment_id = fields.Many2one('account.payment', string="Payment")
    
    waive_off = fields.Boolean(string="Waive Off")
    
    comment_history_ids = fields.One2many('service.comment', 'service_id', string="Comment History")
    service_history_ids = fields.One2many('service.history', 'service_id', string="Service History")
    enquiry_ids = fields.One2many('service.enquiry', 'service_id', string="Enquiries")
    provider_id = fields.Many2one('res.partner', string="Provider") #  domain="[('supplier', '=', True)]"
   
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
    
    rating_user_id = fields.Many2one('res.users', string="Rating User")
    
    completion_time = fields.Datetime(string="Completion Time")
    
    new_service_id = fields.Many2one('aaa.service', string="New Service")
    
    cancelled_service_id = fields.Many2one('aaa.service', string="Cancelled Service", readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('aaa.service') or _('New')
        result = super(AAAService, self).create(vals)
        return result

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

    def cash_service(self):
        self.type = 'cash'

    def convert_to_non_cash(self):
        self.type = 'non_cash'

    def action_cancel_service(self):
        self.state = 'cancel'

    def action_discard(self):
        self.state = 'discard'

    def action_create_enquiry(self):
        # self.ensure_one()
        # return {
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'service.enquiry',
        #     'view_mode': 'form',
        #     'target': 'new',
        #     'context': {
        #         'default_service_id': self.id,
        #     }
        # }
        pass

    def action_waive_off(self):
        # self.waive_off = True
        pass

    def action_new(self):
        # self.ensure_one()
        # new_service = self.copy({
        #     'new_service_id': self.id,
        # })
        # self.state = 'discard'
        # return {
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'aaa.service',
        #     'view_mode': 'form',
        #     'res_id': new_service.id,
        #     'target': 'current',
        # }
        pass

    def history(self):
        # self.ensure_one()
        # return {
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'service.history',
        #     'view_mode': 'tree,form',
        #     'domain': [('service_id', '=', self.id)],
        #     'context': {'default_service_id': self.id},
        # }
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

class ServiceEnquiry(models.Model):
    _name = 'service.enquiry'
    _description = 'Service Enquiry'

    name = fields.Char(string="Name")
    date = fields.Datetime(string="Date")
    mobile = fields.Char(string="Mobile")
    email = fields.Char(string="Email")
    enquiry = fields.Text(string="Enquiry")
    created_by = fields.Many2one('res.users', string="Created By")
    service_id = fields.Many2one('aaa.service', string="Service")


