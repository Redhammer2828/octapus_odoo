from odoo import models, fields, api

class UploadMemberWizard(models.Model):
    _name = 'upload.member.wizard'
    _description = 'Policy Member Upload'

    name = fields.Char(string="Name", required=True)
    file_type = fields.Selection([('excel', 'Excel'), ('csv', 'CSV')], string="File Type", required=True)
    file = fields.Binary(string="File")
    type = fields.Char(string="Type", invisible=True)  # Assuming you need this field for processing

    def action_policy_member_upload_excel(self):
        self.ensure_one()  # Ensure only one record is processed

        if self.file:
            try:
                # Decode binary data to bytes
                file_data = self.env['base.binary'].decode_file(self.file)
                # Read Excel data using pandas
                excel_data = pd.read_excel(file_data)

                # Process and create partner records (replace with your logic)
                for index, row in excel_data.iterrows():
                    # Extract relevant data from each row (e.g., name, address, etc.)
                    name = row['Name']  # Assuming a column named 'Name' exists
                    # ... (other data extraction) ...

                    # Create a new partner record
                    partner_vals = {
                        'name': name,
                        # ... (other partner fields based on extracted data) ...
                    }
                    self.env['res.partner'].create(partner_vals)

                return {'type': 'ir.actions.act_window_close'}  # Close the wizard

            except Exception as e:
                return self.env['user.message'].post_template(
                    'policy_member_upload.error_import_excel',
                    message=f'Error reading Excel file: {e}',
                    duration=10
                )
        else:
            return self.env['user.message'].post_template(
                'policy_member_upload.error_no_file',
                message='Please select a file to upload!',
                duration=10
            )


    def action_policy_member_upload_csv(self):
        # Assuming you want to process CSV files
        # You can replace this logic with your actual implementation
        data = self.file  # Binary data of the uploaded file
        # Process the CSV file data (e.g., using Python's csv module)
        # For demonstration purposes, let's just print the file data
        print("Uploaded CSV file:", data)