from odoo import fields,models

class MemberVehicleType(models.Model):
    _name = 'member.vehicle.model'
    _description='Member Vehicle Models'

    name = fields.Char(' Vehicle Model Name')
    type_id = fields.Many2one('member.vehicle.type', string='Vehicle type')