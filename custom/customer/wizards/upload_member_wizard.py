import io
import base64
import pandas as pd
import re
from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import UserError

class UploadMemberWizard(models.TransientModel):
    _name = 'upload.member.wizard'
    _description = 'Policy Member Upload Wizard'

    name = fields.Char(string="Name", required=True)
    file_type = fields.Selection([('excel', 'Excel'), ('csv', 'CSV')], string="File Type", default='excel', required=True)
    file = fields.Binary(string="File", required=True)
    file_name = fields.Char(string="File Name", readonly=True)
    type = fields.Char(string="Type", invisible=True)

    def action_policy_member_upload_excel(self):
        if not self.file:
            raise UserError('Please select a file to upload.')

        # Decode the file content
        file_content = base64.b64decode(self.file)
        try:
            excel_data = pd.read_excel(io.BytesIO(file_content))
            excel_data.fillna('', inplace=True)
        except Exception as e:
            raise UserError(f'Error reading Excel file: {e}')

        # Pre-fetch valid data for validation
        valid_country_codes = set(self.env['country.code'].search([]).mapped('c_code'))
        valid_category_codes = set(self.env['partner.category'].search([]).mapped('name'))
        valid_package_ids = set(self.env['product.template'].search([]).mapped('id'))

        # Define required fields and regex patterns
        required_fields = [
            'vehicle_chasis_no', 'name', 'customer_code', 'member_expiry_date', 'card_type', 
            'country', 'invoice_ref_date', 'package_id', 'category_code'
        ]
        date_format_regex = re.compile(r'^\d{2}/\d{2}/\d{4}$')
        seen_vehicle_chasis_no = set()

        errors = []
        member_lines = []

        # Iterate over the rows in the Excel data
        for index, row in excel_data.iterrows():
            row_errors = []
            mobile_str = ""

            # Check required fields
            for field in required_fields:
                if pd.isna(row.get(field)) or row.get(field) == '':
                    row_errors.append(f'Field "{field}" is required and cannot be empty. Row: {index + 2}.')

            # Validate date fields
            for date_field in ['member_expiry_date', 'member_activate_date', 'invoice_ref_date']:
                date_value = row.get(date_field)
                if pd.notna(date_value):
                    if isinstance(date_value, (pd.Timestamp, datetime)):
                        date_value = date_value.strftime('%d/%m/%Y')
                    if not isinstance(date_value, str) or not date_format_regex.match(date_value):
                        row_errors.append(f'Field "{date_field}" must be in dd/mm/yyyy format. Row: {index + 2}.')

            # Check for duplicate vehicle chassis numbers
            vehicle_chasis_no = row.get('vehicle_chasis_no')
            if vehicle_chasis_no in seen_vehicle_chasis_no:
                row_errors.append(f'Duplicate value "{vehicle_chasis_no}" found in "vehicle_chasis_no". Row: {index + 2}.')
            else:
                seen_vehicle_chasis_no.add(vehicle_chasis_no)
# -----------------------------------TEMPORARY REMOVAL--------------------------------------------------------------------
            # Validate mobile field
            # mobile = row.get('mobile')
            # if mobile and pd.notna(mobile):
            #     mobile_str = str(mobile).strip().split(".")[0]
            #     if not mobile_str.isdigit():
            #         row_errors.append(f'Field "mobile" must contain only numbers. Row: {index + 2}.')
            # if len(mobile_str) == 1 or set(mobile_str) == {'0'}:
            #     row_errors.append(f'Field "mobile" must not be a single digit or only zeros. Row: {index + 2}.')
# ------------------------------------------------------------------------------------------------------------------------
            # Validate country code
            country_code = row.get('country')
            if pd.notna(country_code) and country_code not in valid_country_codes:
                row_errors.append(f'Invalid country code "{country_code}". Row: {index + 2}.')

            # Validate category code
            category_code = row.get('category_code')
            if pd.notna(category_code) and category_code not in valid_category_codes:
                row_errors.append(f'Invalid category code "{category_code}". Row: {index + 2}.')

            # Validate package ID
            package_id = row.get('package_id')
            if pd.notna(package_id) and package_id not in valid_package_ids:
                row_errors.append(f'Invalid Package ID "{package_id}". Row: {index + 2}.')

            # If any errors are found for the current row, accumulate them and skip to the next row
            if row_errors:
                errors.extend(row_errors)
                continue

            # Prepare data for creating member lines
            member_line_data = {
                'card_type': row['card_type'],
                'old_membership_number': row.get('old_membership_number'),
                'member_name': row.get('name'),
                # Changed for mobile
                # 'mobile': mobile_str, 
                # Changed for mobile temprory
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
                'remarks': row.get('remarks'),
                'package': row.get('package_id'),
                'customer_code': row.get('customer_code'),
                'sequence_code': row.get('category_code'),
            }
            member_lines.append((0, 0, member_line_data))

        # Raise accumulated errors if any
        if errors:
            error_message = "\n".join(errors)
            raise UserError(f'Errors found in the uploaded file:\n{error_message}')

        # Create data upload file record
        data_upload_file = self.env['data.upload.file'].create({
            'name': self.name,
            'file_type': self.file_type,
            'file': self.file,
            'file_name': self.file_name,
            'state': 'draft',
            'upload_member_ids': member_lines
        })

        # Return the form view of the created record
        return {
            'name': 'Data Upload File',
            'type': 'ir.actions.act_window',
            'res_model': 'data.upload.file',
            'view_mode': 'form',
            'res_id': data_upload_file.id,
            'target': 'current',
        }

    def action_policy_member_upload_csv(self):
        # Implementation for CSV upload can be added here
        pass
