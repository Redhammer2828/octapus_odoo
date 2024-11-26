from odoo import models, fields, api

class EnquiryComplaintWizard(models.TransientModel):
    _name = 'enquiry.complaint.wizard'
    _description = 'Enquiry or Complaint Wizard'

    # This field will only serve as an indicator to set Enquiry or Complaint
    is_enquiry = fields.Boolean("Is Enquiry?", default=True)
    enq_cm_id= fields.Many2one('aaa.enquiry', string="ENQ_COMPL")

    def action_enquiry(self):
        # Set the field visibility to Enquiry in the main form
        active_id = self.env.context.get('active_id')
        enquiry_record = self.env['aaa.enquiry'].browse(active_id)
        enquiry_record.is_enquiry = True  # Set the flag for enquiry
        enquiry_record.show_enquiry_fields = True  # Show enquiry-related fields
        enquiry_record.show_complaint_fields = False  # Hide complaint-related fields
        return {'type': 'ir.actions.act_window_close'}

    def action_complaint(self):
        # Set the field visibility to Complaint in the main form
        active_id = self.env.context.get('active_id')
        enquiry_record = self.env['aaa.enquiry'].browse(active_id)
        enquiry_record.is_enquiry = False  # Set the flag for complaint
        enquiry_record.show_enquiry_fields = False  # Hide enquiry-related fields
        enquiry_record.show_complaint_fields = True  # Show complaint-related fields
        return {'type': 'ir.actions.act_window_close'}
