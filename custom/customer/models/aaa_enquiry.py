from odoo import models, fields, api
from odoo.exceptions import ValidationError , UserError

class Enquiry(models.Model):
    _name = 'aaa.enquiry'
    _description = 'Enquiry'

    enquiry = fields.Char('enquiry')
    name = fields.Char(string='Name', readonly=True)
    mem_name = fields.Char(string='Member Name')
    mobile = fields.Char(string='Mobile')
    email = fields.Char(string='Email')
    comment = fields.Text(string='Comment')
    vehicle_chasis_no = fields.Char(string='Vehicle Chasis No')
    vehicle_plate_no = fields.Char(string='Vehicle Plate No')
    membership = fields.Char(string='Membership')
    create_date = fields.Datetime(string='Create Date', readonly=True, default=fields.Datetime.now)
    created_by = fields.Many2one('res.users', string='Created By', readonly=True, default=lambda self: self.env.user)
    policy_no = fields.Char(string='Policy No')
    date = fields.Datetime(string='Create Date', readonly=True, default=fields.Datetime.now)
    
    customer_id = fields.Many2one('res.partner', string='Customer', domain="[('is_company', '=', True)]")
    member_id = fields.Many2one('res.partner', string='Member', domain="[('is_company', '=', False)]")
    service_id = fields.Many2one('product.template', string='Service', domain="[('bundle_product', '=', False)]")
 
    enq_id = fields.Many2one('aaa.service',string='Enq_Service',ondelete='cascade') #IN aaa.enquiry
    enquiry_type_id = fields.Many2one('enquiry.config', string='Enquiry Type')
    enquiries_id = fields.Many2one('enquiry.subtype', string='Enquiry Subtype', domain="[('enquiry_type_id','=',enquiry_type_id)]")
    complaint_type_id = fields.Many2one('complaint.config', string='Complaint Type')
    complaints_id = fields.Many2one('complaint.subtype', string='Complaint Subtype', domain="[('complaint_type_id','=',complaint_type_id)]" )
    
    # This field will control whether it's an enquiry or a complaint
    is_enquiry = fields.Boolean("Is Enquiry?", default=True)
    # New fields for managing visibility
    show_enquiry_fields = fields.Boolean("Show Enquiry Fields", default=True)
    show_complaint_fields = fields.Boolean("Show Complaint Fields", default=False)

    is_saved = fields.Boolean(string="Is Saved", default=False)
    readonly_comment = fields.Boolean(string="Readonly Comment", compute="_compute_readonly_comment", store=False)

    @api.depends('comment')
    def _compute_readonly_comment(self):
        """ This method will set the `readonly_comment` flag to True if the record is saved and the comment is set. """
        for record in self:
            # If record has a comment and is saved, set the flag to True
            record.readonly_comment = bool(record.comment and record.id)

    @api.model
    def create(self, vals):
        """ Overridden create method to set `is_saved` field to True after the record is created """
        record = super(Enquiry, self).create(vals)
        
        # After record creation, set is_saved to True
        record.is_saved = True
        return record
   

    def action_enquiry_complaint(self):
        
        # Your logic to open the wizard
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'enquiry.complaint.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('customer.view_enquiry_complaint_wizard_form').id,
            'target': 'new',  # to open the wizard in a new window
            'context': {
                'default_enq_cm_id': self.id,
            },
        }


      # Compute method for readonly_comment
    # @api.depends('comment', 'is_saved')
    # def _compute_readonly_comment(self):
    #     """ This method will set the `readonly_comment` flag to True if the record is saved and the comment is set. """
    #     for record in self:
    #         # If record has a comment and is saved, set the flag to True
    #         record.readonly_comment = bool(record.comment and record.is_saved)

    # # Overriding the create method to set `is_saved` after the record is created
    # @api.model
    # def create(self, vals):
    #     """ Overridden create method to set `is_saved` field to True after the record is created """
    #     record = super(Enquiry, self).create(vals)
        
    #     # After record creation, set is_saved to True
    #     record.is_saved = True
    #     return record

    # # Action to open the wizard before creating the enquiry record
    # def action_enquiry_complaint(self):
    #     """ Logic to open the wizard before the enquiry record is created """
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'enquiry.complaint.wizard',
    #         'view_mode': 'form',
    #         'view_id': self.env.ref('customer.view_enquiry_complaint_wizard_form').id,
    #         'target': 'new',  # To open the wizard in a new window
    #         'context': {
    #             'default_enq_cm_id': self.id,  # Pass the current record's ID or False initially
    #         },
    #     }
    

    



    @api.onchange('enquiry_type_id')
    def _onchange_enquiry_type(self):
        if self.enquiry_type_id:
            # Log selected complaint type
            print(f"CT id: {self.enquiry_type_id.id}")
            
            # Search for related complaint subtypes
            enquiries = self.env['enquiry.subtype'].search([
                ('enquiry_type_id', '=', self.enquiry_type_id.id)
            ])
            
            # Log found complaint subtype IDs
            print(f"ENQUIRIES: {enquiries.ids}")
            
            # Set domain if any complaints are found
            return {
                'domain': {
                    
                    'enquiries_id': [('id', 'in', enquiries.ids)] if enquiries else []
                }
            }
        else:
            # Clear domain if no complaint_type_id is selected
            print("No enquiry_type_id selected")
            return {
                'domain': {
                    'enquiries_id': []
                }
            }
        
    @api.onchange('complaint_type_id')
    def _onchange_complaint_type(self):
        if self.complaint_type_id:
            # Log selected complaint type
            print(f"CT id: {self.complaint_type_id.id}")
            
            # Search for related complaint subtypes
            complaints = self.env['complaint.subtype'].search([
                ('complaint_type_id', '=', self.complaint_type_id.id)
            ])
            
            # Log found complaint subtype IDs
            print(f"COMPLAINTS: {complaints.ids}")
            
            # Set domain if any complaints are found
            return {
                'domain': {
                    
                    'complaints_id': [('id', 'in', complaints.ids)] if complaints else []
                }
            }
        else:
            # Clear domain if no complaint_type_id is selected
            print("No complaint_type_id selected")
            return {
                'domain': {
                    'complaints_id': []
                }
            }

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        if not self.customer_id:
            self.member_id = False

    @api.onchange('member_id')
    def _onchange_member_id(self):
        if not self.member_id:
            self.service_id = False

class EnquiryConfig(models.Model):
    _name = 'enquiry.config'
    _description = 'Enquiry Types'
 
    name = fields.Char(string='Enquiry Type', required=True)
    subtype_ids = fields.One2many('enquiry.subtype', 'enquiry_type_id', string='Enquiry Subtypes')

class EnquirySubtype(models.Model):
    _name = 'enquiry.subtype'
    _description = 'Enquiries'

    name = fields.Char(string='Enquiry Subtype', required=True)
    enquiry_type_id = fields.Many2one('enquiry.config', string='Enquiry Type', required=True)

class ComplaintConfig(models.Model):
    _name = 'complaint.config'
    _description = 'Complaint Type'

    name = fields.Char(string='Complaint Type', required=True)
    subtype_ids = fields.One2many('complaint.subtype', 'complaint_type_id', string='Complaint Subtypes')

class ComplaintSubtype(models.Model):
    _name = 'complaint.subtype'
    _description = 'Complaints'

    name = fields.Char(string='Complaint Subtype', required=True)
    complaint_type_id = fields.Many2one('complaint.config', string='Complaint Type', required=True)