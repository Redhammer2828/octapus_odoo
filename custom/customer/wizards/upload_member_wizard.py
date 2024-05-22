import io
import base64
import pandas as pd
from odoo import models, fields, api

class UploadMemberWizard(models.TransientModel):
    _name = 'upload.member.wizard'
    _description = 'Policy Member Upload Wizard'

    name = fields.Char(string="Name", required=True)
    file_type = fields.Selection([('excel', 'Excel'), ('csv', 'CSV')], string="File Type", required=True)
    file = fields.Binary(string="File")
    type = fields.Char(string="Type", invisible=True)  # Assuming you need this field for processing

    def action_policy_member_upload_excel(self):
        # Ensure the file is provided
        if not self.file:
            return {'warning': {'title': 'Warning', 'message': 'Please select a file to upload.'}}

        # Decode the file data and create a pandas DataFrame
        file_content = base64.b64decode(self.file)
        try:
            excel_data = pd.read_excel(io.BytesIO(file_content))
        except Exception as e:
            return {'warning': {'title': 'Error', 'message': f'Error reading Excel file: {e}'}}

        # Prepare data for creating upload.member.line records
        member_lines = []
        for index, row in excel_data.iterrows():
            member_line_data = {
                'card_type':  row['card_type'],
                'old_membership_number':  row['old_membership_number'],
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
                'vehicle_chasis_no': row.get('vehicle_chasis_no'),
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
            member_lines.append((0, 0, member_line_data))

        # Create data.upload.file record
        data_upload_file = self.env['data.upload.file'].create({
            'name': self.name,
            'file_type': self.file_type,
            'file': self.file,
            'state': 'draft',  # Default state
            'upload_member_ids': member_lines  # Assign member lines to the One2many field
        })

        # Return action to open form view of the newly created record
        return {
            'name': 'Data Upload File',
            'type': 'ir.actions.act_window',
            'res_model': 'data.upload.file',
            'view_mode': 'form',
            'res_id': data_upload_file.id,  # Assuming data_upload_file is the created record
            'target': 'current',  # Open in the same window
        }
    
    def action_policy_member_upload_csv(self):
        pass
