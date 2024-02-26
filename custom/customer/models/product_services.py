from odoo import models, fields

class ServicesManagement(models.Model):
    _name = 'services.management'
    _description = 'Services Management'

    id = fields.Char(string='ID', required=True, readonly=True)
    name = fields.Char(string='Service Name', required=True)
    service_type = fields.Char(string='service type')
