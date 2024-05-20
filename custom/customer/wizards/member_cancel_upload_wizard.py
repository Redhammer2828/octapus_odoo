import io
import base64
import pandas as pd
from odoo import models, fields, api

class MemberCancelUploadWizard(models.TransientModel):
    _name = "member.cancel.upload.wizard"
    _description = "Policy Member Cancellation Wizard"

    name = fields.Char(string="Name", required=True)
    file_type = fields.Selection([('excel', 'Excel'), ('csv', 'CSV')], string="File Type", required=True)
    file = fields.Binary(string="File")
    type = fields.Char(string="Type", invisible=True) 

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
        member_cancel_lines = []
        for index, row in excel_data.iterrows():
            member_line_data = {
                'customer_code': row.get('customer_code'),
                'vehicle_chasis_no': row.get('vehicle_chasis_no'),
                'cancellation_date': row.get('cancellation_date'),
                'comment': row.get('comments')
                # Add other fields from the Excel file as needed
            }
            member_cancel_lines.append((0, 0, member_line_data))

        # Create member.upload.cancel record
        member_upload_cancel = self.env['member.upload.cancel'].create({
            'name': self.name,
            'file_type': self.file_type,
            'file': self.file,
            'state': 'draft',  # Default state
            'upload_member_ids': member_cancel_lines  # Assign member lines to the One2many field
        })

        # Return action to open form view of the newly created record
        return {
            'name': 'Member Upload Cancel',
            'type': 'ir.actions.act_window',
            'res_model': 'member.upload.cancel',
            'view_mode': 'form',
            'res_id': member_upload_cancel.id,  # Assuming data_upload_file is the created record
            'target': 'current',  # Open in the same window
        }
    
    def action_policy_member_upload_csv(self):
        pass