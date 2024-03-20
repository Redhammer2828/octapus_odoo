from odoo import models, fields

class ProductServices(models.Model):
    _inherit = 'product.template'
    _description = 'Services'

    service_type = fields.Selection([
        ('distance', 'Distance Based'),
        ('location', 'Location Based'),
        ('duration', 'Duration Based'),
        ('location_duration', 'Location and Duration Based'),
        ('none', 'None')
    ], string='Service Type')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', default=lambda self: self.env.ref('uom.product_uom_unit', raise_if_not_found=False))
    uom_po_id = fields.Many2one('uom.uom', string='Purchase Unit of Measure', default=lambda self: self.env.ref('uom.product_uom_unit', raise_if_not_found=False))

    # is_services = fields.Boolean('Is Services')