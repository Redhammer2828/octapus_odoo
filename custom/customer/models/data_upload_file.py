from odoo import models, fields, api ,_
from odoo.exceptions import ValidationError
from collections import defaultdict, Counter
from datetime import datetime
import time
import re

class DataUploadFile(models.Model):
    _name = 'data.upload.file'
    _description = 'Data Upload File'
    
    name = fields.Char(string='Name', required=True)
    file = fields.Binary(string='File')
    file_type = fields.Char('File Type')
    file_name = fields.Char(string="File Name")
    
    date = fields.Datetime('Uploaded Date', default=lambda self: fields.Datetime.now())
    upload_by = fields.Many2one('res.users', string='Uploaded By', default=lambda self: self.env.user)
    upload_log = fields.Text( string='Log')
    upload_member_ids = fields.One2many('upload.member.line', 'upload_file_id', string='Members')
    apply_log = fields.Text( string='Apply Log')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('validate', 'Validated'),
        ('done', 'Done')
    ], string='Status', default='draft')

# -----------------------------------------------------------NEW CODE-----------------------------------------------------------------------------------             
    def action_validate_policy_data(self):
        start_time = time.time()
        country_code_pattern = r'^[A-Z]{2}$'
        
        customer_codes = {member_line.customer_code for member_line in self.upload_member_ids}
        chassis_numbers = {member_line.vehicle_chasis_no.strip().upper() for member_line in self.upload_member_ids if member_line.vehicle_chasis_no.strip().upper() not in ['nan', '']}
        
        matching_partners = self.env['res.partner'].search([('customer_code', 'in', list(customer_codes))])
        partner_ids = matching_partners.ids
        
        partner_chassis = self.env['res.partner'].search([('parent_customer_id', 'in', partner_ids), ('member_type', '=', 'policy'),('membership_state', '!=', 'cancel')])
        partner_chassis_dict = {partner.vehicle_chasis_no.strip().upper(): partner for partner in partner_chassis}
        
        for member_line in self.upload_member_ids:
            excel_chassis_no = member_line.vehicle_chasis_no.strip().upper()
            
            if excel_chassis_no in ['nan', '']:
                member_line.update({'upload_member_status': 'rejection', 'comment': "*Vehicle Chasis Number Does Not Exist!"})
                print("[FAIL]")
                continue
            
            matching_partner = next((p for p in matching_partners if p.customer_code == member_line.customer_code), None)
            
            if not matching_partner:
                member_line.update({'upload_member_status': 'rejection', 'comment': "*Customer not exist!"})
                print("No matching customer found.")
                continue
            
            member = partner_chassis_dict.get(excel_chassis_no)
            
            if member:
                self.check_member_details(member, member_line)
            else:
                expiry_date = fields.Date.from_string(member_line.member_expiry_date)
                activate_date = fields.Date.from_string(member_line.member_activate_date)
                
                if expiry_date < activate_date:
                    member_line.update({'upload_member_status': 'rejection', 'comment': "*Expiry Date cannot be earlier than Activation Date!"})
                else:
                    member_line.update({'upload_member_status': 'new', 'comment': "**Not exist in System*New Member"})
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        total_count = len(self.upload_member_ids)
        status_counts = Counter(member.upload_member_status for member in self.upload_member_ids)
        
        rejected_count = status_counts['rejection']
        new_member_count = status_counts['new']
        updated_member_count = status_counts['update']
        renewal_member_count = status_counts['renewal']
        replaced_member_count = status_counts['replace']
        added_member_count = total_count - rejected_count
        
        self.upload_log = (f"Total Records: {total_count} | Rejected Records: {rejected_count} | Added Records: {added_member_count} | "
                        f"New Records: {new_member_count} | Extension Records: {updated_member_count} | Renewal Records: {renewal_member_count} | Changed Records: {replaced_member_count} | "
                        f"Time to Process: {processing_time} seconds")
        
        self.state = 'validate'

