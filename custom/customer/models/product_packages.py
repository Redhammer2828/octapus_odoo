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

    # product_template_id = fields.Many2one('product.template', string='Product Services', domain="[('type', '=', 'service'), ('detailed_type', '=', 'service')]")
    product_template_id = fields.Many2one('product.template', string='Product Services')

    is_intercity = fields.Selection([
        ('false', 'Same Emirate'),
        ('true', 'Intercity'),
        ('no_validation', 'No Validation'),
        ('same_city', 'Same City')
    ], string='Service Type', default='no_validation', help='Specify if this service allows intercity travel')
    intercity_limit = fields.Float('Intercity Limit', help='Maximum limit for intercity services')
    intercity_limit_period = fields.Selection([
        ('daily', 'Daily'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('no_check', 'No intercity check'),
        ('allow_around_40km', 'Allow Around 40km')
    ], string='Limit Period', default='no_check', help='Period for intercity limit calculation')
    allowed_intercity_emirates = fields.Many2many(
        'res.country.state', 
        string='Allowed Intercity Emirates',
        domain="[('country_id.code', '=', 'AE')]",
        help='Emirates that are allowed for intercity services even when is_intercity=False'
    )
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float('quantity')

    @api.onchange('is_intercity')
    def _onchange_is_intercity(self):
        """Auto-select appropriate settings based on service type"""
        if self.is_intercity == 'same_city':
            # Auto-select allow_around_40km when same_city is chosen
            self.intercity_limit_period = 'allow_around_40km'
        elif self.is_intercity == 'no_validation':
            # Auto-select no intercity check and set intercity limit to 0
            self.intercity_limit_period = 'no_check'
            self.intercity_limit = 0

class  CategoryLimit(models.Model):
    _name = "product.category.limit"

    category_id = fields.Many2one('product.template', string='category')

    categ_id = fields.Many2one('product.category', string='Category')
    hours = fields.Float(string='Validation Hours')
    uom_id = fields.Many2one('uom.uom',string='Unit of Measure')
    quantity = fields.Float(string='Quantity')
