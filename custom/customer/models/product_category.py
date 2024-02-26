from odoo import models, fields, api

class ProductCategoryInherit(models.Model):
    _inherit = 'product.category'

    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
