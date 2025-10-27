import io
import base64
import pandas as pd
import re
from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import UserError
from concurrent.futures import ThreadPoolExecutor

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

        # Check for duplicates in 'vehicle_chasis_no'
        if 'vehicle_chasis_no' not in excel_data.columns:
            raise UserError('The Excel file must contain the "vehicle_chasis_no" column.')

        # Clean and uppercase vehicle_chasis_no before duplicate check
        excel_data['vehicle_chasis_no'] = excel_data['vehicle_chasis_no'].apply(
            lambda x: str(x).strip().upper() if pd.notna(x) and x != '' else x
        )

        duplicated = excel_data['vehicle_chasis_no'].duplicated(keep=False)
        if duplicated.any():
            duplicate_rows = excel_data[duplicated]
            duplicate_errors = []
            for index, row in duplicate_rows.iterrows():
                duplicate_errors.append(
                    f'Duplicate vehicle_chasis_no "{row["vehicle_chasis_no"]}" found in row {index + 2}.'
                )
            error_message = "\n".join(duplicate_errors)
            raise UserError(f'Duplicates found in the uploaded file:\n{error_message}')

        # Pre-fetch valid data for validation
        valid_country_codes = set(self.env['country.code'].search([]).mapped('c_code'))
        # valid_category_codes = set(self.env['partner.category'].search([]).mapped('name'))
        
        # Fetch valid category codes based on conditions
        # valid_category_codes = set(self.env['partner.category'].search([
        #     ('member_type', '=', 'policy'),
        #     ('partner_id', 'in', self.env['res.partner'].search([('customer_code', 'in', excel_data['customer_code'].unique())]).ids)
        # ]).mapped('name'))

        # Ensure customer_code is a Python list
        customer_codes = excel_data['customer_code'].dropna().unique().tolist()
        print("CUSTOMER CODE",customer_codes)
        # Search for partner IDs
        partner_ids = self.env['res.partner'].search([('customer_code', 'in', customer_codes)]).ids
        partner_id = partner_ids[0]
        print("PARTNER CODE",partner_id)
        # Use partner_ids in the second search query
        valid_category_codes = set(
            self.env['partner.category'].search([
                ('member_type', '=', 'policy'),
                ('partner_id', '=', partner_ids)
            ]).mapped('name')
        )
        print("CATEGORY CODE",valid_category_codes)
        valid_package_ids = set(self.env['product.template'].search([]).mapped('id'))

        # Define required fields and regex patterns
        required_fields = [
            'vehicle_chasis_no', 'name', 'customer_code', 'member_expiry_date', 'card_type', 
            'country', 'invoice_ref_date', 'package_id', 'category_code'
        ]
        date_format = '%d-%m-%Y'
        seen_vehicle_chasis_no = set()

        errors = []
        member_lines = []

        # Fetching relevant product.template records where bundle_product = True
        bundle_product_ids = self.env['product.template'].search([('bundle_product', '=', True)]).ids

        def process_row(row, index):
            row_errors = []
            # Check required fields
            for field in required_fields:
                if pd.isna(row.get(field)) or row.get(field) == '':
                    row_errors.append(f'Field "{field}" is required and cannot be empty. Row: {index + 2}.')

            # Validate category code
            category_code = row.get('category_code')
            if category_code and category_code not in valid_category_codes:
                row_errors.append(f'Invalid category code "{category_code}" in row {index + 2}.')

            # Validate package_id against bundle_product_ids
            package_id = row.get('package_id')
            if package_id and int(package_id) not in bundle_product_ids:
                row_errors.append(f'Invalid package_id "{package_id}" in row {index + 2}. Must be one of the package ids in the Package list.')

            # Date fields to be converted
            date_fields = ['delivery_ref_date', 'member_expiry_date', 'invoice_ref_date', 'member_activate_date']

            for date_field in date_fields:
                date_value = row.get(date_field)
                if pd.notna(date_value) and date_value != "":
                    if isinstance(date_value, str):
                        try:
                            date_value = datetime.strptime(date_value, date_format).strftime('%Y-%m-%d')
                        except ValueError:
                            row_errors.append(f'Field "{date_field}" contains an invalid date. Row: {index + 2}.')
                    elif isinstance(date_value, (pd.Timestamp, datetime)):
                        date_value = date_value.strftime('%Y-%m-%d')
                else:
                    date_value = None
                    if date_field == 'member_activate_date':  # Check for member_activate_date being empty
                        row_errors.append(f'Member activate date is required. Row: {index + 2}.')

                row[date_field] = date_value

            # Clean and uppercase vehicle_chasis_no
            vehicle_chasis_no = row.get('vehicle_chasis_no')
            if vehicle_chasis_no and isinstance(vehicle_chasis_no, str):
                vehicle_chasis_no = vehicle_chasis_no.strip().upper()
                row['vehicle_chasis_no'] = vehicle_chasis_no

            # Optionally, check for duplicates in the database
            # Uncomment the following lines if you want to check duplicates against existing records
            """
            vehicle_chasis_no = row.get('vehicle_chasis_no')
            if vehicle_chasis_no:
                existing_member = self.env['policy.member'].search([('vehicle_chasis_no', '=', vehicle_chasis_no)], limit=1)
                if existing_member:
                    row_errors.append(f'vehicle_chasis_no "{vehicle_chasis_no}" already exists in the database. Row: {index + 2}.')
            """

            if row_errors:
                return row_errors, None

            member_line_data = {
                'card_type': row['card_type'],
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
                'remarks': row.get('remarks'),
                'package': row.get('package_id'),
                'customer_code': row.get('customer_code'),
                'sequence_code': row.get('category_code'),
            }
            return [], member_line_data

        # Using thread pool for parallel processing
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_row, row, index) for index, row in excel_data.iterrows()]
            for future in futures:
                row_errors, member_line = future.result()
                if row_errors:
                    errors.extend(row_errors)
                else:
                    member_lines.append((0, 0, member_line))
        if errors:
            error_message = "\n".join(errors)
            raise UserError(f'Errors found in the uploaded file:\n{error_message}')

        # Bulk create member lines
        data_upload_file = self.env['data.upload.file'].create({
            'name': self.name,
            'file_type': self.file_type,
            'file': self.file,
            'file_name': self.file_name,
            'state': 'draft',
            'upload_member_ids': member_lines
        })

        return {
            'name': 'Data Upload File',
            'type': 'ir.actions.act_window',
            'res_model': 'data.upload.file',
            'view_mode': 'form',
            'res_id': data_upload_file.id,
            'target': 'current',
        }

    def action_policy_member_upload_csv(self):
        pass