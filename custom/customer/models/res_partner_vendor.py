from odoo import models, fields, api

class ResPartnerVendor(models.Model):
    _inherit = 'res.partner'

    vendor_function = fields.Char(string='Job Position')


    vendor_rating = fields.Selection([
        ('0', "0"),
        ('1', "1"),
        ('2', "2"),
        ('3', "3"),
        ('4', "4"),
        ('5', "5")
    ], string='Rating')

    property_product_pricelist_id_vendor = fields.Many2one(
        'product.pricelist',
        string='Vendor Pricelist',
        domain="[('is_vendor', '=', True)]",
    )

    def action_active(self):
        pass

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    is_vendor = fields.Boolean(string='Is Vendor', default=False)
    is_customer = fields.Boolean(string='Is customer', default=False)



    @api.onchange('is_vendor')
    def _onchange_customer_type(self):
        """Set is_vendor to True when customer_type is checked."""
        if self.is_vendor:
            self.is_vendor = True
        else:
            self.is_vendor = False

    @api.onchange('is_customer')
    def _onchange_customer_type(self):
        """Set is_vendor to True when customer_type is checked."""
        if self.is_customer:
            self.is_customer = True
        else:
            self.is_customer = False
