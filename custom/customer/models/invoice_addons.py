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
    invoice_line_type = fields.Selection([ ('consolidated', 'Consolidated Invoice'),
                                          ('separate', 'Separate Invoice')], string='Invoice Type', default="consolidated")
    product_ids = fields.Many2many('product.template','product_service_rel', 'product_id', 'service_id', string="Product Ids")
    product_id = fields.Many2one('product.template', string="Package", domain="[('id','in', product_ids)]")
    service_ids = fields.Many2many('aaa.service', 'service_service_rel', 'invoice_id', 'service_id')
    service_id = fields.Many2one('aaa.service', string="Service", domain="[('id','in', service_ids)]")


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
                total = 0
                service_count = 0

                record.invoice_line_ids = [(5, 0, 0)]

                for service in all_services:
                    if record.from_date <= service.service_time.date() <= record.to_date:

                        price_list_item = self.env["product.pricelist.item"].search([('product_tmpl_id','=',service.product_id.id), ('pricelist_id','=',record.partner_id.property_product_pricelist_id.id)])
                
                        service_rate = self.env["service.rate"].search([('product_pricelist_item_id','=',price_list_item.id),
                                                                ('from_loc_id','=',service.from_location.id),
                                                                ('to_loc_id','=',service.to_location.id),])
                        
                        total += service_rate.price
                        service_count += 1
                tax = self.env['account.tax'].search([('amount', '=', 5), ('type_tax_use', '=', 'sale')])

                invoice_lines = [(0, 0, {
                            "name": f"Services Provided for Customer: {record.partner_id.name} from {record.from_date} to {record.to_date} ({service_count} services)",
                            "price_unit": total,
                            "quantity": 1,
                            "tax_ids": [(6, 0, [tax.id])]
                            })]


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
                            "price_unit": 0,
                            "quantity": 1,
                            "name": f"{rec.product_template_id.name} MEMBERSHIP FOR THE PERIOD FROM {record.from_date} TO {record.to_date}",
                        }

                for key in product_quantity.keys():
                    pricelist_item = self.env["product.pricelist.item"].search([('product_tmpl_id','=',key), ('pricelist_id','=',record.partner_id.property_product_pricelist_id.id)])
                    
                    product_quantity[key]["price_unit"] = pricelist_item.fixed_price
                    

                invoice_lines = [(0, 0, values)
                                    for values in product_quantity.values()]

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

                services = []
                if record.service_ids:
                    record.service_ids = [(5, 0, 0)]

                for service in all_services:
                    if record.from_date <= service.service_time.date() <= record.to_date:
                        services.append(service.id)
                distinct_services = list(set(services))
                record.service_ids = [(6,0,distinct_services)]


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
            
            record.invoice_line_ids = [(5, 0, 0)]

            quantity = 0

            if record.member_type == "credit":

                if not record.service_id:
                    continue
                
                price_list_item = self.env["product.pricelist.item"].search([('product_tmpl_id','=',record.service_id.product_id.id), ('pricelist_id','=',record.partner_id.property_product_pricelist_id.id)])
                
                service_rate = self.env["service.rate"].search([('product_pricelist_item_id','=',price_list_item.id),
                                                                ('from_loc_id','=',record.service_id.from_location.id),
                                                                ('to_loc_id','=',record.service_id.to_location.id),])
                
                invoice_line_items = {
                            "product_id": record.service_id.product_id.id,
                            "price_unit": service_rate.price,
                            "quantity": 1,
                            "name": f"{record.service_id.product_id.name} {record.service_id.vehicle_type or ''} {record.service_id.vehicle_model or ''} {record.service_id.vehicle_chasis_no} FROM: {record.service_id.from_location.name} TO: {record.service_id.to_location.name}",
                            }



            elif record.member_type == "policy":

                if not record.product_id:
                    continue

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
                
                pricelist_item = self.env["product.pricelist.item"].search([('product_tmpl_id','=',record.product_id.id), ('pricelist_id','=',record.partner_id.property_product_pricelist_id.id)])

                invoice_line_items = {
                            "product_id": record.product_id.id,
                            "price_unit": pricelist_item.fixed_price,
                            "quantity": quantity,
                            "name": f"{record.product_id.name} MEMBERSHIP FOR THE PERIOD FROM {record.from_date} TO {record.to_date}",
                            }

            
            record.write({"invoice_line_ids":[(0,0,invoice_line_items)]})
                
            
            

    
    


    
