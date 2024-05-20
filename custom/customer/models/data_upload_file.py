from odoo import models, fields, api
from odoo.exceptions import ValidationError
from collections import Counter
import time

class DataUploadFile(models.Model):
    _name = 'data.upload.file'
    _description = 'Data Upload File'
    
    name = fields.Char(string='Name', required=True)
    file = fields.Binary(string='File')
    file_type = fields.Char('File Type')
    
    date = fields.Datetime('Uploaded Date', default=lambda self: fields.Datetime.now())
    upload_by = fields.Many2one('res.users', string='Uploaded By', default=lambda self: self.env.user)
    upload_log = fields.Text( string='Log')
    upload_member_ids = fields.One2many('upload.member.line', 'upload_file_id', string='Members')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('validate', 'Validated'),
        ('done', 'Done')
    ], string='Status', default='draft')
    
    def action_validate_policy_data(self):
        start_time = time.time()
        
        print("Upload Member IDs:", self.upload_member_ids)
        
        for member_line in self.upload_member_ids:
            print("---------------------------------------------------------------------------")
            print("Processing member_line:", member_line)
            matching_partners = self.env['res.partner'].search([('customer_code', '=', member_line.customer_code)])

            print("EXCEL--- CUSTOMER CODE-NAME-----", member_line.customer_code)
            print("ID OF CUSTOMER CODE MATCH in DB--------", matching_partners.ids)
            
            match_found = False  # Flag to indicate if a match is found for the current member_line
            
            for matching_partner in matching_partners:
                member_list = self.env['res.partner'].search([('parent_customer_id', '=', matching_partner.id)])
                print("MEMBERs LIST------", member_list)
                
                for member in member_list:
                    excel_chassis_no = member_line.vehicle_chasis_no.strip().upper()
                    db_chassis_no = member.vehicle_chasis_no.strip().upper()

                    if excel_chassis_no == db_chassis_no:
                        print("Match found for member ID:", member.id)
                        self.check_member_details(member, member_line)
                        match_found = True
                        break  # Exit the loop once a match is found
            
                if match_found:
                    break  # Exit the outer loop if a match is found
            
            # If no match is found for the current member_line, update its status
            if not match_found:
                member_line.update({'upload_member_status': 'new', 'comment': "*New Member"})
        
        end_time = time.time()
        processing_time = end_time - start_time  # Calculate the processing time
        
        # Calculate counts
        total_count = len(self.upload_member_ids)
        rejected_count = Counter(member.upload_member_status for member in self.upload_member_ids)['rejection']
        new_member_count = Counter(member.upload_member_status for member in self.upload_member_ids)['new']
        updated_member_count = Counter(member.upload_member_status for member in self.upload_member_ids)['update']
        renewal_member_count = Counter(member.upload_member_status for member in self.upload_member_ids)['renewal']
        added_member_count = total_count - rejected_count  # Calculate the count of added records

        # Update the upload_log field with counts and processing time
        self.upload_log = f"Total Records: {total_count} | Rejected Records: {rejected_count} | Added Records: {added_member_count} | New Records: {new_member_count} | Updated Records: {updated_member_count} | Renewal Records: {renewal_member_count} | Time to Process: {processing_time} seconds"  
        
        self.state = 'validate'
       
    def check_member_details(self, member, member_line):
        print("Checking details for member ID:", member.id)
        print("CHASIS NUMBER EXCEL: ", member_line.vehicle_chasis_no)
        print("CHASIS NUMBER DB: ", member.vehicle_chasis_no)
        print("VEHICLE CHASIS CHECK:", end=" ")

        # Assuming vehicle_chasis_no is a string, we strip whitespace and convert to uppercase for comparison
        excel_chassis_no = member_line.vehicle_chasis_no.strip().upper()
        db_chassis_no = member.vehicle_chasis_no.strip().upper()

        if excel_chassis_no == db_chassis_no:
            print("[PASS]")
            if member.name == member_line.member_name:
                print("NAME CHECK: [PASS]")
                if member.membership_state == 'temp':
                    print("MEMBERSHIP STATE CHECK: [PASS]")
                    member_line.update({'upload_member_status': 'exist_temp', 'comment': "Exist Under Temp,*Overwrite"})
                    member_line.if_temp_match = member.id
                elif member.membership_state == 'confirm':
                    print("MEMBER ID+_+_+__+_+_+_+__++_+_+_+",member.id)
                    member_line.if_conf_match = member.id
                    print("IF CONF()())(()()()((()())))",member_line.if_conf_match)

                    expiry_date = fields.Date.from_string(member_line.member_expiry_date)
                    activate_date = fields.Date.from_string(member_line.member_activate_date)
                    difference = (expiry_date - activate_date).days
                    print("EXPIRY DATE:", expiry_date)
                    print("ACTIVATION DATE:", activate_date)
                    print("DIFFERENCE CALCULATED:", difference)
                    print("EXPIRY DATE IN RES.PARTNER:", member.member_expiry_date)
                    print("EXPIRY DATE IN EXCEL:", member_line.member_expiry_date)
                    if member.member_expiry_date != member_line.member_expiry_date:
                        if difference >= 365:
                            print("MEMBERSHIP RENEWAL")
                            member_line.update({'upload_member_status': 'renewal', 'comment': "*Membership Renewal"})
                        else:
                            print("MEMBERSHIP EXTENSION")
                            member_line.update({'upload_member_status': 'update', 'comment': "*Membership Extension"})
                    else:
                        print("DUPLICATE RECORD FOUND")
                        member_line.update({'upload_member_status': 'rejection', 'comment': "*Duplicate Record in System!"})
                else:
                    print("MEMBERSHIP STATE CHECK: [FAIL]")
                    member_line.update({'upload_member_status': 'new', 'comment': "Member Not Exist"})
            else:
                print("NAME CHECK: [FAIL]")
                member_line.update({'upload_member_status': 'new', 'comment': "Member Not Exist"})
        else:
            print("[FAIL]")
            member_line.update({'upload_member_status': 'new', 'comment': "*New Member"})

    def apply_member_upload_wizard(self):
        # Get the dynamically imported data after validation
        validated_member_lines = self.upload_member_ids.filtered(lambda line: line.upload_member_status != 'rejection')
        
        for member_line in validated_member_lines:
            if member_line.upload_member_status == 'new':

                card_type_record = self.env['card.type'].search([('code', '=', member_line.card_type)])
                
                matching_partner = self.env['res.partner'].search([('customer_code', '=', member_line.customer_code)])

                # Create a new partner record
                new_partner = self.env['res.partner'].create({
                    # 'customer_code': member_line.customer_code,
                    'card_type_id': card_type_record.id,  # Update with actual field names
                    'old_membership_number': member_line.old_membership_number,
                    'name': member_line.member_name,
                    'street': member_line.street,
                    'parent_customer_id': matching_partner.id,
                    'vehicle_type': member_line.vehicle_type,
                    'vehicle_model': member_line.vehicle_model,
                    'vehicle_mfg_year': member_line.vehicle_mfg_year,
                    'vehicle_plate': member_line.vehicle_plate,
                    'vehicle_chasis_no': member_line.vehicle_chasis_no,
                    'invoice_ref_date': member_line.invoice_ref_date,
                    'delivery_ref_date': member_line.delivery_ref_date,
                    'member_activate_date': member_line.member_activate_date,
                    'member_expiry_date': member_line.member_expiry_date,
                    'policy_no': member_line.policy_no,
                    'is_customer':True,
                    'adhoc_member': False,
                    'credit_member_ok': False,
                    'member_type': 'policy',
                    'membership_state': 'confirm',
                    # Add more fields to create as needed
                })
            elif member_line.upload_member_status in ['renewal', 'update']:
                # Search and get the record based on member_line.if_conf_match
                matching_partner = self.env['res.partner'].browse(member_line.if_conf_match)
                print("MATCHING PARTNER ID&&&&&&&&&&&&&&&", matching_partner.id)
                # Check if matching_partner is not empty
                if matching_partner:
                    matching_partner.write({
                        'member_expiry_date': member_line.member_expiry_date,
                    })
            elif member_line.upload_member_status in ['exist_temp']:
                matching_partner = self.env['res.partner'].browse(member_line.if_temp_match)
                if matching_partner:
                    matching_partner.write({
                        'membership_state': 'confirm',
                        'member_expiry_date': member_line.member_expiry_date,
                    })
                
        self.state = 'done'

    def action_cancel(self):
        self.state = 'draft'
    
    def action_delete_members(self):
        pass
    
    def action_view_rejected_records(self):
        return {
            'name': 'Rejected Members',
            'type': 'ir.actions.act_window',
            'res_model': 'upload.member.line',
            'view_mode': 'tree',
            'view_id': self.env.ref('customer.view_upload_member_line_tree').id,
            'domain': [('upload_file_id', '=', self.id), ('upload_member_status', '=', 'rejection')],
            'context': {'default_upload_file_id': self.id},
        }

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
        ('update', 'Update Member'),
        ('exist_temp', 'Exist in Temp')
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

    # Custom- Jkc logic
    if_temp_match = fields.Integer('Temp Match ID')
    if_conf_match = fields.Integer('If COnf Match')
