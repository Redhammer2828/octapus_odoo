from odoo import models, fields, api
from itertools import chain

class AccountMove(models.Model):
    _inherit = 'account.move'

    member_type = fields.Selection([ ('policy', 'Policy Member'),
                                    ('credit', 'Credit Member') ], string='Member Type', default="policy")
    category_id = fields.Many2one('partner.category', 
                                  string="Customer Category",
                                  domain="[('partner_id','=', partner_id),('member_type','=',member_type)]")

    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    invoice_line_type = fields.Selection([ ('separate', 'Separate Invoice'),
                                          ('consolidated', 'Consolidated Invoice') ], string='Invoice Type', default="consolidated")
    product_ids = fields.Many2many('product.template','product_service_rel', 'product_id', 'service_id', string="Product Ids")
    product_id = fields.Many2one('product.template', string="Product", domain="[('id','in', product_ids)]")
    product_quantity = fields.Integer()


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


    
    def _compute_service_id_domain(self):

        for record in self:

            record.invoice_line_ids = [(5, 0, 0)]
            record.product_id = False

            if not record.from_date or not record.to_date or not record.partner_id or not record.category_id or record.invoice_line_type != "separate":
                continue

            if record.member_type == "credit": 

                all_services = self.env["aaa.service"].search(
                    [("customer_id", "=", record.partner_id.id),
                    ("sequence_id","=",record.category_id.id),
                    ("state","=","done")] 
                )

                products = []
                if record.product_ids:
                    record.product_ids = [(5, 0, 0)]

                for service in all_services:
                    if record.from_date <= service.service_time.date() <= record.to_date:
                        products.append(service.product_id.id)
                distinct_products = list(set(products))
                record.product_ids = [(6,0,distinct_products)]


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

                products = []
                if record.product_ids:
                    record.product_ids = [(5, 0, 0)]

                for rec in all_records:
                    products.append(rec.product_template_id.id)
                    distinct_products = list(set(products))
                    record.product_ids = [(6,0,distinct_products)]
            

    @api.onchange('from_date', 'to_date', 'partner_id', 'category_id', 'member_type', 'invoice_line_type')
    def _onchange_compute_service_id_domain(self):
        self._compute_service_id_domain()


    def compute_separate_invoice_line(self):

        for record in self:
            if not record.product_id:
                continue
            record.invoice_line_ids = [(5, 0, 0)]

            quantity = 0
            record.product_quantity = 0

            if record.member_type == "credit":

                all_services = self.env["aaa.service"].search(
                    [("customer_id", "=", record.partner_id.id),
                    ("sequence_id","=",record.category_id.id),
                    ("state","=","done"),
                    ("product_id","=",record.product_id.id)]
                )

                for service in all_services:
                    if record.from_date <= service.service_time.date() <= record.to_date:
                        quantity += 1
            
                record.product_quantity = quantity

            elif record.member_type == "policy":

                domain = [('invoice_ref_date', '>=', record.from_date), 
                        ('invoice_ref_date', '<=', record.to_date),
                        ("parent_customer_id", "=", record.partner_id.id),
                        ('member_partner_category_id', '=', record.category_id.id),
                        ('member_type', '=', record.member_type),
                        ('product_template_id','=',record.product_id.id)]
                
                partner_domain = domain + [('membership_state', '=', 'confirm')]

                partner_records = self.env['res.partner'].search(partner_domain)
                history_records = self.env['membership.history'].search(domain)

                all_records = chain(partner_records, history_records)

                for rec in all_records:
                    quantity += 1
                
                record.product_quantity = quantity
            
            record.write({"invoice_line_ids":[(0,0,{
                            "product_id": record.product_id.id,
                            "price_unit": record.product_id.price_unit,
                            "quantity": record.product_quantity,
                            "name": record.product_id.name,
                        })]})
                
            

            

    
    


    
