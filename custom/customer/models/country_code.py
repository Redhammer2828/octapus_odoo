from odoo import models, fields

class CountryCode(models.Model):
    _name = 'country.code'
    _description = 'Country Code'

    c_code = fields.Char(string='Country Code', required=True)
    country = fields.Char(string= 'Country', required=True)
    Test = fields.Char(string='Test')
    
