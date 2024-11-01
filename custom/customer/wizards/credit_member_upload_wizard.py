import io
import base64
import pandas as pd
from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import UserError
from concurrent.futures import ThreadPoolExecutor

class CreditMemberUploadWizard(models.TransientModel):
    _name = "credit.member.upload.wizard"
    _description = "Credit Member Upload Wizard"

    name = fields.Char(string="Name", required=True)
    file_type = fields.Selection([('excel', 'Excel')], string="File Type", default='excel', required=True)
    file = fields.Binary(string="File")
    file_name = fields.Char(string="File Name", readonly=True)
    type = fields.Char(string="Type", invisible=True)

    def action_credit_member_upload_excel(self):
        if not self.file:
            raise UserError('Please select a file to upload.')

        # Decode and read the Excel file
        file_content = base64.b64decode(self.file)
        try:
            excel_data = pd.read_excel(io.BytesIO(file_content))
        except Exception as e:
            raise UserError(f'Error reading Excel file: {e}')

        required_fields = [
            'vehicle_chasis_no', 'name', 'customer_code', 
            'member_expiry_date', 'card_type', 'country', 
            'invoice_ref_date', 'category_code'
        ]
        errors = []
        date_format = '%d-%m-%Y'  # Expected date format
        credit_member_lines = []

        # Pre-fetch necessary data to avoid redundant ORM calls
        existing_member_codes = set(self.env['credit.member.upload.line'].search([]).mapped('customer_code'))

        def process_row(index, row):
            row_errors = []
            member_line_data = {}

            # Validate required fields
            for field in required_fields:
                if pd.isna(row.get(field)) or row.get(field) == '':
                    row_errors.append(f'Field "{field}" is required and cannot be empty. Row: {index + 2}.')

            # Process date fields
            date_fields = ['delivery_ref_date', 'member_expiry_date', 'member_activate_date', 'invoice_ref_date']
            for date_field in date_fields:
                date_value = row.get(date_field)
                if pd.notna(date_value):
                    if isinstance(date_value, str):
                        try:
                            date_value = datetime.strptime(date_value, date_format).strftime('%Y-%m-%d')
                        except ValueError:
                            row_errors.append(f'Field "{date_field}" contains an invalid date. Row: {index + 2}.')
                    elif isinstance(date_value, (pd.Timestamp, datetime)):
                        date_value = date_value.strftime('%Y-%m-%d')
                else:
                    date_value = None  # Handle missing dates

                row[date_field] = date_value  # Save converted date back to the row

            if row_errors:
                return row_errors, None

            # Prepare data for the credit.member.line record
            member_line_data = {
                'card_type': row.get('card_type'),
                'old_membership_number': row.get('old_membership_number'),
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
            }
            return [], member_line_data

        # Use thread pool for parallel processing of rows
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_row, index, row) for index, row in excel_data.iterrows()]
            for future in futures:
                row_errors, member_line = future.result()
                if row_errors:
                    errors.extend(row_errors)
                elif member_line:
                    credit_member_lines.append((0, 0, member_line))

        if errors:
            error_message = "\n\n".join(errors)
            raise UserError(f'Errors found in the uploaded file:\n{error_message}')

        # Create the credit.member.upload record
        credit_member_upload = self.env['credit.member.upload'].create({
            'name': self.name,
            'file_type': self.file_type,
            'file': self.file,
            'state': 'draft',
            'upload_member_ids': credit_member_lines
        })

        return {
            'name': 'Credit Member Upload',
            'type': 'ir.actions.act_window',
            'res_model': 'credit.member.upload',
            'view_mode': 'form',
            'res_id': credit_member_upload.id,
            'target': 'current',
        }

    def action_credit_member_upload_csv(self):
        pass
