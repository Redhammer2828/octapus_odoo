from odoo import models, fields

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    country_group_ids = fields.Many2many('res.country.group', string='Country Groups')
    pricelist_item_ids = fields.One2many('product.pricelist.item', 'pricelist_id', string='Pricelist Items')
    customer_type = fields.Selection([
        ('policy', 'Policy'),
        ('credit', 'Credit'),
        ('adhoc', 'Ad Hoc'),
    ], string='Customer Type')


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')
    service_rt_ids = fields.One2many('service.rate', 'product_pricelist_item_id', string='Service Rates')  # Ensure correct field name


class ServiceRate(models.Model):
    _name = 'service.rate'

    product_pricelist_item_id = fields.Many2one('product.pricelist.item', string='Pricelist Item')  # Many2one to create the link to ProductPricelistItem
    from_loc_id = fields.Many2one('aaa.location', string='From Location')
    to_loc_id = fields.Many2one('aaa.location', string='To Location')
    price = fields.Float('Price')
