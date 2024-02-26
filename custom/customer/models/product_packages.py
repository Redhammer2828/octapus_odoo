from odoo import models, fields, api

class ProductPackages(models.Model):
    _inherit = 'product.template'

    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
