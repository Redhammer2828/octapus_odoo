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
    _name = 'location.from'
    _description = 'From Location'
    _rec_name = 'from_location'

    from_location = fields.Char('from')
    from_latitude = fields.Float('From Latitude',digits=(16, 8))
    from_longitude = fields.Float('From Longitude',digits=(16, 8))

class LocationTo(models.Model):
    _name = 'location.to'
    _description = 'To Location'
    _rec_name = 'to_location'

    to_location = fields.Char('To Location')    
    to_latitude = fields.Float('To Latitude',digits=(16, 8))
    to_longitude = fields.Float('To Longitude',digits=(16, 8))
