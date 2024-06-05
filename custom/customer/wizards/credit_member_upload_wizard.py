import io
import base64
import pandas as pd
import re
from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import UserError

class MemberCancelUploadWizard(models.TransientModel):
    _name = "credit.member.upload.wizard"
    _description = "Credit Member Upload Wizard"

    name = fields.Char(string="Name", required=True)
    file_type = fields.Selection([('excel', 'Excel'), ('csv', 'CSV')], string="File Type",default='excel', required=True)
    file = fields.Binary(string="File")
    file_name = fields.Char(string="File Name", readonly=True)
    type = fields.Char(string="Type", invisible=True) 

    def action_credit_member_upload_excel(self):
        # Ensure the file is provided
        if not self.file:
            return {'warning': {'title': 'Warning', 'message': 'Please select a file to upload.'}}

        # Decode the file data and create a pandas DataFrame
        file_content = base64.b64decode(self.file)
        try:
            excel_data = pd.read_excel(io.BytesIO(file_content))
        except Exception as e:
            return {'warning': {'title': 'Error', 'message': f'Error reading Excel file: {e}'}}

                # Excel validation Check 
        required_fields = ['vehicle_chasis_no', 'name', 'customer_code', 'member_expiry_date', 'member_activate_date', 'mobile']
        seen_vehicle_chasis_no = set()
        errors = []
        date_format_regex = re.compile(r'^\d{2}/\d{2}/\d{4}$')


        # Prepare data for creating upload.member.line records
        credit_member_lines = []
        for index, row in excel_data.iterrows():
            row_errors = []

            for field in required_fields:
                if pd.isna(row.get(field)) or row.get(field) == '':
                    row_errors.append(f'Field "{field}" is required and cannot be empty. Row: {index + 1}.')

            for date_field in ['member_expiry_date', 'member_activate_date']:
                date_value = row.get(date_field)
                if pd.notna(date_value):
                    if isinstance(date_value, (pd.Timestamp, datetime)):
                        date_value = date_value.strftime('%d/%m/%Y')
                    if not isinstance(date_value, str) or not date_format_regex.match(date_value):
                        row_errors.append(f'Field "{date_field}" must be in dd/mm/yyyy format. Row: {index + 1}.')

            vehicle_chasis_no = row.get('vehicle_chasis_no')

            if vehicle_chasis_no in seen_vehicle_chasis_no:
                row_errors.append(f'Duplicate value "{vehicle_chasis_no}" found in "vehicle_chasis_no". Row: {index + 1}.')
            else:
                seen_vehicle_chasis_no.add(vehicle_chasis_no)

            if row_errors:
                errors.extend(row_errors)
                continue

            member_line_data = {
                'card_type': row['card_type'],
                'old_membership_number': row['old_membership_number'],
                'member_name': row.get('name'),
                'mobile': row.get('mobile'),
                'street': row.get('address'),
                'state': row.get('emirate'),
                'country': row.get('country'),
                'zip': row.get('zip'),
                'region_code': row.get('region_code'),
                'vehicle_type': row.get('vehicle_type'),
                'vehicle_model': row.get('vehicle_model'),
                'vehicle_mfg_year': row.get('vehicle_mfg_year'),
                'vehicle_plate': row.get('vehicle_plate'),
                'mail_ref': row.get('mail_ref'),
                'vehicle_reg_code': row.get('vehicle_reg_code'),
                'vehicle_chasis_no': vehicle_chasis_no,
                'policy_no': row.get('policy_no'),
                'vehicle_reg_country': row.get('vehicle_reg_country'),
                'vehicle_emirate': row.get('vehicle_emirate'),
                'delivery_ref_date': row.get('delivery_date'),
                'invoice_ref_date': row.get('invoice_ref_date'),
                'member_expiry_date': row.get('member_expiry_date'),
                'member_activate_date': row.get('member_activate_date'),
                'comment': row.get('remarks'),
                'package': row.get('package_id'),
                'customer_code': row.get('customer_code'),
                'sequence_code': row.get('category_code'),
                # Add other fields from the Excel file as needed
            }
            credit_member_lines.append((0, 0, member_line_data))
        
        if errors:
            error_message = "\n".join(errors)
            raise UserError(f'Errors found in the uploaded file:\n{error_message}')

        # Create member.upload.cancel record
        credit_member_upload = self.env['credit.member.upload'].create({
            'name': self.name,
            'file_type': self.file_type,
            'file': self.file,
            'state': 'draft',  # Default state
            'upload_member_ids': credit_member_lines  # Assign member lines to the One2many field
        })

        # Return action to open form view of the newly created record
        return {
            'name': 'Credit Member Upload',
            'type': 'ir.actions.act_window',
            'res_model': 'credit.member.upload',
            'view_mode': 'form',
            'res_id': credit_member_upload.id,  # Assuming data_upload_file is the created record
            'target': 'current',  # Open in the same window
        }
    
    def action_credit_member_upload_csv(self):
        pass