from odoo import models, fields, api
from odoo.exceptions import ValidationError , UserError
import datetime
from datetime import timedelta,datetime
import logging

# Set up logging for debugging purposes
_logger = logging.getLogger(__name__)

class Enquiry(models.Model):
    _name = 'aaa.enquiry'
    _description = 'Enquiry'

    enquiry = fields.Char('enquiry')
    name = fields.Char(string='Enq_NO.', readonly=True, default=lambda self: self._generate_enquiry_number())
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
    service_no = fields.Char(string="Service Number")
    
    enq_id = fields.Many2one('aaa.service',string='Service Number',ondelete='cascade') #IN aaa.enquiry
    enquiry_type_id = fields.Many2one('enquiry.config', string='Enquiry Type')
    enquiries_id = fields.Many2one('enquiry.subtype', string='Enquiry Subtype', domain="[('enquiry_type_id','=',enquiry_type_id)]")
    complaint_type_id = fields.Many2one('complaint.config', string='Complaint Type')
    complaints_id = fields.Many2one('complaint.subtype', string='Complaint Subtype', domain="[('complaint_type_id','=',complaint_type_id)]" )
    
    # This field will control whether it's an enquiry or a complaint
    is_enquiry = fields.Boolean("Is Enquiry?", default=True)
    # New fields for managing visibility
    show_enquiry_fields = fields.Boolean("Show Enquiry Fields", default=False)
    show_complaint_fields = fields.Boolean("Show Complaint Fields", default=False)

    is_saved = fields.Boolean(string="Is Saved", default=False)
    #readonly_comment = fields.Boolean(string="Readonly Comment", compute="_compute_readonly_comment", store=False)
    state = fields.Selection(
        [('draft', 'Draft'), ('saved', 'Saved')],
        string='State',
        default='draft'
    )

   

    @api.model
    def _generate_enquiry_number(self):
        """Generate a sequence number in the format ENQ/{current_month}/{current_year}/{sequence_number}."""
        current_date = datetime.now()
        current_month = current_date.strftime('%m')
        current_year = current_date.strftime('%Y')

        # Add placeholders for dynamic prefix values in ir.sequence
        self.env['ir.sequence'].sudo().write({
            'prefix': f"ENQ/{current_month}/{current_year}/"
        })

        sequence_number = self.env['ir.sequence'].next_by_code('aaa.enquiry.sequence') or '0001'
        return sequence_number

    @api.model
    def create(self, vals):
        """Override the create method to ensure 'name' is auto-generated."""
        if not vals.get('name'):
            vals['name'] = self._generate_enquiry_number()
        return super(Enquiry, self).create(vals)
    





    def write(self, vals):
        """Ensure that the state is updated to 'saved' after the form is saved."""
        if 'state' not in vals and self.state == 'draft':
            vals['state'] = 'saved'
        return super(Enquiry, self).write(vals)
  


   

    
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




