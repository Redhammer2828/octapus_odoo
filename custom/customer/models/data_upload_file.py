from odoo import models, fields, api

class DataUploadFile(models.Model):
    _name = 'data.upload.file'
    _description = 'Data Upload File'
    
    name = fields.Char(string='Name', required=True)
    file = fields.Binary(string='File')
    file_type = fields.Char('File Type')
    
    date = fields.Datetime('Uploaded Date', default=lambda self: fields.Datetime.now())
    upload_by = fields.Many2one('res.users', string='Uploaded By', default=lambda self: self.env.user)

    upload_member_ids = fields.One2many('upload.member.line', 'upload_file_id', string='Members')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('validate', 'Validated'),
        ('done', 'Done')
    ], string='Status', default='draft')

    
    def action_validate_policy_data(self):
        # Check for duplicates in the dynamically shown data
        duplicates = self._find_duplicates()
        if duplicates:
            # Print duplicates to console
            for duplicate in duplicates:
                print(f'Duplicate record: {duplicate}')
            # Handle duplicate records (e.g., raise warning or take appropriate action)
            # For now, let's raise a warning
            return {
                'warning': {
                    'title': 'Duplicate Records',
                    'message': 'Duplicate records found. Check console for details.',
                }
            }
        
        # Implement the validation logic here
        self.state = 'validate'

    def _find_duplicates(self):
        # Extract relevant fields for duplicate check (e.g., member_name, mobile)
        relevant_fields = ['old_membership_number', 'vehicle_chasis_no']  # Adjust as per your requirements
        
        # Create a dictionary to store record IDs based on unique field values
        field_values_dict = {}
        for member_line in self.upload_member_ids:
            key = tuple(member_line[field_name] for field_name in relevant_fields)
            field_values_dict.setdefault(key, []).append(member_line.id)
        
        # Identify duplicate records
        duplicate_records = []
        for key, record_ids in field_values_dict.items():
            if len(record_ids) > 1:
                # Duplicate records found
                duplicate_records.extend(record_ids)
        
        return duplicate_records

    def apply_member_upload_wizard(self):
        # Implement the logic to create/update res.partner records
        self.state = 'done'

    def action_cancel(self):
        self.state = 'draft'
    
    def action_delete_members(self):
        pass
    
    def action_view_rejected_records(self):
        pass

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
    
    vehicle_type = fields.Char('vehicle_type') 
    vehicle_model = fields.Char('vehicle_model') 
    mail_ref = fields.Char('mail_ref') 

    vehicle_mfg_year = fields.Char(string='Vehicle Manufacturing Year')
    vehicle_reg_code = fields.Char(string='Vehicle Registration Code')
   
    street = fields.Char(string='Street')
    zip = fields.Char('zip') #Created
    
    delivery_ref_date = fields.Date(string='Delivery Reference Date')
    comment = fields.Text(string='Comment')
    sequence_code = fields.Char(string='Sequence Code')
    upload_member_status = fields.Selection([
        ('new', 'New'),
        ('renewal', 'Renewal'),
        ('rejection', 'Rejected')
    ], string='Status', default='new')


    card_type = fields.Char('Card Type')
    state = fields.Char('State')
    country = fields.Char('Country')
    region_code = fields.Char('Region Code')
    vehicle_reg_country = fields.Char('Vehicle Reg Country')
    vehicle_emirate = fields.Char('Vehicle Emirate')


    # card_type_id = fields.Many2one('card.type', string='Card Type')
    # country_id = fields.Many2one('res.country', string='Country')
    # state_id = fields.Many2one('res.country.state', string='Emirate')
    # region_code_id = fields.Many2one('region.code', string='Region Code')
    # vehcle_reg_country_id = fields.Many2one('res.country', string='Vehicle Registration Country')
    # vehicle_emirate_id = fields.Many2one('res.country.state', string='Vehicle Emirate')
