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
                    [("customer_id", "=", record.partner_id.id),("sequence_id","=",record.category_id.id),("state","=","done")] 
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
                            "service_number": service.name,
                            "trip_sheet_number": service.credit_proforma_number,
                            "vehicle_model": service.vehicle_model,
                            "vehicle_plate": service.vehicle_plate,
                            "service_product": service.product_id.name,
                            "from_location": service.from_location.name,
                            "to_location": service.to_location.name,
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
                        'membership_no': rec.old_membership_number or rec.ref_num or '',
                        'name': rec.name or '',
                        'plate_no': rec.vehicle_plate or '',
                        'chasis_no': rec.vehicle_chasis_no or '',
                        'policy_no': rec.policy_no or '',
                        'start_date': rec.member_activate_date if rec.member_activate_date else '',
                        'expiry_date': rec.member_expiry_date if rec.member_expiry_date else '',
                        'car_make': rec.vehicle_type or '',
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

    


    # def number_to_words(n):
    #     ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    #     tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    #     teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen",
    #             "Sixteen", "Seventeen", "Eighteen", "Nineteen"]

    #     def convert_chunk(num):
    #         word = ""
    #         if num >= 100:
    #             word += ones[num // 100] + " Hundred "
    #             num %= 100
    #         if 10 <= num < 20:
    #             word += teens[num - 10] + " "
    #         else:
    #             if num >= 20:
    #                 word += tens[num // 10] + " "
    #                 num %= 10
    #             if num > 0:
    #                 word += ones[num] + " "
    #         return word.strip()

    #     if n == 0:
    #         return "Zero"

    #     chunks = []
    #     units = ["", "Thousand", "Million", "Billion"]
    #     i = 0

    #     while n > 0:
    #         chunk = n % 1000
    #         if chunk:
    #             chunk_word = convert_chunk(chunk)
    #             if units[i]:
    #                 chunk_word += " " + units[i]
    #             chunks.append(chunk_word)
    #         n //= 1000
    #         i += 1

    #     return " ".join(reversed(chunks)).strip()

    # def action_report_invoice(self):
    #     from reportlab.lib.pagesizes import landscape, A4
    #     from reportlab.pdfgen import canvas
    #     from reportlab.lib.units import inch
    #     from reportlab.lib.utils import ImageReader
    #     #from num2words import num2words
    #     import io, base64, textwrap
    #     from datetime import datetime

        #self.compute_services_based_on_date()
        # if self.member_type == 'policy':
        #     if self.invoice_line_type == 'consolidated':
        #         self.compute_services_based_on_date()
        #     elif self.invoice_line_type == 'separate':
        #         self.compute_separate_invoice_line()

        # buffer = io.BytesIO()
        # pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
        # width, height = landscape(A4)
        # margin = 20

        # logo_width, logo_height = 1.2 * inch, 1.2 * inch
        # headers = ['MEMBERSHIP\nNO.', 'NAME', 'CUSTOMER', 'PLATE\nNO.', 'CHASIS\nNO.', 'POLICY\nNO.',
        #         'START\nDATE', 'EXPIRY\nDATE', 'CAR\nMAKE', 'AMOUNT']
        # col_widths = [65, 115, 115, 65, 95, 85, 65, 65, 75, 60]
        # header_height = 40
        # row_height = 30

       

        # def number_to_words(n):
        #     ones = ["", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE"]
        #     tens = ["", "", "TWENTY", "THIRTY", "FORTY", "FIFTY", "SIXTY", "SEVENTY", "EIGHTY", "NINETY"]
        #     teens = ["TEN", "ELEVEN", "TWELVE", "THIRTEEN", "FOURTEEN", "FIFTEEN",
        #             "SIXTEEN", "SEVENTEEN", "EIGHTEEN", "NINETEEN"]


        #     def convert_chunk(num):
        #         word = ""
        #         if num >= 100:
        #             word += ones[num // 100] + " HUNDRED "
        #             num %= 100
        #         if 10 <= num < 20:
        #             word += teens[num - 10] + " "
        #         else:
        #             if num >= 20:
        #                 word += tens[num // 10] + " "
        #                 num %= 10
        #             if num > 0:
        #                 word += ones[num] + " "
        #         return word.strip()

        #     if n == 0:
        #         return "ZERO"

        #     chunks = []
        #     units = ["", "THOUSAND", "MILLION", "BILLION"]
        #     i = 0

        #     while n > 0:
        #         chunk = n % 1000
        #         if chunk:
        #             chunk_word = convert_chunk(chunk)
        #             if units[i]:
        #                 chunk_word += " " + units[i]
        #             chunks.append(chunk_word)
        #         n //= 1000
        #         i += 1

        #     return " ".join(reversed(chunks)).strip()

    

        # def draw_invoice_first_page(pdf):
        #     from datetime import datetime
        #     import io
        #     import base64
        #     from reportlab.lib.utils import ImageReader
        #     from reportlab.lib.utils import simpleSplit

        #     width, height = pdf._pagesize
        #     margin = 40
        #     logo_width, logo_height = 100, 50
        #     table_x = margin
        #     table_y = height - 145
        #     table_width = width - 2 * margin
        #     table_height = 650

        #     pdf.setStrokeColorRGB(0, 0, 0)
        #     pdf.setFont("Helvetica", 9)
        #     pdf.setLineWidth(1)

        #     # Default logo_y so it's available even if no logo is set
        #     logo_y = height - margin - logo_height

        #     # 1. Logo and Tagline
        #     company = self.env['res.company'].search([], limit=1)
        #     if company.logo:
        #         logo_data = base64.b64decode(company.logo)
        #         logo_image = ImageReader(io.BytesIO(logo_data))
        #         logo_x = width - margin - logo_width
        #         pdf.drawImage(logo_image, logo_x, logo_y, width=logo_width, height=logo_height)

        #     # Tagline just below the logo
        #     pdf.setFont("Helvetica", 10)
        #     tagline_y = logo_y - 15
        #     pdf.drawRightString(width - margin, tagline_y, "We guarantee to get you moving...")



        #     # 2. Outer Box
        #     box_top = table_y
        #     box_bottom = table_y - table_height
        #     pdf.rect(table_x, box_bottom, table_width, table_height)

        #     cursor_y = table_y - 20

        #     # 3. TAX INVOICE Heading
        #     pdf.setFont("Helvetica-Bold", 16)
        #     pdf.drawCentredString(width / 2, cursor_y, "TAX INVOICE")
        #     cursor_y -= 30

           
        #     # 4. Metadata Section Box
        #     metadata_box_top = cursor_y
        #     metadata_box_bottom = cursor_y - 90
        #     pdf.rect(table_x, metadata_box_bottom, table_width, metadata_box_top - metadata_box_bottom)
        #     pdf.setFont("Helvetica", 9)

        #     # Left and right positions
        #     left_x = table_x + 10
        #     right_x = table_x + table_width / 2 + 10
        #     left_cursor_y = metadata_box_top - 10
        #     right_cursor_y = metadata_box_top - 10
        #     line_height = 12

           

        #     # Left Block
        #     pdf.setFont("Helvetica-Bold", 9)
        #     pdf.drawString(left_x, left_cursor_y, "M/s.")

        #     pdf.setFont("Helvetica", 9)
        #     ms_width = pdf.stringWidth("M/s. ", "Helvetica-Bold", 9)
        #     pdf.drawString(left_x + ms_width, left_cursor_y, self.partner_id.name or '')

        #     left_cursor_y -= line_height
        #     pdf.drawString(left_x, left_cursor_y, f"{self.partner_id.street or ''} {self.partner_id.city or ''}")
        #     left_cursor_y -= line_height
        #     pdf.drawString(left_x, left_cursor_y, self.partner_id.country_id.name or '')

        #     # Draw horizontal separator line before TRN
        #     left_cursor_y -= line_height / 2  # spacing before line
        #     line_start_x = table_x  # left edge of the metadata box
        #     line_end_x = table_x + table_width / 2  # right edge is at the vertical center line
        #     pdf.line(line_start_x, left_cursor_y, line_end_x, left_cursor_y)

        #     # Spacing after the line before writing TRN
        #     left_cursor_y -= line_height  # extra spacing to avoid overlap

        #     # TRN section
        #     trn_value = self.partner_id.trn_number or 'N/A'
        #     pdf.setFont("Helvetica", 9)
        #     pdf.drawString(left_x, left_cursor_y, "TRN :")
        #     pdf.setFont("Helvetica-Bold", 9)
        #     pdf.drawString(left_x + 35, left_cursor_y, trn_value)



        #     # === Right Block ===

        #     row_height = line_height + 6       # Space between rows
        #     text_baseline_offset = 1           # Distance from top of row to text baseline

        #     label_font = "Helvetica-Bold"
        #     value_font = "Helvetica"
        #     font_size = 9

        #     # -------- Invoice No --------
        #     pdf.setFont(label_font, font_size)
        #     pdf.drawString(right_x, right_cursor_y - text_baseline_offset, "Invoice No :")
        #     pdf.setFont(value_font, font_size)
        #     pdf.drawString(right_x + 70, right_cursor_y - text_baseline_offset, self.payment_reference or 'DRAFT')
        #     pdf.line(table_x + table_width / 2, right_cursor_y - row_height // 2, table_x + table_width, right_cursor_y - row_height // 2)
        #     right_cursor_y -= row_height

        #     # -------- Date --------
        #     pdf.setFont(label_font, font_size)
        #     pdf.drawString(right_x, right_cursor_y - text_baseline_offset, "Date :")
        #     pdf.setFont(value_font, font_size)
        #     pdf.drawString(right_x + 70, right_cursor_y - text_baseline_offset, datetime.today().strftime('%d/%m/%Y'))
        #     pdf.line(table_x + table_width / 2, right_cursor_y - row_height // 2, table_x + table_width, right_cursor_y - row_height // 2)
        #     right_cursor_y -= row_height

        #     # -------- TRN --------
        #     pdf.setFont(label_font, font_size)
        #     pdf.drawString(right_x, right_cursor_y - text_baseline_offset, "TRN :")
        #     pdf.setFont(value_font, font_size)
        #     pdf.drawString(right_x + 70, right_cursor_y - text_baseline_offset, self.partner_id.trn_number or 'N/A')
        #     pdf.line(table_x + table_width / 2, right_cursor_y - row_height // 2, table_x + table_width, right_cursor_y - row_height // 2)
        #     right_cursor_y -= row_height

        #     # -------- REF Block (No line after this!) --------
        #     if self.member_type == 'credit' and self.invoice_line_type == 'separate':
        #         if self.service_id:
        #             ref_lines = f"{self.service_id.credit_proforma_number or ''} C/O: {self.service_id.credit_customer_co or ''}\n{self.service_id.name or ''}"
        #         else:
        #             ref_lines = self.partner_id.name or ''
        #     else:
        #         ref_lines = self.partner_id.name or ''

        #     ref_label = "REF :"
        #     lines = ref_lines.split('\n')

        #     for idx, line in enumerate(lines):
        #         label = ref_label if idx == 0 else ""
        #         pdf.setFont(label_font if label else value_font, font_size)
        #         pdf.drawString(right_x, right_cursor_y - text_baseline_offset, label)
        #         pdf.setFont(value_font, font_size)
        #         pdf.drawString(right_x + 70, right_cursor_y - text_baseline_offset, line.strip())
        #         right_cursor_y -= row_height
        #         # NO line here!

        #     # -------- Vertical Divider --------
        #     line_x = table_x + table_width / 2
        #     pdf.line(line_x, metadata_box_top, line_x, metadata_box_bottom)

        #     # Update cursor_y below metadata box
        #     cursor_y = metadata_box_bottom - 20

        #     # 5. Invoice Table Headers (Full width match with box)
        #     headers = ["SL No.", "Particular", "Qty", "Rate", "Taxable Amount", "VAT", "Total Amount"]
        #     col_widths_percent = [0.07, 0.30, 0.07, 0.10, 0.18, 0.12, 0.16]  # 100% total
        #     col_widths = [table_width * pct for pct in col_widths_percent]

        #     x = table_x
        #     y = cursor_y

        #     pdf.setFont("Helvetica-Bold", 9)
        #     for i, header in enumerate(headers):
        #         pdf.rect(x, y - 20, col_widths[i], 20)
        #         pdf.drawCentredString(x + col_widths[i] / 2, y - 14, header)
        #         x += col_widths[i]
        #     cursor_y = y - 20

            

        #     pdf.setFont("Helvetica", 8)
        #     sl = 1
        #     total_taxable = total_vat = total_total = 0.0
        #     line_height = 14  # Increased line spacing

        #     for line in self.invoice_line_ids:
        #         qty = line.quantity
        #         rate = line.price_unit
        #         taxable = line.price_subtotal
        #         vat = taxable * 0.05
        #         total = line.price_total

        #         # Wrap text in "Particular"
        #         particular_text = line.name or ''
        #         particular_width = col_widths[1] - 4  # padding
        #         wrapped_particular_lines = simpleSplit(particular_text, 'Helvetica', 8, particular_width)

        #         # Determine row height with added padding
        #         row_lines = len(wrapped_particular_lines)
        #         row_height = max(row_lines * line_height + 4, 18)

        #         values = [str(sl), wrapped_particular_lines, str(qty), f"{rate:.2f}", f"{taxable:.2f}", f"{vat:.2f}", f"{total:.2f}"]

        #         x = table_x
        #         for i, val in enumerate(values):
        #             pdf.rect(x, cursor_y - row_height, col_widths[i], row_height)

        #             if i == 1:  # "Particular" column
        #                 text_y = cursor_y - line_height
        #                 for line_text in val:
        #                     pdf.drawString(x + 2, text_y, line_text)
        #                     text_y -= line_height
        #             else:
        #                 pdf.drawString(x + 2, cursor_y - 11, val)

        #             x += col_widths[i]

        #         cursor_y -= row_height
        #         sl += 1
        #         total_taxable += taxable
        #         total_vat += vat
        #         total_total += total


            
        #     # Assuming 'number_to_words' function is already defined as before
        #     amount_word = number_to_words(int(total_total))
        #     amount_in_words = f"AED {amount_word} ONLY"  # Only the amount in words

        #     # Set the x position and width
        #     x = table_x
        #     span_width = sum(col_widths[:4])

        #     # Draw the rectangle around the entire section
        #     pdf.rect(x, cursor_y - 20, span_width, 20)

        #     # Define the label
        #     label_text = "Invoice Value (In Words):"

        #     # Set bold font and draw the label
        #     pdf.setFont("Helvetica-Bold", 9)
        #     pdf.drawString(x + 3, cursor_y - 14, label_text)

        #     # Measure label width to position the next text right after it
        #     label_width = pdf.stringWidth(label_text, "Helvetica-Bold", 9)

        #     # Set regular font and draw the amount right after the label
        #     pdf.setFont("Helvetica", 9)
        #     pdf.drawString(x + 3 + label_width + 2, cursor_y - 14, amount_in_words)

        #     # Update the x position
        #     x += span_width

            # # Assuming 'number_to_words' function is already defined as before
            # amount_word = number_to_words(int(total_total))
            # amount_in_words = f"AED {amount_word} ONLY"

            # # Set the x position and total width to span across
            # x = table_x
            # span_width = sum(col_widths[:4])

            # # Label text
            # label_text = "Invoice Value (In Words):"

            # # Set font and calculate label width
            # pdf.setFont("Helvetica-Bold", 9)
            # label_width = pdf.stringWidth(label_text, "Helvetica-Bold", 9)

            # # Available width for wrapped text after label and padding
            # available_width = span_width - (label_width + 8)  # padding: 3 (left) + 2 (gap) + 3 (right)

            # # Wrap the amount_in_words
            # wrapped_lines = simpleSplit(amount_in_words, 'Helvetica', 9, available_width)

            # # Calculate required height based on number of lines
            # line_height = 12  # Adjust if needed
            # wrapped_height = max(len(wrapped_lines) * line_height + 6, 20)  # 6px padding

            # # Draw the rectangle for the entire section
            # pdf.rect(x, cursor_y - wrapped_height, span_width, wrapped_height)

            # # Draw the label
            # pdf.setFont("Helvetica-Bold", 9)
            # pdf.drawString(x + 3, cursor_y - line_height, label_text)

            # Draw wrapped amount text
            # pdf.setFont("Helvetica", 9)
            # text_x = x + 3 + label_width + 2
            # text_y = cursor_y - line_height
            # for line in wrapped_lines:
            #     pdf.drawString(text_x, text_y, line)
            #     text_y -= line_height

            # # Update cursor_y and x
            # # cursor_y -= wrapped_height
            # x += span_width


            

        #     # Set font to bold for the values and currency
        #     pdf.setFont("Helvetica-Bold", 9)

        #     total_values = [
        #         (f"{total_taxable:.2f} AED", col_widths[4]),
        #         (f"{total_vat:.2f} AED", col_widths[5]),
        #         (f"{total_total:.2f} AED", col_widths[6])
        #     ]

        #     for value, width_ in total_values:
        #         pdf.rect(x, cursor_y - 20, width_, 20)
        #         pdf.drawRightString(x + width_ - 3, cursor_y - 14, value)
        #         x += width_

        #     cursor_y -= 30
        #      # 8. Bank Details
        #     bank_lines = [
        #         "Bank Details",
        #         "Beneficiary: ARABIAN AUTOMOBILE ASSOCIATION",
        #         "AED Account No: 101 20410956 01",
        #         "IBAN: AE72 0260 0010 1204 1095 601",
        #         "EMIRATES NBD Group Head Office Dubai United Arab Emirates",
        #         "Swift Code: EBILAEAD",
        #     ]

        #     bank_section_top_y = cursor_y  # Store top Y for later border

        #     for i, line in enumerate(bank_lines):
        #         if i == 0:
        #             pdf.setFont("Helvetica-Bold", 8)  # Bold for "Bank Details"
        #         else:
        #             pdf.setFont("Helvetica", 8)       # Regular font for the rest
        #         pdf.drawString(table_x + 10, cursor_y, line)
        #         cursor_y -= 12
    

        #     # Signature Section
        #     signature_box_height = 72  # Same height as bank section (6 lines × 12px spacing)
        #     signature_box_top = cursor_y
        #     signature_box_bottom = cursor_y - signature_box_height

        #     # Draw only the bottom border of the signature section (remove the top border)
        #     pdf.rect(table_x, signature_box_bottom, table_width, signature_box_height, fill=0)  # fill=0 ensures it’s just a border

        #     # Add text inside signature section
        #     cursor_y = signature_box_top - 10  # padding from top

        #     pdf.drawString(table_x + 10, cursor_y, "Prepared by:")
        #     pdf.drawRightString(width - margin, cursor_y, "Received by:")

        #     cursor_y -= 30  # Adjust vertical spacing for the second row of text

        #     # Draw both strings at the same y-coordinate
        #     pdf.drawString(table_x + 10, cursor_y, "for Arabian Automobile Association")
        #     pdf.drawRightString(width - margin, cursor_y, "Customer Signature")

        #     cursor_y = signature_box_bottom - 10  # move cursor below this box for next section



        #     # 10. Footer
        #     footer_height = 40  # Height of the footer section (adjust as needed)
        #     footer_box_top = cursor_y
        #     footer_box_bottom = cursor_y - footer_height

        #     # Calculate the width of the footer (same as the invoice table width)
        #     footer_box_width = table_width  # Same width as the table box

        #     # Draw a bottom border line to enclose the footer content, restricted to the footer width
        #     pdf.rect(table_x, footer_box_bottom, footer_box_width, footer_height, fill=0)  # fill=0 ensures it's just a border

        #     # Set footer text
        #     pdf.setFont("Helvetica", 7)
        #     footer_1 = "P.O.BOX 80846, DUBAI, U.A.E TEL NO: 04-2578484 FAX NO: 04-2578351 EMAIL: accounts@aaaemirates.com WEBSITE:www.aaaemirates.com"
        #     footer_2 = "This Tax Invoice has been electronically approved and signed by an authorised personnel of AAA"

        #     # Add footer content inside the restricted footer width
        #     pdf.drawCentredString(width / 2, footer_box_top - 10, footer_1)

        #     # Draw a single full-width horizontal line between footer_1 and footer_2
        #     line_y_position = footer_box_top - 20  # Position of the line
        #     pdf.line(margin, line_y_position, width - margin, line_y_position)  # Full-width line

        #     # Move the cursor position down for the second footer text
        #     footer_box_top -= 25  # Adjusted for spacing between line and second text

        #     # Add the second footer text
        #     pdf.drawCentredString(width / 2, footer_box_top - 10, footer_2)

        #     # Move the cursor for the next content after the footer
        #     cursor_y = footer_box_bottom - 10  # Adjust the cursor position after the footer

        # # Finalize
        #     pdf.showPage()



        # def draw_service_statement_page(pdf):
        #     from reportlab.lib.colors import HexColor, white, black
        #     from reportlab.lib.utils import ImageReader
        #     import base64, io
        #     from reportlab.pdfbase.pdfmetrics import stringWidth

        #     # Get company data
        #     company = self.env['res.company'].search([], limit=1)

        #     # PDF dimensions
        #     width, height = pdf._pagesize
        #     margin = 30
        #     table_width = width - 2 * margin  # Ensures table fits within page margins
        #     y_position = height - margin

        #     # Draw logo
        #     if company.logo:
        #         logo = base64.b64decode(company.logo)
        #         logo_image = ImageReader(io.BytesIO(logo))
        #         pdf.drawImage(logo_image, width - 140, y_position - 50, width=100, height=40)

        #     # Draw title
        #     pdf.setFont("Helvetica-Bold", 16)
        #     title = "SERVICE STATEMENT"
        #     pdf.drawCentredString(width / 2, y_position - 60, title)

        #     # Setup
        #     y_position -= 90
        #     row_height = 20
        #     padding = 4

        #     headers = [
        #         "Service Date", "Service Number", "Trip Sheet No.",
        #         "Vehicle Model", "Vehicle Plate", "From Location",
        #         "To Location", "Total"
        #     ]

        #     col_widths_percent = [0.10, 0.14, 0.12, 0.13, 0.13, 0.13, 0.13, 0.12]
        #     col_widths = [table_width * pct for pct in col_widths_percent]

        #     def wrap_text(text, max_width, font_name="Helvetica", font_size=8):
        #         words = str(text).split()
        #         lines, current_line = [], ""
        #         for word in words:
        #             test_line = f"{current_line} {word}".strip()
        #             if stringWidth(test_line, font_name, font_size) <= max_width - 2 * padding:
        #                 current_line = test_line
        #             else:
        #                 lines.append(current_line)
        #                 current_line = word
        #         if current_line:
        #             lines.append(current_line)
        #         return lines

        #     def draw_table_header(y):
        #         pdf.setFont("Helvetica-Bold", 8)
        #         pdf.setFillColor(HexColor("#00007A"))
        #         x = margin
        #         for i, header in enumerate(headers):
        #             w = col_widths[i]
        #             pdf.setFillColor(HexColor("#00007A"))
        #             pdf.rect(x, y, w, row_height, fill=1)
        #             pdf.setFillColor(white)
        #             pdf.drawCentredString(x + w / 2, y + 6, header)
        #             x += w
        #         pdf.setFillColor(black)

        #     draw_table_header(y_position)
        #     y_position -= row_height

        #     pdf.setFont("Helvetica", 8)

        #     total_sum = 0

        #     for record in self.credit_service_line_ids:
        #         service_price = record.price or 0.0

        #         values = [
        #             record.service_date.strftime('%d/%m/%Y') if record.service_date else '',
        #             record.service_number or '',
        #             record.trip_sheet_number or '',
        #             record.vehicle_model or '',
        #             record.vehicle_plate or '',
        #             record.from_location if record.from_location else '',
        #             record.to_location if record.to_location else '',
        #             f"{service_price:.2f}",
        #         ]

        #         wrapped = [wrap_text(val, col_widths[i]) for i, val in enumerate(values)]
        #         max_lines = max(len(lines) for lines in wrapped)
        #         actual_row_height = max_lines * 10 + 4

        #         if y_position - actual_row_height < 60:
        #             pdf.showPage()
        #             y_position = height - margin
        #             draw_table_header(y_position)
        #             y_position -= row_height
        #             pdf.setFont("Helvetica", 8)

        #         x = margin
        #         for i, lines in enumerate(wrapped):
        #             pdf.rect(x, y_position - actual_row_height, col_widths[i], actual_row_height)
        #             for j, line in enumerate(lines):
        #                 pdf.drawString(x + padding, y_position - 12 - j * 10, line)
        #             x += col_widths[i]

        #         total_sum += service_price * 1.05

        #         y_position -= actual_row_height

        #     # TOTAL row
        #     values = ["", "", "", "", "", "", "TOTAL", f"{total_sum:.2f}"]
        #     wrapped = [wrap_text(val, col_widths[i]) for i, val in enumerate(values)]
        #     max_lines = max(len(lines) for lines in wrapped)
        #     actual_row_height = max_lines * 10 + 4

        #     x = margin
        #     for i, lines in enumerate(wrapped):
        #         if i in (6, 7):  # Bold both "TOTAL" and the value
        #             pdf.setFont("Helvetica-Bold", 8)
        #         else:
        #             pdf.setFont("Helvetica", 8)

        #         pdf.rect(x, y_position - actual_row_height, col_widths[i], actual_row_height)
        #         for j, line in enumerate(lines):
        #             pdf.drawString(x + padding, y_position - 12 - j * 10, line)
        #         x += col_widths[i]

        #     y_position -= actual_row_height
        #     pdf.showPage()






        # def draw_header():
        #     company = self.env['res.company'].search([], limit=1)
        #     if company.logo:
        #         logo_data = base64.b64decode(company.logo)
        #         logo_image = ImageReader(io.BytesIO(logo_data))
        #         pdf.drawImage(
        #             logo_image,
        #             width - margin - logo_width,
        #             height - logo_height - 10,
        #             width=logo_width,
        #             height=logo_height,
        #         )

        #     pdf.setFont("Helvetica-Bold", 12)
        #     title = "Invoice Members Report"
        #     pdf.drawString((width - pdf.stringWidth(title, "Helvetica-Bold", 12)) / 2, height - 40, title)

        #     pdf.setFont("Helvetica", 10)
        #     package = f"Customer: {self.partner_id.name} | Type: {self.member_type}"
        #     pdf.drawString((width - pdf.stringWidth(package, "Helvetica", 10)) / 2, height - 55, package)

        #     pdf.setFont("Helvetica", 8)
        #     tagline_y = height - logo_height - 15
        #     pdf.drawRightString(width - margin, tagline_y, "We guarantee to get you moving...")

        # def draw_table_header(y_position):
        #     x_offset = margin
        #     pdf.setFont("Helvetica-Bold", 8)
        #     for i, header in enumerate(headers):
        #         pdf.rect(x_offset, y_position - header_height, col_widths[i], header_height)
        #         for j, line in enumerate(header.split('\n')):
        #             text_width = pdf.stringWidth(line, "Helvetica-Bold", 8)
        #             x_text = x_offset + (col_widths[i] - text_width) / 2
        #             y_text = y_position - 15 - (j * 10)
        #             pdf.drawString(x_text, y_text, line)
        #         x_offset += col_widths[i]
        #     return y_position - header_height

        # def draw_data_row(data, y_position):
        #     x_offset = margin
        #     pdf.setFont("Helvetica", 7)
        #     line_height = 8

        #     def wrap_text(text, width):
        #         text = str(text) if text else ''
        #         max_chars = int(width / 5.5)
        #         return textwrap.wrap(text, max_chars)

        #     max_lines = 1
        #     column_lines = []
        #     for i, value in enumerate(data.values()):
        #         wrapped = wrap_text(value, col_widths[i])
        #         column_lines.append(wrapped)
        #         max_lines = max(max_lines, len(wrapped))

        #     adjusted_row_height = row_height * max_lines
        #     for i, lines in enumerate(column_lines):
        #         pdf.rect(x_offset, y_position - adjusted_row_height, col_widths[i], adjusted_row_height)
        #         start_y = y_position - line_height
        #         for line in lines:
        #             pdf.drawString(x_offset + 5, start_y, line)
        #             start_y -= line_height
        #         x_offset += col_widths[i]
        #     return y_position - adjusted_row_height

        # def collect_and_print_data():
        #     data_list = []

        #     product_ids = self.invoice_line_ids.mapped('product_id.product_tmpl_id.id')
        #     product_price_map = {
        #         line.product_id.product_tmpl_id.id: line.price_unit
        #         for line in self.invoice_line_ids
        #     }

        #     partner_domain = [
        #         ('product_template_id', 'in', product_ids),
        #         ('member_type', '=', self.member_type),
        #         ('member_partner_category_id', '=', self.category_id.id),
        #         ('parent_customer_id', '=', self.partner_id.id),
        #         ('membership_state', '=', 'confirm'),
        #         ('invoice_ref_date', '>=', self.from_date),
        #         ('invoice_ref_date', '<=', self.to_date),
        #     ]

        #     history_domain = [
        #         ('product_template_id', 'in', product_ids),
        #         ('member_type', '=', self.member_type),
        #         ('member_partner_category_id', '=', self.category_id.id),
        #         ('parent_customer_id', '=', self.partner_id.id),
        #         ('invoice_ref_date', '>=', self.from_date),
        #         ('invoice_ref_date', '<=', self.to_date),
        #     ]

        #     partners = self.env['res.partner'].search(partner_domain)
        #     histories = self.env['membership.history'].search(history_domain)

        #     for record in list(partners) + list(histories):
        #         product_id = record.product_template_id.id
        #         amount = product_price_map.get(product_id, 0.0)

        #         # data_list.append({
        #         #     'membership_no': record.old_membership_number or record.ref_num or '',
        #         #     'name': record.name or '',
        #         #     'customer': record.parent_customer_id.name or '',
        #         #     'plate_no': record.vehicle_plate or '',
        #         #     'chasis_no': record.vehicle_chasis_no or '',
        #         #     'policy_no': record.policy_no or '',
        #         #     'start_date': record.member_activate_date.strftime('%d-%m-%Y') if record.member_activate_date else '',
        #         #     'expiry_date': record.member_expiry_date.strftime('%d-%m-%Y') if record.member_expiry_date else '',
        #         #     'car_make': record.vehicle_type or '',
        #         #     'amount': f"{amount:.2f}",
        #         # })

        #     draw_header()
        #     y = draw_table_header(height - 120)

        #     for row in data_list:
        #         y = draw_data_row(row, y)
        #         if y < 50:
        #             pdf.showPage()
        #             draw_header()
        #             y = draw_table_header(height - 120)

        
        # #draw_invoice_first_page(pdf)

        

        # draw_invoice_first_page(pdf)

        # # Logic for handling different member types and invoice line types
        # if self.member_type == 'credit':
        #     if self.invoice_line_type == 'separate':
        #         # Skip collect_and_print_data() entirely
        #         pass
        #     elif self.invoice_line_type == 'consolidated':
        #         # Skip collect_and_print_data(), but draw service statement
        #         draw_service_statement_page(pdf)
        #     else:
        #         # Default behavior for credit members with other invoice types
        #         collect_and_print_data()
        # else:
        #     # Non-credit members
        #     collect_and_print_data()

        # pdf.save()
        # buffer.seek(0)


        # attachment = self.env['ir.attachment'].create({
        #     'name': f"Invoice_Members_Report_{self.id}.pdf",
        #     'datas': base64.b64encode(buffer.read()),
        #     'type': 'binary',
        # })

        # return {
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'ir.attachment',
        #     'res_id': attachment.id,
        #     'view_mode': 'form',
        #     'target': 'new',
        # }


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    vat_amount = fields.Monetary(string="Tax Amount", readonly=True,
        currency_field='company_currency_id')                
            
            
class CreditServiceLine(models.Model):
    _name = 'credit.service.line'
    _description = 'Credit Service Lines'

    credit_invoice_id = fields.Many2one('account.move', string="Invoice ID")
    service_date = fields.Date(string="Service Date")
    service_number = fields.Char(string="Service Number")
    trip_sheet_number = fields.Char(string="Trip Sheet No.")
    vehicle_model = fields.Char(string="Vehicle Model")
    vehicle_plate = fields.Char(string="Vehicle Plate")
    service_product = fields.Char(string="Product")
    from_location = fields.Char(string="From Location")
    to_location = fields.Char(string="To Location")
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

    
