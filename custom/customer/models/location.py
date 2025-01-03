from odoo import models, fields
import requests
from odoo import http
from odoo.http import request, Response


class LocationInternal(models.Model):
    _name = 'location.internal'
    _description ='Internal Location'

    name = fields.Char(string='Location', required=True)

class LocationExternal(models.Model):
    _name = 'location.external'
    _description = 'External Location'

    name = fields.Char(string='Location', required=True)

class AaaLocation(models.Model):
    _name = 'aaa.location'

    name = fields.Char(string='Location')
    type = fields.Selection([
        ('internal', 'internal'),
        ('external', 'external'),
    ], string='type')

class LocationService(models.Model):
    _name = 'location.service'
    _description = 'Service Location'

    amount = fields.Integer('Amount')
    from_h3index = fields.Char('From H3index')
    from_latitude = fields.Float('From Latitude',digits=(10, 8))
    from_location = fields.Char('From Location')
    from_longitude = fields.Float('From Longitude',digits=(10, 8))
    to_h3index = fields.Char('To H3index')
    to_latitude = fields.Float('To Latitude',digits=(10, 8))
    to_location = fields.Char('To Location')
    to_longitude = fields.Float('To Longitude',digits=(10, 8))

class LocationFrom(models.Model):
    _name = 'location.latlong'
    _description = 'From Location'
    _rec_name = 'location'

    location = fields.Char('Location')
    latitude = fields.Char('Latitude')
    longitude = fields.Char('Longitude')
    # h3_index = fields.Char('H3 INDEX')

class Location(models.Model):
    _name = 'location'
    _description = 'Location'

    name = fields.Char(string="Location Name", required=True)
    latitude = fields.Char(string="Latitude")
    longitude = fields.Char(string="Longitude")


class LocationSuggestion(models.Model):
    _name = 'location.suggestion'
    _description = 'Location Suggestion'

    name = fields.Char(string='Location Name')
    feature_data = fields.Text(string='Feature Data')
    # latitude = fields.Float(string='Latitude', digits=(16, 14))
    # longitude = fields.Float(string='Longitude', digits=(16, 14))
    latitude = fields.Char('latitude')
    longitude = fields.Char('longitude')


    # --------------TEST------------------------------
    # models/location_search.py