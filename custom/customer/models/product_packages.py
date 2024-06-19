from odoo import models, fields, api

class ProductPackages(models.Model):
    _inherit = 'product.template'

    bundle_product = fields.Boolean(string='Bundle Product')
 
    category_limit_ids = fields.One2many('product.category.limit', 'category_id', string='Category Limits')
    
    service_ids = fields.One2many('product.package.service', 'product_template_id')
    is_packages = fields.Boolean('Is Packages')

    # @api.model
    # def create(self, vals):
    #     if self.env.context.get('product_packages_view_form'):
    #         vals['is_packages'] = True

class ProductPackagesService(models.Model):
    _name = 'product.package.service'
    _description = 'Your Service Model'

    product_template_id = fields.Many2one('product.template', string='Product Services', domain="[('type', '=', 'service'), ('detailed_type', '=', 'service')]")

    is_intercity = fields.Boolean('Intercity')
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float('quantity')

class  CategoryLimit(models.Model):
    _name = "product.category.limit"

    category_id = fields.Many2one('product.template', string='category')

    categ_id = fields.Many2one('product.category', string='Category')
    hours = fields.Float(string='Validation Hours')
    uom_id = fields.Many2one('uom.uom',string='Unit of Measure')
    quantity = fields.Float(string='Quantity')
