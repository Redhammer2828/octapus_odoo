from odoo import models, fields

class PolicyServiceHistory(models.Model):
    _name = 'policy.service.history'
    _description = 'Policy Service History'

    member_id = fields.Many2one('res.partner', string='Member', readonly=True)
    member_activate_date = fields.Date(string='Activate Date', readonly=True)
    member_expiry_date = fields.Date(string='Expiry Date', readonly=True)
    line_ids = fields.One2many('policy.service.history.lines', 'history_id', string='Services', readonly=True)
    category_line_ids = fields.One2many('category.lines', 'history_id', string='Categories', readonly=True)


class ServiceHistoryLines(models.Model):
    _name = 'policy.service.history.lines'
    _description = 'Service History Lines'

    history_id = fields.Many2one('policy.service.history', string='History')
    product_id = fields.Many2one('product.template', string='Service')

class CategoryLines(models.Model):
    _name = 'category.lines'
    _description = 'Category Lines'

    history_id = fields.Many2one('policy.service.history', string='History')
    category_id = fields.Many2one('product.category', string='category')
    count = fields.Integer('No. of Services')