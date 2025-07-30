from odoo import models, fields, api


class CreditServiceValidation(models.Model):
    _name = 'credit.service.validation'
    _description = 'Credit Service Validation'

    partner_id = fields.Many2one('res.partner', string="Customer")
    member_type = fields.Selection([ ('credit', 'Credit Member') ], string='Member Type', default="credit")
    category_id = fields.Many2one('partner.category', 
                                  string="Customer Category",
                                  domain="[('partner_id','=', partner_id),('member_type','=',member_type)]")
    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    state = fields.Selection([  ('draft', 'Draft'),
                                ('confirm', 'Confirmed')  ], string='Status', default="draft")
    service_line_ids = fields.One2many("service.statement.line", "credit_service_id", string="Services")
    taxable_amount = fields.Float(string="Taxable Amount")
    vat = fields.Float(string="VAT 5%")
    total_amount = fields.Float(string="Total Amount")
    is_rent_a_car = fields.Boolean(string="Is Rent a Car Service", default=False)

    @api.onchange('partner_id', 'category_id', 'from_date', 'to_date')
    def _onchange_any_field(self):
        for record in self:
            record.service_line_ids = [(5, 0, 0)]

    def get_services(self):

        for record in self:
            if not record.from_date or not record.to_date or not record.partner_id or not record.category_id:
                continue

            all_services = self.env["aaa.service"].search(
                    [("customer_id", "=", record.partner_id.id),("sequence_id","=",record.category_id.id),("state","=","done"),("invoice_state","=","not_invoiced")] 
                )
            
            credit_services = {}
            record.service_line_ids = [(5, 0, 0)]

            taxable_amount = 0
            vat = 0
            total_amount = 0

            for service in all_services:
                service_date = service.service_time.date()
                if record.from_date <= service_date <= record.to_date:

                    price_list_item = self.env["product.pricelist.item"].search([('product_tmpl_id','=',service.product_id.id), ('pricelist_id','=',record.partner_id.property_product_pricelist_id.id),
                    ('date_start', '<=', service_date),
                    ('date_end', '>=', service_date)])
                
                    service_rate = self.env["service.rate"].search([('product_pricelist_item_id','=',price_list_item.id),
                                                            ('from_loc_id','=',service.from_location.id),
                                                            ('to_loc_id','=',service.to_location.id),], limit=1)
                    
                    credit_services[service.id] = {
                            "service_date": service_date,
                            "service_number_id": service.id,
                            "trip_sheet_number": service.credit_proforma_number,
                            "vehicle_model": service.vehicle_model,
                            "vehicle_plate": service.vehicle_plate,
                            "service_product_id": service.product_id.id,
                            "from_location_id": service.from_location.id,
                            "to_location_id": service.to_location.id,
                            "date_time_from": service.date_time_from if service.product_id.name == "RENT A CAR" or service.product_id.name == "RENT A CAR - UPGRADE" else False,
                            "date_time_to": service.date_time_to if service.product_id.name == "RENT A CAR" or service.product_id.name == "RENT A CAR - UPGRADE" else False,
                            "quantity": service.quantity if service.product_id.name == "RENT A CAR" or service.product_id.name == "RENT A CAR - UPGRADE" else False,
                            "price": service_rate.price,
                            }
                    
                    if service.product_id.name == "RENT A CAR" or service.product_id.name == "RENT A CAR - UPGRADE":
                        record.is_rent_a_car = True
                    else:
                        record.is_rent_a_car = False

                    taxable_amount += service_rate.price
            vat = taxable_amount * 0.05
            total_amount = taxable_amount + vat    

            service_lines = [(0, 0, values)
                                for values in credit_services.values()] 
            
            record.write({"service_line_ids": service_lines,
                          "taxable_amount": taxable_amount,
                          "vat": vat,
                          "total_amount": total_amount})
            
    
    def update_total(self):
        for record in self:
            taxable_amount = sum(line.price for line in record.service_line_ids if line.add_to_report)
            vat = taxable_amount * 0.05
            total_amount = taxable_amount + vat 
            record.write({"taxable_amount": taxable_amount,
                          "vat": vat,
                          "total_amount": total_amount})
            
    def action_add_location_to_pricelist(self):
        for record in self:
            for line in record.service_line_ids:

                if line.is_new_location_combination:
                    price_list_item = self.env["product.pricelist.item"].search([('product_tmpl_id','=',line.service_product_id.id), ('pricelist_id','=',record.partner_id.property_product_pricelist_id.id),
                    ('date_start', '<=', line.service_date),
                    ('date_end', '>=', line.service_date)])

                    location_combination = self.env["service.rate"].search([('product_pricelist_item_id','=',price_list_item.id),
                                                            ('from_loc_id','=',line.from_location_id.id),
                                                            ('to_loc_id','=',line.to_location_id.id),])
                    
                    if not location_combination:
                        self.env["service.rate"].create({
                            'product_pricelist_item_id': price_list_item.id,
                            'from_loc_id': line.from_location_id.id,
                            'to_loc_id': line.to_location_id.id,
                            'price': line.price,
                            })
                        
                line.is_new_location_combination = False
                    




    def action_confirm(self):
        for record in self:
            record.state = "confirm"

    
    def action_draft(self):
        for record in self:
            record.state = "draft"


class ServiceStatementLine(models.Model):
    _name = 'service.statement.line'
    _description = 'Service Statement Line'


    credit_service_id = fields.Many2one('credit.service.validation', string="Credit ID")
    service_date = fields.Date(string="Service Date")
    # service_number = fields.Char(string="Service Number")
    service_number_id = fields.Many2one('aaa.service', string="Service Number")
    trip_sheet_number = fields.Char(string="Trip Sheet No.")
    vehicle_model = fields.Char(string="Vehicle Model")
    vehicle_plate = fields.Char(string="Vehicle Plate")
    # service_product = fields.Char(string="Product")
    # from_location = fields.Char(string="From Location")
    # to_location = fields.Char(string="To Location")
    service_product_id = fields.Many2one('product.template', string="Service")
    from_location_id = fields.Many2one('aaa.location', string="From Location")
    to_location_id = fields.Many2one('aaa.location', string="To Location")
    date_time_from = fields.Datetime(string="From Date")
    date_time_to = fields.Datetime(string="To Date")
    quantity = fields.Float(string="Quantity")
    price = fields.Float(string="Price")
    add_to_report = fields.Boolean(string="Add to Report", default=True)
    is_new_location_combination = fields.Boolean(string="Update Locations", default=False)
