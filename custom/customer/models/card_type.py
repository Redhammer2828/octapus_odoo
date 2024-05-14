from odoo import models, fields

class CardType(models.Model):
    _name = 'card.type'
    _description = 'Card type '

    code = fields.Char(string='Code', required=True)
    name = fields.Char(string='Name', required=True)
 
