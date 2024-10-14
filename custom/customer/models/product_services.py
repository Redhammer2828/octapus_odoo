from odoo import models, fields

class ProductServices(models.Model):
    _inherit = 'product.template'
    _description = 'Services'

    service_based = fields.Selection([
        ('distance', 'Distance Based'),
        ('location', 'Location Based'),
        ('duration', 'Duration Based'),
        ('location_duration', 'Location and Duration Based'),
        ('none', 'None')
    ], string='Service Based')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', default=lambda self: self.env.ref('uom.product_uom_unit', raise_if_not_found=False))
    uom_po_id = fields.Many2one('uom.uom', string='Purchase Unit of Measure', default=lambda self: self.env.ref('uom.product_uom_unit', raise_if_not_found=False))
    # is_services = fields.Boolean('Is Services')
    provider_from_location_id = fields.Many2one('location.internal', string="From Location")
    provider_to_location_id = fields.Many2one('location.internal', string="To Location")
    datetime_from = fields.Datetime(string="Datetime From")
    datetime_to = fields.Datetime(string="Datetime To")
    quantity = fields.Float(string="Quantity")
    price_unit = fields.Char('Price Unit')
    price_subtotal = fields.Char('price_subtotal')

    service_credit_addon_id = fields.Many2one('aaa.service', string="Service")
