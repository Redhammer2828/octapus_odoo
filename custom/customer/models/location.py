from odoo import models, fields

class LocationInternal(models.Model):
    _name = 'location.internal'
    _description ='Internal Location'

    name = fields.Char(string='Location', required=True)

class LocationExternal(models.Model):
    _name = 'location.external'
    _description = 'External Location'

    name = fields.Char(string='Location', required=True)

class LocationService(models.Model):
    _name = 'location.service'
    _description = 'Service Location'

    amount = fields.Integer('amount')
    from_h3index = fields.Integer('from_h3index')
    from_latitude = fields.Float('from_latitude')
    from_location = fields.Char('from_location')
    from_longitude = fields.Float('from_longitude')
    to_h3index = fields.Integer('to_h3index')
    to_latitude = fields.Float('to_latitude')
    to_location = fields.Char('to_location')
    to_longitude = fields.Float('to_longitude')

class LocationFrom(models.Model):
    _name = 'location.latlong'
    _description = 'From Location'
    _rec_name = 'location'

    location = fields.Char('Location')
    latitude = fields.Float('Latitude',digits=(16, 8))
    longitude = fields.Float('Longitude',digits=(16, 8))