#------NEW MEMBERCHIP EXPIRY DATE ADN ACTIVATION CHECK ADDED CODE------
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
            print("EXCEL-CUSTOMER CODE",member_line.customer_code)
            # matching_customer = self.env['res.partner'].search([('customer_code', '=', member_line.customer_code)], limit=1)
            # print("PARENT CUSTOMER ID",member.parent_customer_id.id)
            # Retrieve the parent customer record using the parent_customer_id
            parent_customer = self.env['res.partner'].browse(member.parent_customer_id.id)
             # Get the customer_code from the parent customer record
            parent_customer_code = parent_customer.customer_code
            print("DB-CUSTOMER CODE",parent_customer_code)
            matching_partner = self.env['res.partner'].search([('customer_code', '=', member_line.customer_code)], limit=1)
            print("RES PARTNER ID OF CUSTOMER CODE",matching_partner)
            # Customer Code Check
            if member_line.customer_code == parent_customer_code:
                print("CUSTOMER CODE CHECK: [PASS]")
                if member.name == member_line.member_name:
                    print("NAME CHECK: [PASS]")
                    if member.membership_state == 'temp':
                        print("MEMBERSHIP STATE CHECK: [PASS]")
                        member_line.update({'upload_member_status': 'exist_temp', 'comment': "Exist Under Temp,*Overwrite"})
                        member_line.if_temp_match = member.id
                    elif member.membership_state == 'confirm':
                        print("MEMBER ID+_+_+__+_+_+_+__++_+_+_+", member.id)
                        member_line.if_conf_match = member.id
                        print("IF CONF()())(()()()((()())))", member_line.if_conf_match)

                        expiry_date = fields.Date.from_string(member_line.member_expiry_date)
                        activate_date = fields.Date.from_string(member.member_expiry_date)
                        db_expiry_date = fields.Date.from_string(member.member_expiry_date)
                        difference = (expiry_date - db_expiry_date).days
                        print("EXPIRY DATE:", expiry_date)
                        print("DB EXPIRY DATE:", db_expiry_date)
                        print("DIFFERENCE CALCULATED:", difference)
                        print("EXPIRY DATE IN RES.PARTNER:", member.member_expiry_date)
                        print("EXPIRY DATE IN EXCEL:", member_line.member_expiry_date)
                        
                        # New check: if member_line.member_expiry_date is less than member_line.member_activate_date
                        if expiry_date < activate_date:
                            print("EXPIRY DATE IS LESS THAN ACTIVATION DATE: [FAIL]")
                            member_line.update({'upload_member_status': 'rejection', 'comment': "*Expiry Date is less than Activation Date"})
                        else:
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
                    # member_line.update({'upload_member_status': 'new', 'comment': "Member Not Exist"})
                    db_name= member.name
                    db_expiry_date = member.member_expiry_date
                    excel_expiry_date = member_line.member_expiry_date
                    
                    if db_expiry_date >= excel_expiry_date:
                        member_line.update({'upload_member_status':'rejection', 'comment': 'Member with same expiry date'})
                        print("EXPIRY DATE_CHECK FAILED!!")
                    elif member.member_expiry_date < member_line.member_expiry_date:
                        member_line.update({'upload_member_status': 'replace', 'comment': "Member Replaced"})
                        member_line.if_rep_match = member.id

                        print("MEMBER REPLACEMENT PASS...")
            else:
                # Search for the chassis number under another customer code
                print("CUSTOMER CODE CHECK: [FAIL]")

                other_partner = self.env['res.partner'].search([
                    ('vehicle_chasis_no', '=', excel_chassis_no),
                    ('membership_state', '!=', 'cancel')
                ], limit=1)
                print("OTHER PARTNER",other_partner)
                if other_partner:
                    current_date = fields.Date.context_today(self)
                    db_expiry_date = member.member_expiry_date
                    if db_expiry_date >= current_date:
                        member_line.update({'upload_member_status': 'company_change', 'comment': "Active Data Found Under Another Customer. Cancelling & Add as New Member"})
                    elif db_expiry_date < current_date:
                        member_line.update({'upload_member_status': 'company_change', 'comment': "Expired Data Found Under Another Customer. Cancelling & Add as New Member"})
                        member_line.if_cpm_match = member.id
                        print("MEMBER REPLACEMENT PASS...")
                else:    
                    member_line.update({'upload_member_status': 'new', 'comment': "*New Member"})
                    print("New member: No matching chassis number found under another customer.")
#------------------------------------------OLF FLOW------------------------------------------------------ 
        else:
            if excel_chassis_no == 'nan' or excel_chassis_no == '':
                member_line.update({'upload_member_status': 'rejection', 'comment': "*Vehicle Chasis Number Does Not Exist!"})
                print("[FAIL]")
            else:

                member_line.update({'upload_member_status': 'new', 'comment': "*New Member"})
