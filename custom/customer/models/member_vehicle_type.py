from odoo import fields,models

class MemberVehicleType(models.Model):
    _name = 'member.vehicle.type'
    _description='Member Vehicle Type'

    name = fields.Char(' Vehicle Name')
    
    vehicle_model_ids = fields.One2many('member.vehicle.model', 'type_id', string='vehicle_model')

