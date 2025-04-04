from odoo import models, fields, api

class ProductCategoryInherit(models.Model):
    _inherit = 'product.category'

    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')

    property_cost_method = fields.Selection([
        ('standard', 'Standard Price'),
        ('fifo', 'First In First Out (FIFO)'),
        ('average', 'Average Cost (AVCO)')
    ], string='Costing Method', default='standard')

    property_valuation = fields.Selection([
        ('manual_periodic', 'Manual'),
        ('real_time', 'Automated')
    ], string='Inventory Valuation' , default='manual_periodic')

    category_service_count = fields.Integer(string="Category Services Count", compute='_compute_category_service_count')

    @api.depends('name')
    def _compute_category_service_count(self):
        for cash in self:
            cash_service_ids = self.env['product.template'].search([
                ('categ_id', '=', self.id),
                
            ])
            print("CASH SERVICES", cash_service_ids.ids)
            cash.category_service_count= len(cash_service_ids)

    def action_view_category_service(self):

         return {
            'name': 'Products',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'tree,form',
            'domain': [('categ_id', '=', self.id)],
            'context': {},
            'views': [(self.env.ref('customer.product_service_view_tree').id, 'tree'),
                    (self.env.ref('customer.product_service_view_form').id, 'form')],
        }
