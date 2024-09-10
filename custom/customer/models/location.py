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

    amount = fields.Integer('Amount')
    from_h3index = fields.Char('From H3index')
    from_latitude = fields.Float('From Latitude')
    from_location = fields.Char('From Location')
    from_longitude = fields.Float('From Longitude')
    to_h3index = fields.Char('To H3index')
    to_latitude = fields.Float('To Latitude')
    to_location = fields.Char('To Location')
    to_longitude = fields.Float('To Longitude')

class LocationFrom(models.Model):
    _name = 'location.latlong'
    _description = 'From Location'
    _rec_name = 'location'

    location = fields.Char('Location')
    latitude = fields.Char('Latitude')
    longitude = fields.Char('Longitude')
    h3_index = fields.Char('H3 INDEX')
