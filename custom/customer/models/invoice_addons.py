from odoo import models, fields, api
from itertools import chain

class AccountMove(models.Model):
    _inherit = 'account.move'

    member_type = fields.Selection([ ('policy', 'Policy Member'),
                                    ('credit', 'Credit Member') ], string='Member Type')
    category_id = fields.Many2one('partner.category', 
                                  string="Customer Category",
                                  domain="[('partner_id','=', partner_id),('member_type','=',member_type)]")

    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")


    @api.onchange('member_type', 'partner_id')
    def _onchange_member_type(self):
        if self.member_type and self.partner_id:
            domain = [
                ('partner_id', '=', self.partner_id.id),
                ('member_type', '=', self.member_type)
            ]
            first_category = self.env['partner.category'].search(domain, limit=1)
            self.category_id = first_category.id if first_category else False


    def compute_services_based_on_date(self):

        for record in self:
            if not record.from_date or not record.to_date or not record.partner_id or not record.category_id:
                continue

            if record.member_type == "credit":

                all_services = self.env["aaa.service"].search(
                    [("customer_id", "=", record.partner_id.id),("sequence_id","=",record.category_id.id),("state","=","done")] 
                )
                invoice_lines = []
                product_quantity = {}

                record.invoice_line_ids = [(5, 0, 0)]

                for service in all_services:
                    if record.from_date <= service.service_time.date() <= record.to_date:
                        product_id = service.product_id.id

                        if product_id in product_quantity:
                            product_quantity[product_id]["quantity"] += 1

                        else:
                            product_quantity[product_id] = {
                                "product_id": product_id,
                                "price_unit": service.product_id.price_unit,
                                "quantity": 1,
                                "name": service.product_id.name,
                            }

                invoice_lines = [(0, 0, values)
                                    for values in product_quantity.values()]
                print(invoice_lines)

                record.write({"invoice_line_ids":invoice_lines})


            elif record.member_type == "policy":

                domain = [('invoice_ref_date', '>=', record.from_date), 
                          ('invoice_ref_date', '<=', record.to_date),
                          ("parent_customer_id", "=", record.partner_id.id),
                          ('member_partner_category_id', '=', record.category_id.id),
                          ('member_type', '=', record.member_type),]
                
                partner_domain = domain + [('membership_state', '=', 'confirm')]

                partner_records = self.env['res.partner'].search(partner_domain)
                history_records = self.env['membership.history'].search(domain)

                all_records = chain(partner_records, history_records)

                invoice_lines = []
                product_quantity = {}

                record.invoice_line_ids = [(5, 0, 0)]

                for rec in all_records:
                    product_id = rec.product_template_id.id

                    if product_id in product_quantity:
                            product_quantity[product_id]["quantity"] += 1

                    else:
                        product_quantity[product_id] = {
                            "product_id": product_id,
                            "price_unit": rec.product_template_id.price_unit,
                            "quantity": 1,
                            "name": rec.product_template_id.name,
                        }

                invoice_lines = [(0, 0, values)
                                    for values in product_quantity.values()]
                print(invoice_lines)

                record.write({"invoice_line_ids":invoice_lines})



            

    
    


    
