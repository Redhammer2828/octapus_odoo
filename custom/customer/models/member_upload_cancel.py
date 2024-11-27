from odoo import models, fields ,api
from odoo.exceptions import ValidationError
from collections import Counter
import time
import pickle
import base64

class MemberUploadCancel(models.Model):
    _name = 'member.upload.cancel'
    _description = 'Member Upload Cancel'

    name = fields.Char(string='Name', required=True)
    file = fields.Binary(string='File')
    file_type = fields.Char('File Type')

    date = fields.Datetime('Uploaded Date', default=lambda self: fields.Datetime.now())
    upload_by = fields.Many2one('res.users', string='Uploaded By', default=lambda self: self.env.user)
    upload_log = fields.Text( string='Log')
    upload_member_ids = fields.One2many('member.upload.cancel.line', 'upload_file_id', string='Members')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('validate', 'Validated'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft')

    temp_store = fields.Text(string='Temporary Store', default='{}')

    def action_validate_policy_data(self):
        start_time = time.time()
        temp_dict = {}

        # Fetch all customer codes and their associated partners at once
        customer_codes = self.upload_member_ids.mapped('customer_code')
        partner_records = self.env['res.partner'].search([('customer_code', 'in', customer_codes)])
        partner_dict = {partner.customer_code: partner for partner in partner_records}

        # Fetch all members linked to the fetched partners
        member_records = self.env['res.partner'].search([
            ('parent_customer_id', 'in', partner_records.ids),
            ('membership_state', '=', 'confirm')
        ])
        member_dict = {(member.parent_customer_id.id, member.vehicle_chasis_no.strip().upper()): member for member in member_records}

        # Process each member line
        for member_line in self.upload_member_ids:
            print("Processing member_line:", member_line)

            matching_partner = partner_dict.get(member_line.customer_code)
            if matching_partner:
                key = (matching_partner.id, member_line.vehicle_chasis_no.strip().upper())
                matched_member = member_dict.get(key)
                if matched_member:
                    print("Match found for member ID:", matched_member.id)
                    self.check_member_details(matched_member, member_line)
                    temp_dict[matched_member.id] = member_line.id
                else:
                    member_line.update({'upload_status': 'invalid', 'comment': "*No Matching Record Found in System"})
            else:
                member_line.update({'upload_status': 'invalid', 'comment': "*No Matching Record Found in System"})

        # Calculate processing time
        end_time = time.time()
        processing_time = end_time - start_time

        # Calculate counts
        total_count = len(self.upload_member_ids)
        invalid_count = len(self.upload_member_ids.filtered(lambda m: m.upload_status == 'invalid'))
        cancelled_count = len(self.upload_member_ids.filtered(lambda m: m.upload_status == 'cancellation'))

        self.upload_log = f"Total Records: {total_count} | Invalid Records: {invalid_count} | Cancelled Records: {cancelled_count} | Time to Process: {processing_time:.2f} seconds"
        
        # Store data with pickle and base64 encoding
        self.temp_store = base64.b64encode(pickle.dumps(temp_dict)).decode('utf-8')
        self.state = 'validate'

    def check_member_details(self, member, member_line):
        excel_chassis_no = member_line.vehicle_chasis_no.strip().upper()
        db_chassis_no = member.vehicle_chasis_no.strip().upper()
        if excel_chassis_no == db_chassis_no and member.membership_state == 'confirm':
                print("[PASS Chasis Check")

                member_line.update({
                'upload_status': 'cancellation',
                'comment': member_line.comment  # Update comment with the value from Excel
                })
        else:
            print("FAIL Vehicle Chasis check")

    def action_cancel(self):
        self.state = 'draft'

    def apply_member_upload_wizard(self):
        # Load data with base64 decoding and pickle
        temp_dict = pickle.loads(base64.b64decode(self.temp_store.encode('utf-8')))
        members = self.env['res.partner'].browse(list(temp_dict.keys()))
        member_lines = self.env['member.upload.cancel.line'].browse(list(temp_dict.values()))

        for member, member_line in zip(members, member_lines):
            member.write({
                'membership_cancel_date': member_line.cancellation_date,
                'membership_state': 'cancel'
            })
        self.state = 'done'

# --------------------------------------------------------------------------------------------------
class MemberUploadCancelLine(models.Model):
    _name = 'member.upload.cancel.line'
    _description = 'Member Upload Cancel Line'

    upload_file_id = fields.Many2one('member.upload.cancel', string='Upload File')
    
    customer_code = fields.Char(string='Customer Code')
    vehicle_chasis_no = fields.Char(string='Vehicle Chassis No')
    cancellation_date = fields.Date(string='Cancellation Date')
    comment = fields.Text(string='Comment')

    upload_status = fields.Selection([
        ('draft', 'To Validate'),
        ('invalid', 'Invalid Date'),
        ('cancellation', 'Validated')
    ], string='Upload Status',default='draft')
   
    upload_member_status = fields.Selection([
        ('new', 'New Member'),
        ('rejection', 'Rejected Member'),
        ('renewal', 'Renewal Member'),
        ('update', 'Update Member'),
        ('exist_temp', 'Exist in Temp')
    ], string='Upload Status')
    # --------------------------------------------------------------------


