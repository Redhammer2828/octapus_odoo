from odoo import models, fields

class CardType(models.Model):
    _name = 'card.type'
    _description = 'Card type '

    name = fields.Char(string='name', required=True)
    code = fields.Char(string='code', required=True)
 
