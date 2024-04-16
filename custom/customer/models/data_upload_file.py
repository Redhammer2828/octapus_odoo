from odoo import models, fields, api

class DataUploadFile(models.Model):
    _name = 'data.upload.file'
    _description = 'Data Upload File'
    
    name = fields.Char(string='Name', required=True)
    file = fields.Binary(string='File')
    file_type = fields.Char('File Type')
    
    # date = fields.Date('Uploaded Date')
    # upload_by = fields.Char('uploaded_by')
    
    
    upload_member_ids = fields.One2many('upload.member.line', 'upload_file_id', string='Members')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('validate', 'Validated'),
        ('done', 'Done')
    ], string='Status', default='draft')

    def action_validate_policy_data(self):
        # Implement the validation logic here
        self.state = 'validate'

    def apply_member_upload_wizard(self):
        # Implement the logic to create/update res.partner records
        self.state = 'done'

    def action_cancel(self):
        self.state = 'draft'

class UploadMemberLine(models.Model):
    _name = 'upload.member.line'
    _description = 'Upload Member Line'

    upload_file_id = fields.Many2one('data.upload.file', string='Upload File')
    
    member_name = fields.Char(string='Name')
    mobile = fields.Char(string='Mobile')
    vehicle_plate = fields.Char(string='Vehicle Plate')
    vehicle_chasis_no = fields.Char(string='Vehicle Chassis No')
    member_activate_date = fields.Date(string='Member Activate Date')
    member_expiry_date = fields.Date(string='Member Expiry Date')
    invoice_ref_date = fields.Date(string='Invoice Reference Date')
    customer_code = fields.Char(string='Customer Code')
    package = fields.Char(string='Package ID')
    member_type = fields.Selection([
        ('new', 'New'),
        ('renewal', 'Renewal'),
        ('other', 'Other')
    ], string='Member Type', default='new')
    customer_ref_date = fields.Date(string='Customer Reference Date')
    old_membership_number = fields.Char(string='Old Membership Number')
    policy_no = fields.Char(string='Policy No')
    vehicle_mfg_year = fields.Char(string='Vehicle Manufacturing Year')
    vehcle_reg_country_id = fields.Many2one('res.country', string='Vehicle Registration Country')
    vehicle_emirate_id = fields.Many2one('res.country.state', string='Vehicle Emirate')
    vehicle_reg_code = fields.Char(string='Vehicle Registration Code')
    street = fields.Char(string='Street')
    state_id = fields.Many2one('res.country.state', string='State')
    region_code_id = fields.Many2one('region.code', string='Region Code')
    country_id = fields.Many2one('res.country', string='Country')
    delivery_ref_date = fields.Date(string='Delivery Reference Date')
    card_type_id = fields.Many2one('card.type', string='Card Type')
    comment = fields.Text(string='Comment')
    sequence_code = fields.Char(string='Sequence Code')
    upload_member_status = fields.Selection([
        ('new', 'New'),
        ('renewal', 'Renewal'),
        ('rejection', 'Rejected')
    ], string='Status', default='new')