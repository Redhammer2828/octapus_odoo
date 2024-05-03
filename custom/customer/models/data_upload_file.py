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
        duplicate_records, matching_partner_records = self._find_duplicates()
        
        # Handle duplicate records
        if duplicate_records:
            # Update upload_member_status to 'Rejected Member'
            self.upload_member_ids.filtered(lambda line: line.id in duplicate_records).update({'upload_member_status': 'rejection'})
        
        # Handle matching partner records
        if matching_partner_records:
            # Update upload_member_status to 'Rejected Member' for each matching record
            for partner_record in matching_partner_records:
                self.upload_member_ids.filtered(lambda line: line.vehicle_chasis_no == partner_record.vehicle_chasis_no
                                                and line.member_expiry_date == partner_record.member_expiry_date).update({'upload_member_status': 'rejection'})
        
#-----------------------------------------------------------------------------------------------------------------------------
        # Check for customer_code matches and update upload_member_status
        for member_line in self.upload_member_ids:
            matching_partner = self.env['res.partner'].search([
                ('customer_code', '=', member_line.customer_code),
            ], limit=1)
            if matching_partner: # if Customer_code matches , Same insurance company
                # Customer code matches, move to next checks
                if matching_partner.vehicle_chasis_no == member_line.vehicle_chasis_no: # If Vehicle Chasis Number Matches , Moves to name check
                # Check if the name matches
                    if matching_partner.name == member_line.member_name:
                        # Name matches, check membership_state
                        if matching_partner.membership_state == 'temp':            #temp , confirm , cancel 3  statuses are there
                            member_line.update({'upload_member_status': 'new'})   # If same comp , same member , Exist in temp , save as new Membership.
                        elif matching_partner.membership_state == 'confirm':
                            # Calculate difference between member_expiry_date and member_activate_date
                            expiry_date = fields.Date.from_string(member_line.member_expiry_date)
                            activate_date = fields.Date.from_string(member_line.member_activate_date)
                            difference = (expiry_date - activate_date).days
                            if difference >= 365:  # 12 months or above
                                member_line.update({'upload_member_status': 'Renewal Member'})
                            else:
                                member_line.update({'upload_member_status': 'Update Member'})
                    else:
                        # Name doesn't match, update upload_member_status to 'new'
                        member_line.update({'upload_member_status': 'new'}) # If name  does not match, that is Member does to exist under Same company ,New Membership
                else:
                    member_line.update({'upload_member_status': 'new'}) # if Vehicle Chasis Number  does not Match : Need to save as new rec , New membership
            else:
                # No matching partner found, update upload_member_status to 'Rejected Member'
                member_line.update({'upload_member_status': 'rejection'}) #Company Doesnt exist , so Rejection.
 #--------------------------------------------------------------------------------------------------------------------------------       
        
        # If duplicates or matching partner records are found, return a warning
        if duplicate_records or matching_partner_records:
            return {
                'type': 'ir.actions.act_window_close',
                'warning': {
                    'title': 'Records Rejected',
                    'message': 'Duplicate or matching records found. They have been marked as Rejected Members.',
                }
            }
        
        # Implement the validation logic here
        self.state = 'validate'



    def _find_duplicates(self):
        # Extract relevant fields for duplicate check
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
        
        # Check for matching partner records
        matching_partner_records = []
        for member_line in self.upload_member_ids:
            matching_partners = self.env['res.partner'].search([
                ('vehicle_chasis_no', '=', member_line.vehicle_chasis_no),
                ('member_expiry_date', '=', member_line.member_expiry_date),
            ])
            if matching_partners:
                # Matching partner records found
                matching_partner_records.extend(matching_partners)
        
        return duplicate_records, matching_partner_records

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
    # --------------------------------------------------------------------
    # Created
    member_type = fields.Selection([
        ('policy', 'Policy Member'),
        ('credit', 'Credit Member')
    ], string='Member Type')

    upload_member_status = fields.Selection([
        ('new', 'New Member'),
        ('rejection', 'Rejected Member'),
        ('renewal', 'Renewal Member'),
        ('update', 'Update Member')
    ], string='Upload Status')
    # --------------------------------------------------------------------
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


    card_type = fields.Char('Card Type')
    state = fields.Char('State')
    country = fields.Char('Country')
    region_code = fields.Char('Region Code')
    vehicle_reg_country = fields.Char('Vehicle Reg Country')
    vehicle_emirate = fields.Char('Vehicle Emirate')
