from odoo import fields,models

class ExternalService(models.Model):
    _name = "external.service"
    _description="External Service"

    name = fields.Char(string='name')
    category = fields.Char(string='Category')
    default_member = fields.Char(string='Default Member')

    customer_id = fields.Many2one('res.partner', string='customer')

    #page
    vehicle_model_ids = fields.One2many('member.vehicle.model', 'type_id', string='vehicle_model')