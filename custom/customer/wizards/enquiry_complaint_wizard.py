from odoo import models, fields, api

class EnquiryComplaintWizard(models.TransientModel):
    _name = 'enquiry.complaint.wizard'
    _description = 'Enquiry or Complaint Wizard'

    is_enquiry = fields.Boolean("Is Enquiry?", default=True)
    enq_cm_id = fields.Many2one('aaa.enquiry', string="ENQ_COMPL")

    def action_enquiry(self):
        """Open the enquiry form for a new record with no prefilled data."""
        # Create a new enquiry record with appropriate field visibility settings
        enquiry_record = self.env['aaa.enquiry'].create({
            'is_enquiry': True,
            'show_enquiry_fields': True,
            'show_complaint_fields': False,
            'enquiry_type_id': False,   # Ensure these fields are empty
            'enquiries_id': False,     # Ensure these fields are empty
            'state': 'draft',          # Default state is 'draft'
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'aaa.enquiry',
            'view_mode': 'form',
            'res_id': enquiry_record.id,
            'target': 'current',
            'context': self._clear_context(),
        }

    def action_complaint(self):
        """Open the complaint form for a new record with no prefilled data."""
        # Create a new complaint record with appropriate field visibility settings
        enquiry_record = self.env['aaa.enquiry'].create({
            'is_enquiry': False,
            'show_enquiry_fields': False,
            'show_complaint_fields': True,
            'complaint_type_id': False,  # Ensure these fields are empty
            'complaints_id': False,      # Ensure these fields are empty
            'state': 'draft',            # Default state is 'draft'
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'aaa.enquiry',
            'view_mode': 'form',
            'res_id': enquiry_record.id,
            'target': 'current',
            'context': self._clear_context(),
        }

    def _clear_context(self):
        """Clears default values from context."""
        return {
            'default_enquiry_type_id': False,
            'default_enquiries_id': False,
            'default_complaint_type_id': False,
            'default_complaints_id': False,
        }

    
