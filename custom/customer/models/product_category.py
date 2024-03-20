from odoo import models, fields, api

class ProductCategoryInherit(models.Model):
    _inherit = 'product.category'

    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')

    property_cost_method = fields.Selection([
        ('standard', 'Standard Price'),
        ('fifo', 'First In First Out (FIFO)'),
        ('average', 'Average Cost (AVCO)')
    ], string='Costing Method', default='standard' ,required=True)

    property_valuation = fields.Selection([
        ('manual_periodic', 'Manual'),
        ('real_time', 'Automated')
    ], string='Inventory Valuation' , default='manual_periodic' , required=True)