# ----------------------------------------------------------------------------------------------------------------------------------------------
    def apply_member_upload_wizard(self):
    
            # Start measuring time
            start_time = time.time()
            # Get the dynamically imported data after validation
            validated_member_lines = self.upload_member_ids.filtered(lambda line: line.upload_member_status != 'rejection')
            current_month = datetime.today().month
            current_year = datetime.today().year
    
            # Step 1: Pre-fetch data to minimize repetitive database queries
            customer_codes = {line.customer_code for line in validated_member_lines}
            partners = self.env['res.partner'].search([('customer_code', 'in', list(customer_codes))])
            partner_dict = {partner.customer_code: partner for partner in partners}
    
            card_types = {line.card_type for line in validated_member_lines}
            card_type_records = self.env['card.type'].search([('code', 'in', list(card_types))])
            card_type_dict = {card.code: card for card in card_type_records}
    
            sequence_codes = {line.sequence_code for line in validated_member_lines}
            categories = self.env['partner.category'].search([('name', 'in', list(sequence_codes))])
            category_dict = {(cat.name, cat.partner_id.id): cat for cat in categories}
    
            packages = {line.package for line in validated_member_lines}
            package_records = self.env['product.template'].search([('id', 'in', list(packages))])
            package_dict = {pkg.id: pkg for pkg in package_records}
    
            # Step 2: Process each member line
            for member_line in validated_member_lines:
                member_activate_date = fields.Date.from_string(member_line.member_activate_date)    
                # Handle 'new' status
                if member_line.upload_member_status == 'new':
                    card_type_record = card_type_dict.get(member_line.card_type)
                    matching_partner = partner_dict.get(member_line.customer_code)
    
                    if not matching_partner or not card_type_record:
                        print(f"No matching partner or card type for member {member_line.customer_code}")
                        continue
    
                    matching_category = category_dict.get((member_line.sequence_code, matching_partner.id))
                    matching_package = package_dict.get(member_line.package)
    
                    # Create a new partner record
                    new_partner = self.env['res.partner'].create({
                        'card_type_id': card_type_record.id,
                        'old_membership_number': member_line.old_membership_number,
                        'name': member_line.member_name,
                        'street': member_line.street,
                        'mobile': member_line.mobile,
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
                        'is_customer': True,
                        'adhoc_member': False,
                        'credit_member_ok': False,
                        'member_type': 'policy',
                        'membership_state': 'confirm',
                        'member_partner_category_id': matching_category.id if matching_category else None,
                        # Add more fields to create as needed
                    })
                # Handle 'renewal' or 'update' status
                elif member_line.upload_member_status in ['renewal']:
                    matching_partner = self.env['res.partner'].browse(member_line.if_conf_match)
                    if matching_partner:
                        matching_partner.write({
                            'membership_state': 'cancel',
                            'comment': 'Member Renewed the policy',
                        })
                        print("Renewed the policy member.....")
                        # Create a history record for the existing member
                        self.env['membership.history'].create({
                            'policy_no': matching_partner.policy_no,
                            'vehicle_chasis_no': matching_partner.vehicle_chasis_no,
                            'vehicle_type': matching_partner.vehicle_type,
                            'vehicle_plate': matching_partner.vehicle_plate,
                            'member_activate_date': matching_partner.member_activate_date,
                            'member_expiry_date': matching_partner.member_expiry_date,
                            'card_type_id': matching_partner.card_type_id.id,
                            'history_id': matching_partner.id,
                        })
                        print("Created history record for existing member.")
    
                        # Update existing member with new details
                        matching_partner.write({
                            'name': member_line.member_name,
                            'membership_state': 'confirm',
                            'member_expiry_date': member_line.member_expiry_date,
                            'policy_no': member_line.policy_no,
                            'member_activate_date': member_line.member_activate_date,
                            'invoice_ref_date': member_line.invoice_ref_date,
                            'delivery_ref_date': member_line.delivery_ref_date,
                            'vehicle_type': member_line.vehicle_type,
                            'vehicle_model': member_line.vehicle_model,
                            'vehicle_mfg_year': member_line.vehicle_mfg_year,
                            'vehicle_plate': member_line.vehicle_plate,
                            'vehicle_chasis_no': member_line.vehicle_chasis_no,
                            'street': member_line.street,
                            'mobile': member_line.mobile,
                        })
                        print("Existing member replaced with renewed policy details")
    
                    print(f"Finished processing member_line: {member_line.customer_code}")
    
                elif member_line.upload_member_status in ['update']:
                    matching_partner = self.env['res.partner'].browse(member_line.if_conf_match)
                    if matching_partner:
                        matching_partner.write({
                            'membership_state': 'cancel',
                            'comment': 'Member Extended the policy',
                        })
                        print(" POLICY EXTENSION...........")
                        # Create a history record for the existing member
                        self.env['membership.history'].create({
                            'policy_no': matching_partner.policy_no,
                            'vehicle_chasis_no': matching_partner.vehicle_chasis_no,
                            'vehicle_type': matching_partner.vehicle_type,
                            'vehicle_plate': matching_partner.vehicle_plate,
                            'member_activate_date': matching_partner.member_activate_date,
                            'member_expiry_date': matching_partner.member_expiry_date,
                            'card_type_id': matching_partner.card_type_id.id,
                            'history_id': matching_partner.id,
                        })
                        print("Created history record for existing member.")
    
                        # Update existing member with new details
                        matching_partner.write({
                            'name': member_line.member_name,
                            'membership_state': 'confirm',
                            'member_expiry_date': member_line.member_expiry_date,
                            'policy_no': member_line.policy_no,
                            'member_activate_date': member_line.member_activate_date,
                            'invoice_ref_date': member_line.invoice_ref_date,
                            'delivery_ref_date': member_line.delivery_ref_date,
                            'vehicle_type': member_line.vehicle_type,
                            'vehicle_model': member_line.vehicle_model,
                            'vehicle_mfg_year': member_line.vehicle_mfg_year,
                            'vehicle_plate': member_line.vehicle_plate,
                            'vehicle_chasis_no': member_line.vehicle_chasis_no,
                            'street': member_line.street,
                            'mobile': member_line.mobile,
                        })
                        print("Existing member replaced with extended policy details")
    
                    print(f"Finished processing member_line: {member_line.customer_code}")
    
                # Handle 'TEMP' status
                elif member_line.upload_member_status == 'exist_temp':
                    matching_partner = self.env['res.partner'].browse(member_line.if_temp_match)
                    if matching_partner:
                        matching_partner.write({
                            'membership_state': 'confirm',
                            'member_expiry_date': member_line.member_expiry_date,
                        })
    
                # Handle 'REPLACE' status
                elif member_line.upload_member_status == 'replace':
                    matching_partner = self.env['res.partner'].browse(member_line.if_rep_match)
                    if matching_partner:
                        matching_partner.write({
                            'membership_state': 'cancel',
                            'comment': 'Member replaced with uploaded member details',
                        })
                        print("Replaced member state updated to canceled.")
    
                        # Create a history record for the existing member
                        self.env['membership.history'].create({
                            'policy_no': matching_partner.policy_no,
                            'vehicle_chasis_no': matching_partner.vehicle_chasis_no,
                            'vehicle_type': matching_partner.vehicle_type,
                            'vehicle_plate': matching_partner.vehicle_plate,
                            'member_activate_date': matching_partner.member_activate_date,
                            'member_expiry_date': matching_partner.member_expiry_date,
                            'card_type_id': matching_partner.card_type_id.id,
                            'history_id': matching_partner.id,
                        })
                        print("Created history record for existing member.")
                        # Update existing member with new details
                        matching_partner.write({
                            'name': member_line.member_name,
                            'membership_state': 'confirm',
                            'member_expiry_date': member_line.member_expiry_date,
                            'policy_no': member_line.policy_no,
                            'member_activate_date': member_line.member_activate_date,
                            'invoice_ref_date': member_line.invoice_ref_date,
                            'delivery_ref_date': member_line.delivery_ref_date,
                            'vehicle_type': member_line.vehicle_type,
                            'vehicle_model': member_line.vehicle_model,
                            'vehicle_mfg_year': member_line.vehicle_mfg_year,
                            'vehicle_plate': member_line.vehicle_plate,
                            'vehicle_chasis_no': member_line.vehicle_chasis_no,
                            'street': member_line.street,
                            'mobile': member_line.mobile,
                        })
                        print("Existing member replaced with uploaded member details.")
                # Handle 'replace' status
                elif member_line.upload_member_status == 'company_change':
                    matching_partner = self.env['res.partner'].browse(member_line.if_cpm_match)
                    if matching_partner:
                        matching_partner.write({
                            'membership_state': 'cancel',
                            'comment': 'Member replaced with uploaded member details',
                        })
                        print("Replaced member state updated to canceled.")
    
                        # Create a history record for the existing member
                        self.env['membership.history'].create({
                            'policy_no': matching_partner.policy_no,
                            'vehicle_chasis_no': matching_partner.vehicle_chasis_no,
                            'vehicle_type': matching_partner.vehicle_type,
                            'vehicle_plate': matching_partner.vehicle_plate,
                            'member_activate_date': matching_partner.member_activate_date,
                            'member_expiry_date': matching_partner.member_expiry_date,
                            'card_type_id': matching_partner.card_type_id.id,
                            'history_id': matching_partner.id,
                        })
                        print("Created history record for existing member.")
                        parent_customer_code = self.env['res.partner'].search([('customer_code', '=', member_line.customer_code)], limit=1)
                        # Update existing member with new details
                        matching_partner.write({
                            'parent_customer_id': parent_customer_code.id,
                            'name': member_line.member_name,
                            'membership_state': 'confirm',
                            'member_expiry_date': member_line.member_expiry_date,
                            'policy_no': member_line.policy_no,
                            'member_activate_date': member_line.member_activate_date,
                            'invoice_ref_date': member_line.invoice_ref_date,
                            'delivery_ref_date': member_line.delivery_ref_date,
                            'vehicle_type': member_line.vehicle_type,
                            'vehicle_model': member_line.vehicle_model,
                            'vehicle_mfg_year': member_line.vehicle_mfg_year,
                            'vehicle_plate': member_line.vehicle_plate,
                            'vehicle_chasis_no': member_line.vehicle_chasis_no,
                            'street': member_line.street,
                            'mobile': member_line.mobile,
                        })
                        print("Existing member replaced with uploaded member details.")
    
                print(f"Finished processing member_line: {member_line.customer_code}")
        
            # Measure the time taken
            end_time = time.time()
            time_taken = end_time - start_time
    
            # Ensure apply_log is a string
            if not self.apply_log:
                self.apply_log = ""
    
            # Update the state and log
            self.state = 'done'
            self.apply_log += f" in {time_taken:.2f} seconds."
            print(f"State Updated to 'Done' and apply log updated with time taken: {time_taken:.2f} seconds.")
    
    def action_cancel(self):
        self.state = 'draft'
    
    def action_delete_members(self):
        return {
            'name': 'Delete Members',
            'type': 'ir.actions.act_window',
            'res_model': 'upload.member.line',
            'view_mode': 'tree',
            'view_id': self.env.ref('customer.upload_member_line_tree_view').id,
            'domain': [('upload_file_id', '=', self.id)],
            'context': {'default_upload_file_id': self.id},
        }
    
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
    
    def action_view_added_records(self):
        return {
            'name': 'Added Members',
            'type': 'ir.actions.act_window',
            'res_model': 'upload.member.line',
            'view_mode': 'tree',
            'view_id': self.env.ref('customer.view_upload_member_line_tree').id,
            'domain': [('upload_file_id', '=', self.id), ('upload_member_status', 'in', ['new', 'renewal', 'update', 'exist_temp'])],
            'context': {'default_upload_file_id': self.id},
        }
    

    def action_discard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'tree,form',
            'target': 'current',
        }

class UploadMemberLine(models.Model):
    _name = 'upload.member.line'
    _description = 'Upload Member Line'

    upload_file_id = fields.Many2one('data.upload.file', string='Upload File')
    upload_credit_file_id = fields.Many2one('credit.member.upload', string='Upload File')
    
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
        ('replace', 'Replaced Member'),
        ('discard', 'Discarded Member'),
        ('exist_temp', 'Exist in Temp'),
        ('company_change','Company change')
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
    remarks = fields.Text('Remarks')
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
    if_rep_match = fields.Integer('If Replace Match')
    if_cpm_match = fields.Integer('If Company change Match')
    
    