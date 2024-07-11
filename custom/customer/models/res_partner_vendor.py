from odoo import models,fields
 
class ResPartnerVendor(models.Model):
    _inherit='res.partner'
  
    vendor_function= fields.Char(string='Job Position')

    vendor_rating= fields.Selection([
        ('0',"0"),
        ('1',"1"),
        ('2',"2"),
        ('3',"3"),
        ('4',"4"),
        ('5', "5")
    ], string='Rating')
 
    def action_active(self):
      pass
 