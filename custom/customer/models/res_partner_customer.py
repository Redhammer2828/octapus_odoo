#model/res_partner_customer.py
from odoo import fields, models ,api

class ResPartnerCustomer(models.Model):
    _inherit = 'res.partner'
    _description = 'Customer Information'

    customer_code = fields.Char(string='Code')
    function = fields.Char(string='Function')

    member_count = fields.Integer(compute='_compute_member_count', string='Member Count')

    customer = fields.Binary('customer')  #Field (Flag) for Members (is_customer)
    
    #Page - Category
    customer_category_ids = fields.One2many('partner.category', 'partner_id', string='Customer Categories')
    
    invoicing_policy = fields.Selection([ ('individual', 'Individual'),
                                    ('consolidated', 'Consolidated') ], string='Invoicing Policy') 
          # Set the default value here
    #Action for Member Button
    def action_view_member(self):
        return {
            'name': 'Members',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('parent_customer_id', '=', self.id), ('is_customer','=',True)],
            'context': {
                'from_res_partner_member_form': True,
                'default_parent_customer_id': self.id,  # Pre-select the parent customer
            },
            'views': [(self.env.ref('customer.res_partner_member_tree').id, 'tree'),
                    (self.env.ref('customer.res_partner_member_form').id, 'form')],
            # Add any other action parameters as needed
        }
        
    #For Calculating Count of Memnbers 
    @api.depends('parent_customer_id')
    def _compute_member_count(self):
        for record in self:
            if record.id:
                member_count = self.env['res.partner'].search_count([('parent_customer_id', '=', record.id)])
                record.member_count = member_count
            else:
                record.member_count = 0
    
    def waive_off_history(self):
        pass

    def duplicate_record(self):
        self.ensure_one()
        duplicate_record = self.copy()
        view_id = self.env.ref('customer.res_partner_customer_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Duplicate Record',
            'res_model': self._name,
            'res_id': duplicate_record.id,
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
        }

class PartnerCategory(models.Model):
    _name = 'partner.category'
    _description = 'Partner Category'
    _rec_name = 'description'

    partner_id = fields.Many2one('res.partner', string='Partner', inverse_name='customer_category_ids')

    name = fields.Char(string="Code")
    member_type = fields.Selection([
        ('policy', 'Policy'),
        ('credit', 'Credit'),
        ('adhoc', 'Adhoc')],
        string='Type')
    description = fields.Text(string="Description")
    default_member = fields.Many2one('res.partner',String="Default Member")
