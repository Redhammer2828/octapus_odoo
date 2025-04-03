from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    category_id = fields.Many2one('partner.category', string="Customer Category",
                                  domain="[('partner_id','=', partner_id)]")

    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")


    # @api.onchange('from_date', 'to_date', 'partner_id', 'category_id')
    def compute_services_based_on_date(self):

        for record in self:
            if not record.from_date or not record.to_date or not record.partner_id or not record.category_id:
                continue

            all_services = self.env["aaa.service"].search(
                [("customer_id", "=", record.partner_id.id),("sequence_id","=",record.category_id.id),("state","=","done")], 
            )
            invoice_lines = []
            product_quantity = {}

            # if record.invoice_line_ids:
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

            # record.invoice_line_ids = invoice_lines
            record.write({"invoice_line_ids":invoice_lines})
            

    
    


    
