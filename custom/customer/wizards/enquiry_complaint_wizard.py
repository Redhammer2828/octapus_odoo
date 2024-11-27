from odoo import models, fields, api

class EnquiryComplaintWizard(models.TransientModel):
    _name = 'enquiry.complaint.wizard'
    _description = 'Enquiry or Complaint Wizard'

    is_enquiry = fields.Boolean("Is Enquiry?", default=True)
    enq_cm_id = fields.Many2one('aaa.enquiry', string="ENQ_COMPL")

    def action_enquiry(self):
        """Open the enquiry form and ensure no default values are prefetched."""
        active_id = self.env.context.get('default_enq_cm_id')
        enquiry_record = self.env['aaa.enquiry'].browse(active_id)

        # Set flags to ensure correct fields are shown
        enquiry_record.write({
            'is_enquiry': True,
            'show_enquiry_fields': True,
            'show_complaint_fields': False,
            'enquiry_type_id': False,   # Reset any potentially set fields
            'enquiries_id': False,     # Reset subtypes for enquiry
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
        """Open the complaint form and ensure no default values are prefetched."""
        active_id = self.env.context.get('default_enq_cm_id')
        enquiry_record = self.env['aaa.enquiry'].browse(active_id)

        # Set flags to ensure correct fields are shown
        enquiry_record.write({
            'is_enquiry': False,
            'show_enquiry_fields': False,
            'show_complaint_fields': True,
            'complaint_type_id': False,  # Reset any potentially set fields
            'complaints_id': False,      # Reset subtypes for complaints
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
