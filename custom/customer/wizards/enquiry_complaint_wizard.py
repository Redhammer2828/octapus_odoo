from odoo import models, fields, api

class EnquiryComplaintWizard(models.TransientModel):
    _name = 'enquiry.complaint.wizard'
    _description = 'Enquiry or Complaint Wizard'

    # This field will serve as an indicator to set Enquiry or Complaint
    is_enquiry = fields.Boolean("Is Enquiry?", default=True)
    enq_cm_id = fields.Many2one('aaa.enquiry', string="ENQ_COMPL")  # Reference to the enquiry record

    def action_enquiry(self):
        # Handle setting the form to 'Enquiry' type
        active_id = self.env.context.get('default_enq_cm_id')  # Get the enquiry record ID passed from the context
        enquiry_record = self.env['aaa.enquiry'].browse(active_id)
        
        # Update the enquiry record: set it as enquiry and show related fields
        enquiry_record.is_enquiry = True
        enquiry_record.show_enquiry_fields = True  # Show fields related to enquiry
        enquiry_record.show_complaint_fields = False  # Hide fields related to complaints

        # Optional: Set default values related to enquiries (e.g., enquiry type, subtypes)
        # enquiry_record.enquiry_type_id = self.env['enquiry.config'].search([], limit=1).id
        # enquiry_record.enquiries_id = self.env['enquiry.subtype'].search([], limit=1).id

        # Close the wizard and open the enquiry form
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'aaa.enquiry',
            'view_mode': 'form',
            'res_id': enquiry_record.id,
            'target': 'current',
        }

    def action_complaint(self):
        # Handle setting the form to 'Complaint' type
        active_id = self.env.context.get('default_enq_cm_id')  # Get the enquiry record ID passed from the context
        enquiry_record = self.env['aaa.enquiry'].browse(active_id)
        
        # Update the enquiry record: set it as complaint and show related fields
        enquiry_record.is_enquiry = False
        enquiry_record.show_enquiry_fields = False  # Hide fields related to enquiry
        enquiry_record.show_complaint_fields = True  # Show fields related to complaints

        # Optional: Set default values related to complaints (e.g., complaint type, subtypes)
        # enquiry_record.complaint_type_id = self.env['complaint.config'].search([], limit=1).id
        # enquiry_record.complaints_id = self.env['complaint.subtype'].search([], limit=1).id

        # Close the wizard and open the complaint form
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'aaa.enquiry',
            'view_mode': 'form',
            'res_id': enquiry_record.id,
            'target': 'current',
        }
