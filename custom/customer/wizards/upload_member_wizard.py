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
                'member_name': row.get('name'),
                'mobile': row.get('mobile'),
                # Add other fields from the Excel file as needed
            }
            member_lines.append(member_line_data)
        
        data_upload_file = self.env['data.upload.file'].create({
            'name': self.name,
            'file_type': self.file_type,
            'file': self.file,
            'state': 'draft',  # Default state
        })
        
        # Create upload.member.line records
        try:
            self.env['upload.member.line'].create(member_lines)
        except Exception as e:
            return {'warning': {'title': 'Error', 'message': f'Error creating member lines: {e}'}}

        # Return a message indicating success
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
