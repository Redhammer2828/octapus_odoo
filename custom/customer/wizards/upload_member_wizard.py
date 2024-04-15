from odoo import models, fields, api

class UploadMemberWizard(models.Model):
    _name = 'upload.member.wizard'
    _description = 'Policy Member Upload'

    name = fields.Char(string="Name", required=True)
    file_type = fields.Selection([('excel', 'Excel'), ('csv', 'CSV')], string="File Type", required=True)
    file = fields.Binary(string="File")
    type = fields.Char(string="Type", invisible=True)  # Assuming you need this field for processing

    def action_policy_member_upload_excel(self):
        pass

    def action_policy_member_upload_csv(self):
        pass