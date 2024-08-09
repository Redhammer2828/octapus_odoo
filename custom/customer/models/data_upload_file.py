from odoo import models, fields, api
from odoo.exceptions import ValidationError
from collections import defaultdict, Counter
from datetime import datetime
import time

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

# # -----------------------------------------------------------OLD CODE-----------------------------------------------------------------------------------             
#     def action_validate_policy_data(self):
#         start_time = time.time()
#         i=0
#         for member_line in self.upload_member_ids:
#             # print("---------------------------------------------------------------------------")
#             print("Processing member_line:", member_line)
#             matching_partners = self.env['res.partner'].search([('customer_code', '=', member_line.customer_code)])

#             print("EXCEL--- CUSTOMER CODE-NAME-----", member_line.customer_code)
#             print("ID OF CUSTOMER CODE MATCH in DB--------", matching_partners.ids)
#             match_found = False  # Flag to indicate if a match is found for the current member_line
#             i+=1
#             print("LOOP",i)
#             if not matching_partners:
#             # If no matching partners are found, update the member line status and continue to the next member line
#                 member_line.update({'upload_member_status': 'rejection', 'comment': "*Customer not exist!"})
#                 print("No matching customer found.")
#                 continue
            
#             for matching_partner in matching_partners:
#                 member_list = self.env['res.partner'].search([('parent_customer_id', '=', matching_partner.id),('member_type', '=', 'policy')])
#                 for member in member_list:
#                     excel_chassis_no = member_line.vehicle_chasis_no.strip().upper()
#                     db_chassis_no = member.vehicle_chasis_no.strip().upper()
#                     if excel_chassis_no in ['nan', '']:  # Corrected condition
#                         member_line.update({'upload_member_status': 'rejection', 'comment': "*Vehicle Chasis Number Does Not Exist!"})
#                         print("[FAIL]")
#                     elif excel_chassis_no == db_chassis_no:
#                         print("Match found for member ID:", member.id)
#                         self.check_member_details(member, member_line)
#                         match_found = True
#                         break  # Exit the loop once a match is found
#                 if match_found:
#                     break  # Exit the outer loop if a match is found
            
#             # If no match is found for the current member_line, update its status
#             if not match_found:
#                     expiry_date = fields.Date.from_string(member_line.member_expiry_date)
#                     activate_date = fields.Date.from_string(member_line.member_activate_date)
                    
#                     if expiry_date < activate_date:
#                         member_line.update({'upload_member_status': 'rejection', 'comment': "*Expiry Date cannot be earlier than Activation Date!"})
#                     else:
#                         member_line.update({'upload_member_status': 'new', 'comment': "**Not exist in System*New Member"})
                        
#         end_time = time.time()
#         processing_time = end_time - start_time  # Calculate the processing time
        
#         # Calculate counts
#         total_count = len(self.upload_member_ids)
#         rejected_count = Counter(member.upload_member_status for member in self.upload_member_ids)['rejection']
#         new_member_count = Counter(member.upload_member_status for member in self.upload_member_ids)['new']
#         updated_member_count = Counter(member.upload_member_status for member in self.upload_member_ids)['update']
#         renewal_member_count = Counter(member.upload_member_status for member in self.upload_member_ids)['renewal']
#         added_member_count = total_count - rejected_count  # Calculate the count of added records

#         # Update the upload_log field with counts and processing time
#         self.upload_log = f"Total Records: {total_count} | Rejected Records: {rejected_count} | Added Records: {added_member_count} | New Records: {new_member_count} | Updated Records: {updated_member_count} | Renewal Records: {renewal_member_count} | Time to Process: {processing_time} seconds"  
        
