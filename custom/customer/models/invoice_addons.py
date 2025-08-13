from odoo import models, fields, api
import pytz
from itertools import chain
import io
import base64
import textwrap
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import inch
from datetime import datetime
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from datetime import datetime
import base64, io

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
    credit_service_line_ids = fields.One2many("credit.service.line", "credit_invoice_id", string="Services")
    policy_membership_line_ids = fields.One2many("policy.membership.line", "policy_invoice_id", string="Memberships")
    company_seal = fields.Binary(string="Stamp Image")
    is_rent_a_car = fields.Boolean(string="Is Rent a Car Service", default=False)

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'res.company'),
            ('res_id', '=', self.env.company.id),
            ('name', '=', 'aaa_seal.jpg')
        ], limit=1)
        if attachment:
            res.company_seal = attachment.datas
        return res
    

    def action_post(self):
        result = super().action_post()
        for record in self:
            if record.invoice_line_type == 'separate':
                record.service_id.invoice_state = 'invoiced'
                record.service_id.invoiced_by = self.env.user.id
                record.service_id.invoiced_date = record.invoice_date
                record.service_id.invoice_id = record.id
            
            else:
                for line in record.credit_service_line_ids:
                    line.service_number_id.invoice_state = 'invoiced'
                    line.service_number_id.invoiced_by = self.env.user.id
                    line.service_number_id.invoiced_date = record.invoice_date
                    line.service_number_id.invoice_id = record.id
        
        return result


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

            # if record.state != 'draft':
            #     record.button_draft()
            if record.state != 'draft':
                # If it's already posted, skip modifying
                if record.state == 'posted':
                    continue
                # Otherwise, try setting it to draft
                record.button_draft()

            if record.member_type == "credit":

                all_services = self.env["aaa.service"].search(
                    [("customer_id", "=", record.partner_id.id),("sequence_id","=",record.category_id.id),("state","=","done"),("invoice_state","=","not_invoiced")] 
                )
                invoice_lines = []
                total = 0
                service_count = 0
                credit_services = {}
                # quantity = 0

                record.invoice_line_ids = [(5, 0, 0)]
                record.credit_service_line_ids = [(5, 0, 0)]

                for service in all_services:
                    service_date = service.service_time.date()
                    if record.from_date <= service_date <= record.to_date:

                        price_list_item = self.env["product.pricelist.item"].search([('product_tmpl_id','=',service.product_id.id), ('pricelist_id','=',record.partner_id.property_product_pricelist_id.id),
                        ('date_start', '<=', service_date),
                        ('date_end', '>=', service_date)])
                
                        service_rate = self.env["service.rate"].search([('product_pricelist_item_id','=',price_list_item.id),
                                                                ('from_loc_id','=',service.from_location.id),
                                                                ('to_loc_id','=',service.to_location.id),],limit=1)
                        
                        total += service_rate.price
                        service_count += 1
  

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

                       

                tax = self.env['account.tax'].search([('amount', '=', 5), ('type_tax_use', '=', 'sale'), ('active', '=', 'True')])

                invoice_lines = [(0, 0, {
                            "name": f"Services Provided for Customer: {record.partner_id.name} from {record.from_date.strftime('%d/%m/%Y')} to {record.to_date.strftime('%d/%m/%Y')} ({service_count} services)",
                            "price_unit": total,
                            "quantity": 1,
                            "tax_ids": [(6, 0, [tax.id])]
                            })]
                credit_service_lines = [(0, 0, values)
                                            for values in credit_services.values()]

                record.write({"invoice_line_ids": invoice_lines,
                              "credit_service_line_ids": credit_service_lines})
                
                for line in record.invoice_line_ids:
                    line.vat_amount = line.price_total - line.price_subtotal


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
                policy_memberships = {}
                product_quantity = {}

                record.invoice_line_ids = [(5, 0, 0)]
                record.policy_membership_line_ids = [(5, 0, 0)]

                for rec in all_records:
                    product_id = rec.product_template_id.id

                    amount = self.env["product.pricelist.item"].search([('product_tmpl_id','=',product_id), ('pricelist_id','=',record.partner_id.property_product_pricelist_id.id)])

                    policy_memberships[rec.id] = {
                        'membership_no': rec.old_membership_number or rec.ref_num or False,
                        'name': rec.name or False,
                        'plate_no': rec.vehicle_plate or False,
                        'chasis_no': rec.vehicle_chasis_no or False,
                        'policy_no': rec.policy_no or False,
                        'start_date': rec.member_activate_date if rec.member_activate_date else False,
                        'expiry_date': rec.member_expiry_date if rec.member_expiry_date else False,
                        'car_make': rec.vehicle_type or False,
                        'amount': amount.fixed_price,
                    } 

                    if product_id in product_quantity:
                            product_quantity[product_id]["quantity"] += 1

                    else:
                        product_quantity[product_id] = {
                            "product_id": product_id,
                            "price_unit": 0,
                            "quantity": 1,
                            "name": f"{rec.product_template_id.name} MEMBERSHIP FOR THE PERIOD FROM {record.from_date.strftime('%d/%m/%Y')} TO {record.to_date.strftime('%d/%m/%Y')}",
                        }

                for key in product_quantity.keys():
                    pricelist_item = self.env["product.pricelist.item"].search([('product_tmpl_id','=',key), ('pricelist_id','=',record.partner_id.property_product_pricelist_id.id)])
                    
                    product_quantity[key]["price_unit"] = pricelist_item.fixed_price
                    

                invoice_lines = [(0, 0, values)
                                    for values in product_quantity.values()]
                policy_membership_lines = [(0, 0, values)
                                            for values in policy_memberships.values()]

                record.write({"invoice_line_ids": invoice_lines,
                              "policy_membership_line_ids": policy_membership_lines})
                
                for line in record.invoice_line_ids:
                    line.vat_amount = line.price_total - line.price_subtotal


    
    def _compute_service_id_domain(self):

        for record in self:

            record.invoice_line_ids = [(5, 0, 0)]
            record.credit_service_line_ids = [(5, 0, 0)]
            record.policy_membership_line_ids = [(5, 0, 0)]
            record.product_id = False
            record.service_id = False

            if not record.from_date or not record.to_date or not record.partner_id or not record.category_id or record.invoice_line_type != "separate":
                continue

            if record.member_type == "credit": 

                all_services = self.env["aaa.service"].search(
                    [("customer_id", "=", record.partner_id.id),
                    ("sequence_id","=",record.category_id.id),
                    ("state","=","done"),
                    ("invoice_state","=","not_invoiced")] 
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

            if record.state != 'draft':
                # If it's already posted, skip modifying
                if record.state == 'posted':
                    continue
                # Otherwise, try setting it to draft
                record.button_draft()
            
            record.invoice_line_ids = [(5, 0, 0)]

            quantity = 0

            if record.member_type == "credit":

                if not record.service_id:
                    continue

                service_date = record.service_id.service_time.date()
                
                price_list_item = self.env["product.pricelist.item"].search([('product_tmpl_id','=',record.service_id.product_id.id), ('pricelist_id','=',record.partner_id.property_product_pricelist_id.id),
                ('date_start', '<=', service_date),
                ('date_end', '>=', service_date)])
                
                service_rate = self.env["service.rate"].search([('product_pricelist_item_id','=',price_list_item.id),
                                                                ('from_loc_id','=',record.service_id.from_location.id),
                                                                ('to_loc_id','=',record.service_id.to_location.id)],limit=1)
                
                if record.service_id.product_id.name == "RENT A CAR" or record.service_id.product_id.name == "RENT A CAR - UPGRADE":

                    from_time = fields.Datetime.context_timestamp(record, record.service_id.date_time_from).strftime('%d/%m/%Y %H:%M:%S')
                    to_time = fields.Datetime.context_timestamp(record, record.service_id.date_time_to).strftime('%d/%m/%Y %H:%M:%S')

                    name = f"{record.service_id.product_id.name} {record.service_id.vehicle_type or ''} {record.service_id.vehicle_model or ''} {record.service_id.vehicle_chasis_no} FROM: {from_time} TO: {to_time}"

                    quantity = record.service_id.quantity
                
                else:
                    name = f"{record.service_id.product_id.name} {record.service_id.vehicle_type or ''} {record.service_id.vehicle_model or ''} {record.service_id.vehicle_chasis_no} FROM: {record.service_id.from_location.name} TO: {record.service_id.to_location.name}"

                    quantity = 1

                invoice_line_items = {
                            "product_id": record.service_id.product_id.id,
                            "price_unit": service_rate.price,
                            "quantity": quantity,
                            "name": name,
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
                            "name": f"{record.product_id.name} MEMBERSHIP FOR THE PERIOD FROM {record.from_date.strftime('%d/%m/%Y')} TO {record.to_date.strftime('%d/%m/%Y')}",
                            }

            
            record.write({"invoice_line_ids":[(0,0,invoice_line_items)]})

            for line in record.invoice_line_ids:
                    line.vat_amount = line.price_total - line.price_subtotal


    def compute_credit_service_line_total(self):
        for record in self:
            total_price = sum(line.price for line in record.credit_service_line_ids if line.add_to_invoice)
            for line_id in record.invoice_line_ids: 
                record.write({"invoice_line_ids":[(1,line_id.id,{"price_unit":total_price})]})




class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    vat_amount = fields.Monetary(string="Tax Amount", readonly=True,
        currency_field='company_currency_id')                
            
            
class CreditServiceLine(models.Model):
    _name = 'credit.service.line'
    _description = 'Credit Service Lines'

    credit_invoice_id = fields.Many2one('account.move', string="Invoice ID")
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
    add_to_invoice = fields.Boolean(string="Add to Invoice", default=True)


class PolicyMembershipLine(models.Model):
    _name = 'policy.membership.line'
    _description = 'Policy Membership Lines'
    
    policy_invoice_id = fields.Many2one('account.move', string="Invoice ID")
    membership_no = fields.Char(string="Membership No.")
    name = fields.Char(string="Name")
    plate_no = fields.Char(string="Plate No.")
    chasis_no = fields.Char(string="Chassis No.")
    policy_no = fields.Char(string="Policy No.")
    start_date = fields.Date(string="Start Date")
    expiry_date = fields.Date(string="Expiry Date")
    car_make = fields.Char(string="Membership No.")
    amount = fields.Float(string="Amount")

    
