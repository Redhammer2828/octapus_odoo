from odoo import models, fields ,api
from odoo.exceptions import ValidationError
from collections import Counter
import time

class CreditMemberUpload(models.Model):
    _name = 'credit.member.upload'
    _description = 'Member Upload Cancel'

    name = fields.Char(string='Name', required=True)
    file = fields.Binary(string='File')
    file_type = fields.Char('File Type')
    file_name = fields.Char(string="File Name")

    date = fields.Datetime('Uploaded Date', default=lambda self: fields.Datetime.now())
    upload_by = fields.Many2one('res.users', string='Uploaded By', default=lambda self: self.env.user)
    upload_log = fields.Text( string='Log')
    upload_member_ids = fields.One2many('credit.member.upload.line', 'upload_file_id', string='Members')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('validate', 'Validated'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft')

    temp_store = fields.Text(string='Temporary Store', default='{}')

    def action_validate_policy_data(self):
        start_time = time.time()
        
        # Collect all necessary data upfront
        customer_codes = [line.customer_code for line in self.upload_member_ids]
        matching_partners = self.env['res.partner'].search([('customer_code', 'in', customer_codes)])
        
        partner_dict = {partner.customer_code: partner for partner in matching_partners}
        
        for member_line in self.upload_member_ids:
            matching_partner = partner_dict.get(member_line.customer_code)
            
            if not matching_partner:
                member_line.update({'upload_member_status': 'rejection', 'comment': "*Customer not exist!"})
                continue
            
            member_list = self.env['res.partner'].search([
                ('parent_customer_id', '=', matching_partner.id),
                ('member_type', '=', 'credit')
            ])
            
            match_found = False
            excel_chassis_no = member_line.vehicle_chasis_no.strip().upper()
            
            if excel_chassis_no in ['NAN', '']:
                member_line.update({'upload_member_status': 'rejection', 'comment': "*Vehicle Chasis Number Does Not Exist!"})
                continue
            
            for member in member_list:
                db_chassis_no = member.vehicle_chasis_no.strip().upper()
                if excel_chassis_no == db_chassis_no:
                    self.check_member_details(member, member_line)
                    match_found = True
                    break
            
            if not match_found:
                expiry_date = fields.Date.from_string(member_line.member_expiry_date)
                activate_date = fields.Date.from_string(member_line.member_activate_date)
                
                if activate_date is not None and expiry_date < activate_date:
                    member_line.update({'upload_member_status': 'rejection', 'comment': "*Expiry Date cannot be earlier than Activation Date!"})
                else:
                    member_line.update({'upload_member_status': 'new', 'comment': "**Not exist in System*New Member"})
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Calculate counts
        total_count = len(self.upload_member_ids)
        status_counter = Counter(member.upload_member_status for member in self.upload_member_ids)
        rejected_count = status_counter['rejection']
        new_member_count = status_counter['new']
        updated_member_count = status_counter['update']
        renewal_member_count = status_counter['renewal']
        added_member_count = total_count - rejected_count
        
        # Update the upload_log field with counts and processing time
        self.upload_log = (
            f"Total Records: {total_count} | Rejected Records: {rejected_count} | "
            f"Added Records: {added_member_count} | New Records: {new_member_count} | "
            f"Updated Records: {updated_member_count} | Renewal Records: {renewal_member_count} | "
            f"Time to Process: {processing_time} seconds"
        )
        
        self.state = 'validate'

    def check_member_details(self, member, member_line):
        excel_chassis_no = member_line.vehicle_chasis_no.strip().upper()
        db_chassis_no = member.vehicle_chasis_no.strip().upper()

        if excel_chassis_no == db_chassis_no:
            if member.name == member_line.member_name:
                if member.membership_state == 'temp':
                    member_line.update({'upload_member_status': 'exist_temp', 'comment': "Exist Under Temp,*Overwrite"})
                    member_line.if_temp_match = member.id
                elif member.membership_state == 'confirm':
                    member_line.if_conf_match = member.id
                    
                    expiry_date = fields.Date.from_string(member_line.member_expiry_date)
                    activate_date = fields.Date.from_string(member_line.member_activate_date)
                    difference = (expiry_date - activate_date).days
                    
                    if expiry_date < activate_date:
                        member_line.update({'upload_member_status': 'rejection', 'comment': "*Expiry Date is less than Activation Date"})
                    else:
                        if member.member_expiry_date != member_line.member_expiry_date:
                            if difference >= 365:
                                member_line.update({'upload_member_status': 'renewal', 'comment': "*Membership Renewal"})
                            else:
                                member_line.update({'upload_member_status': 'update', 'comment': "*Membership Extension"})
                        else:
                            member_line.update({'upload_member_status': 'rejection', 'comment': "*Duplicate Record in System!"})
                else:
                    member_line.update({'upload_member_status': 'new', 'comment': "Member Not Exist"})
            else:
                member_line.update({'upload_member_status': 'new', 'comment': "Member Not Exist"})
        else:
            if excel_chassis_no in ['NAN', '']:
                member_line.update({'upload_member_status': 'rejection', 'comment': "*Vehicle Chasis Number Does Not Exist!"})
            else:
                member_line.update({'upload_member_status': 'new', 'comment': "*New Member"})


    def apply_member_upload_wizard(self):
        # Get the dynamically imported data after validation
        validated_member_lines = self.upload_member_ids.filtered(lambda line: line.upload_member_status != 'rejection')
        
        # Collect customer codes and card types upfront
        customer_codes = {line.customer_code for line in validated_member_lines if line.upload_member_status == 'new'}
        card_types = {line.card_type for line in validated_member_lines if line.upload_member_status == 'new'}

        # Batch search for all matching partners and card types
        matching_partners = self.env['res.partner'].search([('customer_code', 'in', list(customer_codes))])
        matching_partners_dict = {partner.customer_code: partner for partner in matching_partners}
        
        card_type_records = self.env['card.type'].search([('code', 'in', list(card_types))])
        card_type_dict = {card.code: card for card in card_type_records}

        # Batch search for partner categories
        partner_ids = [partner.id for partner in matching_partners]
        sequence_codes = {line.sequence_code for line in validated_member_lines}
        matching_categories = self.env['partner.category'].search([
            ('name', 'in', list(sequence_codes)),
            ('partner_id', 'in', partner_ids)
        ])
        category_dict = {(category.name, category.partner_id.id): category for category in matching_categories}

        for member_line in validated_member_lines:
            if member_line.upload_member_status == 'new':
                card_type_record = card_type_dict.get(member_line.card_type)
                matching_partner = matching_partners_dict.get(member_line.customer_code)

                if not matching_partner or not card_type_record:
                    # If no matching partner or card type record is found, skip this line
                    continue

                # Retrieve the matching category
                matching_category = category_dict.get((member_line.sequence_code, matching_partner.id))
                
                # Create a new partner record
                new_partner = self.env['res.partner'].create({
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
                    'is_customer': True,
                    'adhoc_member': False,
                    'credit_member_ok': False,
                    'member_type': 'credit',
                    'membership_state': 'confirm',
                    'member_partner_category_id': matching_category.id if matching_category else False
                })
            elif member_line.upload_member_status in ['renewal', 'update']:
                # Update the matching partner record based on member_line.if_conf_match
                matching_partner = self.env['res.partner'].browse(member_line.if_conf_match)
                if matching_partner:
                    matching_partner.write({'member_expiry_date': member_line.member_expiry_date})
            elif member_line.upload_member_status == 'exist_temp':
                # Update the matching partner record based on member_line.if_temp_match
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
        return {
            'name': 'Delete Members',
            'type': 'ir.actions.act_window',
            'res_model': 'credit.member.upload.line',
            'view_mode': 'tree',
            'view_id': self.env.ref('customer.upload_member_line_tree_view').id,
            'domain': [('upload_file_id', '=', self.id)],
            'context': {'default_upload_file_id': self.id},
        }
    
    def action_view_rejected_records(self):
        return {
            'name': 'Rejected Members',
            'type': 'ir.actions.act_window',
            'res_model': 'credit.member.upload.line',
            'view_mode': 'tree',
            'view_id': self.env.ref('customer.view_credit_member_upload_line_tree').id,
            'domain': [('upload_file_id', '=', self.id), ('upload_member_status', '=', 'rejection')],
            'context': {'default_upload_file_id': self.id},
        }
        
# ------------------------------------------------------------------------------------
class CreditMemberUploadLine(models.Model):
    _name = 'credit.member.upload.line'
    _description = 'Credit Member upload Line'

    upload_file_id = fields.Many2one('credit.member.upload', string='Upload File')
    
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