#         self.state = 'validate'
# -----------------------------------------------------------NEW CODE-----------------------------------------------------------------------------------             
    def action_validate_policy_data(self):
        start_time = time.time()
        
        customer_codes = {member_line.customer_code for member_line in self.upload_member_ids}
        chassis_numbers = {member_line.vehicle_chasis_no.strip().upper() for member_line in self.upload_member_ids if member_line.vehicle_chasis_no.strip().upper() not in ['nan', '']}
        
        matching_partners = self.env['res.partner'].search([('customer_code', 'in', list(customer_codes))])
        partner_ids = matching_partners.ids
        
        partner_chassis = self.env['res.partner'].search([('parent_customer_id', 'in', partner_ids), ('member_type', '=', 'policy')])
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
        added_member_count = total_count - rejected_count
        
        self.upload_log = (f"Total Records: {total_count} | Rejected Records: {rejected_count} | Added Records: {added_member_count} | "
                        f"New Records: {new_member_count} | Updated Records: {updated_member_count} | Renewal Records: {renewal_member_count} | "
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
                    activate_date = fields.Date.from_string(member_line.member_activate_date)
                    difference = (expiry_date - activate_date).days
                    print("EXPIRY DATE:", expiry_date)
                    print("ACTIVATION DATE:", activate_date)
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
                print("NAME CHECK: [FAIL]", member.name)
                db_name= member.name
                
                if member.member_expiry_date >= member_line.member_expiry_date:
                    member_line.update({'upload_member_status':'rejection', 'comment': 'Member with same expiry date'})
                    print("EXPIRY DATE_CHECK FAILED!!")
                elif member.member_expiry_date < member_line.member_expiry_date:
                    member_line.update({'upload_member_status': 'replace', 'comment': "Member Replaced"})
                    member_line.if_rep_match = member.id

                    print("MEMBER REPLACEMENT PASS...")
                    

        else:
            if excel_chassis_no == 'nan' or excel_chassis_no == '':
                member_line.update({'upload_member_status': 'rejection', 'comment': "*Vehicle Chasis Number Does Not Exist!"})
                print("[FAIL]")
            else:
                member_line.update({'upload_member_status': 'new', 'comment': "*New Member"})
    
    def apply_member_upload_wizard(self):
        # Get the dynamically imported data after validation
        validated_member_lines = self.upload_member_ids.filtered(lambda line: line.upload_member_status != 'rejection')
        current_month = datetime.today().month
        current_year = datetime.today().year

        matching_partner= self.env['res.partner']
        
        for member_line in validated_member_lines:
             # Convert member_activate_date to a datetime object for comparison
                member_activate_date = fields.Date.from_string(member_line.member_activate_date)
                if member_activate_date.month != current_month:
                    # If the month is different, update the invoice_ref_date to the current month
                    new_invoice_ref_date = member_activate_date.replace(month=current_month, year=current_year)
                    member_line.update({
                        'invoice_ref_date': new_invoice_ref_date,
                        'member_activate_date': new_invoice_ref_date,
                    })
                    print(f"Updated member_activate_date and invoice_ref_date to {new_invoice_ref_date} for member {member_line.member_name}")
                else:
                    # If the month is the same, use the existing invoice_ref_date
                    member_line.update({
                        'member_activate_date': member_line.invoice_ref_date,
                    })
                    print(f"Set member_activate_date to invoice_ref_date for member {member_line.member_name}")

                if member_line.upload_member_status == 'new':

                    card_type_record = self.env['card.type'].search([('code', '=', member_line.card_type)])
                    
                    matching_partner = self.env['res.partner'].search([('customer_code', '=', member_line.customer_code)])
                    print("MATHING CUSTOMERR", matching_partner.ids)
                    #------------CATEGORY CODE UPLOAD----------------------
                    matching_category=self.env['partner.category'].search([('name','=', member_line.sequence_code),('partner_id','=', matching_partner.id)],limit=1)
                    print("MATCHING SEQ_CODE", matching_category.ids)

                    matching_package = self.env['product.template'].search([('id', '=', member_line.package)],limit=1)
                    print("PACKAGES",matching_package.ids)
                    # matching_category_code = self.env[]
                    # Create a new partner record
                    new_partner = self.env['res.partner'].create({
                        # 'customer_code': member_line.customer_code,
                        'card_type_id': card_type_record.id,  # Update with actual field names
                        'old_membership_number': member_line.old_membership_number,
                        'name': member_line.member_name,
                        'street': member_line.street,
                        'mobile': member_line.mobile,
                        'parent_customer_id': matching_partner.id,
                        #'product_template_id': member_line.package,
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
                        'member_partner_category_id': matching_category.id
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
                    matching_partner = self.env['res.partner'].browse(member_line.if_rep_match)
                    if matching_partner:
                        matching_partner.write({
                            'membership_state': 'confirm',
                            'member_expiry_date': member_line.member_expiry_date,
                        })
                
                elif member_line.upload_member_status == 'replace':
                    # Ensure that the 'if_temp_match' and 'if_conf_match' fields are correctly assigned
                
                    matching_partner = self.env['res.partner'].browse(member_line.if_rep_match )
                    print("REPLACING PARTNER ID", matching_partner.id)
                
                if matching_partner:
                    # Update the state of the existing member to 'cancel'
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
                

                self.state = 'done'
# ----------------------------------------------------------------------------------------------------------------------------------------------
# ___________________________________________________________________________________________________________________________________   
    # def apply_member_upload_wizard(self):
    #     # Get the dynamically imported data after validation
    #     validated_member_lines = self.upload_member_ids.filtered(lambda line: line.upload_member_status != 'rejection')
        
    #     for member_line in validated_member_lines:
    #         if member_line.upload_member_status == 'new':
    #             # Search for the card type record
    #             card_type_record = self.env['card.type'].search([('code', '=', member_line.card_type)], limit=1)
    #             if not card_type_record:
    #                 raise ValidationError(f"Card type '{member_line.card_type}' not found.")

    #             # Search for the matching partner
    #             matching_partner = self.env['res.partner'].search([('customer_code', '=', member_line.customer_code)], limit=1)
    #             if not matching_partner:
    #                 raise ValidationError(f"Partner with customer code '{member_line.customer_code}' not found.")
                
    #             # Search for the matching category
    #             matching_category = self.env['partner.category'].search([('name', '=', member_line.sequence_code), ('partner_id', '=', matching_partner.id)], limit=1)
    #             if not matching_category:
    #                 raise ValidationError(f"Category '{member_line.sequence_code}' not found for partner ID {matching_partner.id}.")

    #             # Create a new partner record
    #             new_partner = self.env['res.partner'].create({
    #                 'card_type_id': card_type_record.id,  # Update with actual field names
    #                 'old_membership_number': member_line.old_membership_number,
    #                 'name': member_line.member_name,
    #                 'street': member_line.street,
    #                 'parent_customer_id': matching_partner.id,
    #                 'vehicle_type': member_line.vehicle_type,
    #                 'vehicle_model': member_line.vehicle_model,
    #                 'vehicle_mfg_year': member_line.vehicle_mfg_year,
    #                 'vehicle_plate': member_line.vehicle_plate,
    #                 'vehicle_chasis_no': member_line.vehicle_chasis_no,
    #                 'invoice_ref_date': member_line.invoice_ref_date,
    #                 'delivery_ref_date': member_line.delivery_ref_date,
    #                 'member_activate_date': member_line.member_activate_date,
    #                 'member_expiry_date': member_line.member_expiry_date,
    #                 'policy_no': member_line.policy_no,
    #                 'is_customer': True,
    #                 'adhoc_member': False,
    #                 'credit_member_ok': False,
    #                 'member_type': 'policy',
    #                 'membership_state': 'confirm',
    #                 'member_partner_category_id': matching_category.id,
    #                 'product_template_id': member_line.package,
    #                 'mobile': member_line.mobile,
    #                 # Add more fields to create as needed
    #             })
    #             print("New Partner Created:", new_partner.id)
            
    #         elif member_line.upload_member_status in ['renewal', 'update']:
    #             # Search and get the record based on member_line.if_conf_match
    #             matching_partner = self.env['res.partner'].browse(member_line.if_conf_match)
    #             print("Matching Partner for Update/Renewal:", matching_partner.id)
    #             if matching_partner:
    #                 matching_partner.write({
    #                     'member_expiry_date': member_line.member_expiry_date,
    #                 })
    #                 print("Partner Updated:", matching_partner.id)
            
    #         elif member_line.upload_member_status in ['exist_temp']:
    #             matching_partner = self.env['res.partner'].browse(member_line.if_temp_match)
    #             if matching_partner:
    #                 matching_partner.write({
    #                     'membership_state': 'confirm',
    #                     'member_expiry_date': member_line.member_expiry_date,
    #                 })
    #                 print("Temp Partner Confirmed:", matching_partner.id)
                    
    #     self.state = 'done'
    #     print("State Updated to 'Done'")

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
        ('replace', 'Replaced Member'),
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
    if_rep_match = fields.Integer('If Replace Match')