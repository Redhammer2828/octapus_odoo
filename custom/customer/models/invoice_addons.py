from odoo import models, fields, api
from itertools import chain
from datetime import datetime
import io
import base64
import textwrap
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import inch

class AccountMove(models.Model):
    _inherit = 'account.move'

    member_type = fields.Selection([
        ('policy', 'Policy Member'),
        ('credit', 'Credit Member')
    ], string='Member Type')

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

            if record.state != 'draft':
                record.button_draft()

            record.invoice_line_ids = [(5, 0, 0)]

            invoice_lines = []
            product_quantity = {}

            if record.member_type == "credit":
                all_services = self.env["aaa.service"].search([
                    ("customer_id", "=", record.partner_id.id),
                    ("sequence_id", "=", record.category_id.id),
                    ("state", "=", "done")
                ])
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

            elif record.member_type == "policy":
                domain = [
                    ('invoice_ref_date', '>=', record.from_date),
                    ('invoice_ref_date', '<=', record.to_date),
                    ("parent_customer_id", "=", record.partner_id.id),
                    ('member_partner_category_id', '=', record.category_id.id),
                    ('member_type', '=', record.member_type),
                ]

                partner_domain = domain + [('membership_state', '=', 'confirm')]
                partner_records = self.env['res.partner'].search(partner_domain)
                history_records = self.env['membership.history'].search(domain)
                all_records = chain(partner_records, history_records)

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

            invoice_lines = [(0, 0, values) for values in product_quantity.values()]
            record.write({"invoice_line_ids": invoice_lines})

    def _calculate_amount(self, partner):
        return partner.product_template_id.list_price if partner.product_template_id else 0
    
    from datetime import datetime

    def action_report_invoice(self):
        self.compute_services_based_on_date()

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
        width, height = landscape(A4)
        margin = 20

        logo_width, logo_height = 1.2 * inch, 1.2 * inch
        headers = ['MEMBERSHIP\nNO.', 'NAME', 'CUSTOMER', 'PLATE\nNO.', 'CHASIS\nNO.', 'POLICY\nNO.',
                'START\nDATE', 'EXPIRY\nDATE', 'CAR\nMAKE', 'AMOUNT']
        col_widths = [65, 115, 115, 65, 95, 85, 65, 65, 75, 60]
        header_height = 40
        row_height = 30

        def draw_invoice_first_page():
            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawString(margin, height - 40, "Arabian Automobile Association")
            pdf.setFont("Helvetica", 10)
            pdf.drawString(margin, height - 60, "AL NAHDA 2")
            pdf.drawString(margin, height - 75, "DU 80846")
            pdf.drawString(margin, height - 90, "United Arab Emirates")

            # Partner name - top right
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawRightString(width - margin, height - 40, self.partner_id.name)

            # DRAFT INVOICE Title
            title = f"DRAFT INVOICE {self.payment_reference or ''}"
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(margin, height - 130, title)

            # Invoice date
            invoice_date = datetime.today().strftime('%d/%m/%Y')
            pdf.setFont("Helvetica", 10)
            pdf.drawString(margin, height - 150, f"Invoice Date: {invoice_date}")

            # Table headers
            table_headers = ["Description", "Quantity", "Unit Price", "Taxes", "Amount"]
            col_x = [margin, 280, 370, 460, 580]
            pdf.setFont("Helvetica-Bold", 9)
            for i, header in enumerate(table_headers):
                pdf.drawString(col_x[i], height - 180, header)

            # Invoice lines
            pdf.setFont("Helvetica", 8)
            y = height - 200
            for line in self.invoice_line_ids:
                taxes = ", ".join(t.name for t in line.tax_ids)
                values = [
                    line.product_id.display_name or '',
                    str(line.quantity),
                    f"{line.price_unit:.2f}",
                    taxes or '',
                    f"{line.price_subtotal:.2f}",
                ]
                for i, val in enumerate(values):
                    pdf.drawString(col_x[i], y, val)
                y -= 15
                if y < 100:
                    pdf.showPage()
                    y = height - 60

            # Payment Communication
            pdf.setFont("Helvetica", 9)
            pdf.drawString(margin, y - 20, f"Payment Communication: {self.payment_reference or ''}")

            pdf.showPage()

        def draw_header():
            company = self.env['res.company'].search([], limit=1)
            if company.logo:
                logo_data = base64.b64decode(company.logo)
                logo_image = ImageReader(io.BytesIO(logo_data))
                pdf.drawImage(
                    logo_image,
                    width - margin - logo_width,
                    height - logo_height - 10,
                    width=logo_width,
                    height=logo_height,
                )

            pdf.setFont("Helvetica-Bold", 12)
            title = "Invoice Members Report"
            pdf.drawString((width - pdf.stringWidth(title, "Helvetica-Bold", 12)) / 2, height - 40, title)

            pdf.setFont("Helvetica", 10)
            package = f"Customer: {self.partner_id.name} | Type: {self.member_type}"
            pdf.drawString((width - pdf.stringWidth(package, "Helvetica", 10)) / 2, height - 55, package)

            pdf.setFont("Helvetica", 8)
            tagline_y = height - logo_height - 15
            pdf.drawRightString(width - margin, tagline_y, "We guarantee to get you moving...")

        def draw_table_header(y_position):
            x_offset = margin
            pdf.setFont("Helvetica-Bold", 8)
            for i, header in enumerate(headers):
                pdf.rect(x_offset, y_position - header_height, col_widths[i], header_height)
                for j, line in enumerate(header.split('\n')):
                    text_width = pdf.stringWidth(line, "Helvetica-Bold", 8)
                    x_text = x_offset + (col_widths[i] - text_width) / 2
                    y_text = y_position - 15 - (j * 10)
                    pdf.drawString(x_text, y_text, line)
                x_offset += col_widths[i]
            return y_position - header_height

        def draw_data_row(data, y_position):
            x_offset = margin
            pdf.setFont("Helvetica", 7)
            line_height = 8

            def wrap_text(text, width):
                text = str(text) if text else ''
                max_chars = int(width / 5.5)
                return textwrap.wrap(text, max_chars)

            max_lines = 1
            column_lines = []
            for i, value in enumerate(data.values()):
                wrapped = wrap_text(value, col_widths[i])
                column_lines.append(wrapped)
                max_lines = max(max_lines, len(wrapped))

            adjusted_row_height = row_height * max_lines
            for i, lines in enumerate(column_lines):
                pdf.rect(x_offset, y_position - adjusted_row_height, col_widths[i], adjusted_row_height)
                start_y = y_position - line_height
                for line in lines:
                    pdf.drawString(x_offset + 5, start_y, line)
                    start_y -= line_height
                x_offset += col_widths[i]
            return y_position - adjusted_row_height

        def collect_and_print_data():
            data_list = []

            product_ids = self.invoice_line_ids.mapped('product_id.product_tmpl_id.id')

            product_price_map = {
                line.product_id.product_tmpl_id.id: line.price_unit
                for line in self.invoice_line_ids
            }

            partner_domain = [
                ('product_template_id', 'in', product_ids),
                ('member_type', '=', self.member_type),
                ('member_partner_category_id', '=', self.category_id.id),
                ('parent_customer_id', '=', self.partner_id.id),
                ('membership_state', '=', 'confirm'),
                ('invoice_ref_date', '>=', self.from_date),
                ('invoice_ref_date', '<=', self.to_date),
            ]

            history_domain = [
                ('product_template_id', 'in', product_ids),
                ('member_type', '=', self.member_type),
                ('member_partner_category_id', '=', self.category_id.id),
                ('parent_customer_id', '=', self.partner_id.id),
                ('invoice_ref_date', '>=', self.from_date),
                ('invoice_ref_date', '<=', self.to_date),
            ]

            partners = self.env['res.partner'].search(partner_domain)
            histories = self.env['membership.history'].search(history_domain)

            for record in list(partners) + list(histories):
                product_id = record.product_template_id.id
                amount = product_price_map.get(product_id, 0.0)

                data_list.append({
                    'membership_no': record.old_membership_number or record.ref_num or '',
                    'name': record.name or '',
                    'customer': record.parent_customer_id.name or '',
                    'plate_no': record.vehicle_plate or '',
                    'chasis_no': record.vehicle_chasis_no or '',
                    'policy_no': record.policy_no or '',
                    'start_date': record.member_activate_date.strftime('%d-%m-%Y') if record.member_activate_date else '',
                    'expiry_date': record.member_expiry_date.strftime('%d-%m-%Y') if record.member_expiry_date else '',
                    'car_make': record.vehicle_type or '',
                    'amount': f"{amount:.2f}",
                })

            draw_header()
            y = draw_table_header(height - 120)

            for row in data_list:
                y = draw_data_row(row, y)
                if y < 50:
                    pdf.showPage()
                    draw_header()
                    y = draw_table_header(height - 120)

        # First page with invoice-style intro
        draw_invoice_first_page()
        # Member report pages
        collect_and_print_data()

        pdf.save()
        buffer.seek(0)

        attachment = self.env['ir.attachment'].create({
            'name': f"Invoice_Members_Report_{self.id}.pdf",
            'datas': base64.b64encode(buffer.read()),
            'type': 'binary',
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'res_id': attachment.id,
            'view_mode': 'form',
            'target': 'new',
        }

    
    # def action_report_invoice(self):
    #     self.compute_services_based_on_date()

    #     buffer = io.BytesIO()
    #     pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    #     width, height = landscape(A4)
    #     margin = 20

    #     logo_width, logo_height = 1.2 * inch, 1.2 * inch
    #     headers = ['MEMBERSHIP\nNO.', 'NAME', 'CUSTOMER', 'PLATE\nNO.', 'CHASIS\nNO.', 'POLICY\nNO.',
    #             'START\nDATE', 'EXPIRY\nDATE', 'CAR\nMAKE', 'AMOUNT']
    #     col_widths = [65, 115, 115, 65, 95, 85, 65, 65, 75, 60]
    #     header_height = 40
    #     row_height = 30

    #     def draw_header():
    #         company = self.env['res.company'].search([], limit=1)
    #         if company.logo:
    #             logo_data = base64.b64decode(company.logo)
    #             logo_image = ImageReader(io.BytesIO(logo_data))
    #             pdf.drawImage(
    #                 logo_image,
    #                 width - margin - logo_width,
    #                 height - logo_height - 10,
    #                 width=logo_width,
    #                 height=logo_height,
    #             )

    #         pdf.setFont("Helvetica-Bold", 12)
    #         title = "Invoice Members Report"
    #         pdf.drawString((width - pdf.stringWidth(title, "Helvetica-Bold", 12)) / 2, height - 40, title)

    #         pdf.setFont("Helvetica", 10)
    #         package = f"Customer: {self.partner_id.name} | Type: {self.member_type}"
    #         pdf.drawString((width - pdf.stringWidth(package, "Helvetica", 10)) / 2, height - 55, package)

    #         pdf.setFont("Helvetica", 8)
    #         tagline_y = height - logo_height - 15
    #         pdf.drawRightString(width - margin, tagline_y, "We guarantee to get you moving...")

    #     def draw_table_header(y_position):
    #         x_offset = margin
    #         pdf.setFont("Helvetica-Bold", 8)
    #         for i, header in enumerate(headers):
    #             pdf.rect(x_offset, y_position - header_height, col_widths[i], header_height)
    #             for j, line in enumerate(header.split('\n')):
    #                 text_width = pdf.stringWidth(line, "Helvetica-Bold", 8)
    #                 x_text = x_offset + (col_widths[i] - text_width) / 2
    #                 y_text = y_position - 15 - (j * 10)
    #                 pdf.drawString(x_text, y_text, line)
    #             x_offset += col_widths[i]
    #         return y_position - header_height

    #     def draw_data_row(data, y_position):
    #         x_offset = margin
    #         pdf.setFont("Helvetica", 7)
    #         line_height = 8

    #         def wrap_text(text, width):
    #             text = str(text) if text else ''
    #             max_chars = int(width / 5.5)
    #             return textwrap.wrap(text, max_chars)

    #         max_lines = 1
    #         column_lines = []
    #         for i, value in enumerate(data.values()):
    #             wrapped = wrap_text(value, col_widths[i])
    #             column_lines.append(wrapped)
    #             max_lines = max(max_lines, len(wrapped))

    #         adjusted_row_height = row_height * max_lines
    #         for i, lines in enumerate(column_lines):
    #             pdf.rect(x_offset, y_position - adjusted_row_height, col_widths[i], adjusted_row_height)
    #             start_y = y_position - line_height
    #             for line in lines:
    #                 pdf.drawString(x_offset + 5, start_y, line)
    #                 start_y -= line_height
    #             x_offset += col_widths[i]
    #         return y_position - adjusted_row_height
        
    #     def collect_and_print_data():
    #         data_list = []

    #         product_ids = self.invoice_line_ids.mapped('product_id.product_tmpl_id.id')

    #         # Map product_template_id to price_unit
    #         product_price_map = {
    #             line.product_id.product_tmpl_id.id: line.price_unit
    #             for line in self.invoice_line_ids
    #         }

    #         # Partner domain
    #         partner_domain = [
    #             ('product_template_id', 'in', product_ids),
    #             ('member_type', '=', self.member_type),
    #             ('member_partner_category_id', '=', self.category_id.id),
    #             ('parent_customer_id', '=', self.partner_id.id),
    #             ('membership_state', '=', 'confirm'),
    #             ('invoice_ref_date', '>=', self.from_date),
    #             ('invoice_ref_date', '<=', self.to_date),
    #         ]

    #         # History domain
    #         history_domain = [
    #             ('product_template_id', 'in', product_ids),
    #             ('member_type', '=', self.member_type),
    #             ('member_partner_category_id', '=', self.category_id.id),
    #             ('parent_customer_id', '=', self.partner_id.id),
    #             ('invoice_ref_date', '>=', self.from_date),
    #             ('invoice_ref_date', '<=', self.to_date),
    #         ]

    #         partners = self.env['res.partner'].search(partner_domain)
    #         histories = self.env['membership.history'].search(history_domain)

    #         for record in list(partners) + list(histories):
    #             product_id = record.product_template_id.id
    #             amount = product_price_map.get(product_id, 0.0)

    #             data_list.append({
    #                 'membership_no': record.old_membership_number or record.ref_num or '',
    #                 'name': record.name or '',
    #                 'customer': record.parent_customer_id.name or '',
    #                 'plate_no': record.vehicle_plate or '',
    #                 'chasis_no': record.vehicle_chasis_no or '',
    #                 'policy_no': record.policy_no or '',
    #                 'start_date': record.member_activate_date.strftime('%d-%m-%Y') if record.member_activate_date else '',
    #                 'expiry_date': record.member_expiry_date.strftime('%d-%m-%Y') if record.member_expiry_date else '',
    #                 'car_make': record.vehicle_type or '',
    #                 'amount': f"{amount:.2f}",
    #             })

    #         draw_header()
    #         y = draw_table_header(height - 120)

    #         for row in data_list:
    #             y = draw_data_row(row, y)
    #             if y < 50:
    #                 pdf.showPage()
    #                 draw_header()
    #                 y = draw_table_header(height - 120)


    #     # def collect_and_print_data():
    #     #     data_list = []

    #     #     product_ids = self.invoice_line_ids.mapped('product_id.product_tmpl_id.id')

    #     #     # Domain for res.partner
    #     #     partner_domain = [
    #     #         ('product_template_id', 'in', product_ids),
    #     #         ('member_type', '=', self.member_type),
    #     #         ('member_partner_category_id', '=', self.category_id.id),
    #     #         ('parent_customer_id', '=', self.partner_id.id),
    #     #         ('membership_state', '=', 'confirm'),
    #     #         ('invoice_ref_date', '>=', self.from_date),
    #     #         ('invoice_ref_date', '<=', self.to_date),
    #     #     ]

    #     #     # Domain for membership.history (remove 'membership_state')
    #     #     history_domain = [
    #     #         ('product_template_id', 'in', product_ids),
    #     #         ('member_type', '=', self.member_type),
    #     #         ('member_partner_category_id', '=', self.category_id.id),
    #     #         ('parent_customer_id', '=', self.partner_id.id),
    #     #         ('invoice_ref_date', '>=', self.from_date),
    #     #         ('invoice_ref_date', '<=', self.to_date),
    #     #     ]

    #     #     partners = self.env['res.partner'].search(partner_domain)
    #     #     histories = self.env['membership.history'].search(history_domain)

    #     #     for partner in partners:
    #     #         data_list.append({
    #     #             'membership_no': partner.old_membership_number or partner.ref_num or '',
    #     #             'name': partner.name or '',
    #     #             'customer': partner.parent_customer_id.name or '',
    #     #             'plate_no': partner.vehicle_plate or '',
    #     #             'chasis_no': partner.vehicle_chasis_no or '',
    #     #             'policy_no': partner.policy_no or '',
    #     #             'start_date': partner.member_activate_date.strftime('%d-%m-%Y') if partner.member_activate_date else '',
    #     #             'expiry_date': partner.member_expiry_date.strftime('%d-%m-%Y') if partner.member_expiry_date else '',
    #     #             'car_make': partner.vehicle_type or '',
    #     #             'amount': self._calculate_amount(partner),
    #     #         })

    #     #     for history in histories:
    #     #         data_list.append({
    #     #             'membership_no': history.old_membership_number or history.ref_num or '',
    #     #             'name': history.name or '',
    #     #             'customer': history.parent_customer_id.name or '',
    #     #             'plate_no': history.vehicle_plate or '',
    #     #             'chasis_no': history.vehicle_chasis_no or '',
    #     #             'policy_no': history.policy_no or '',
    #     #             'start_date': history.member_activate_date.strftime('%d-%m-%Y') if history.member_activate_date else '',
    #     #             'expiry_date': history.member_expiry_date.strftime('%d-%m-%Y') if history.member_expiry_date else '',
    #     #             'car_make': history.vehicle_type or '',
    #     #             'amount': self._calculate_amount(history),
    #     #         })

    #     #     draw_header()
    #     #     y = draw_table_header(height - 120)

    #     #     for row in data_list:
    #     #         y = draw_data_row(row, y)
    #     #         if y < 50:
    #     #             pdf.showPage()
    #     #             draw_header()
    #     #             y = draw_table_header(height - 120)

    #     collect_and_print_data()
    #     pdf.save()
    #     buffer.seek(0)

    #     attachment = self.env['ir.attachment'].create({
    #         'name': f"Invoice_Members_Report_{self.id}.pdf",
    #         'datas': base64.b64encode(buffer.read()),
    #         'type': 'binary',
    #     })

    #     return {
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'ir.attachment',
    #         'res_id': attachment.id,
    #         'view_mode': 'form',
    #         'target': 'new',
    #     }



    





# from odoo import models, fields, api
# from itertools import chain

# class AccountMove(models.Model):
#     _inherit = 'account.move'

#     member_type = fields.Selection([ ('policy', 'Policy Member'),
#                                     ('credit', 'Credit Member') ], string='Member Type')
#     category_id = fields.Many2one('partner.category', 
#                                   string="Customer Category",
#                                   domain="[('partner_id','=', partner_id),('member_type','=',member_type)]")

#     from_date = fields.Date(string="From Date")
#     to_date = fields.Date(string="To Date")


#     @api.onchange('member_type', 'partner_id')
#     def _onchange_member_type(self):
#         if self.member_type and self.partner_id:
#             domain = [
#                 ('partner_id', '=', self.partner_id.id),
#                 ('member_type', '=', self.member_type)
#             ]
#             first_category = self.env['partner.category'].search(domain, limit=1)
#             self.category_id = first_category.id if first_category else False


#     def compute_services_based_on_date(self):

#         for record in self:
#             if not record.from_date or not record.to_date or not record.partner_id or not record.category_id:
#                 continue

#             if record.member_type == "credit":

#                 all_services = self.env["aaa.service"].search(
#                     [("customer_id", "=", record.partner_id.id),("sequence_id","=",record.category_id.id),("state","=","done")] 
#                 )
#                 invoice_lines = []
#                 product_quantity = {}

#                 record.invoice_line_ids = [(5, 0, 0)]

#                 for service in all_services:
#                     if record.from_date <= service.service_time.date() <= record.to_date:
#                         product_id = service.product_id.id

#                         if product_id in product_quantity:
#                             product_quantity[product_id]["quantity"] += 1

#                         else:
#                             product_quantity[product_id] = {
#                                 "product_id": product_id,
#                                 "price_unit": service.product_id.price_unit,
#                                 "quantity": 1,
#                                 "name": service.product_id.name,
#                             }

#                 invoice_lines = [(0, 0, values)
#                                     for values in product_quantity.values()]
#                 print(invoice_lines)

#                 record.write({"invoice_line_ids":invoice_lines})


#             elif record.member_type == "policy":

#                 domain = [('invoice_ref_date', '>=', record.from_date), 
#                           ('invoice_ref_date', '<=', record.to_date),
#                           ("parent_customer_id", "=", record.partner_id.id),
#                           ('member_partner_category_id', '=', record.category_id.id),
#                           ('member_type', '=', record.member_type),]
                
#                 partner_domain = domain + [('membership_state', '=', 'confirm')]

#                 partner_records = self.env['res.partner'].search(partner_domain)
#                 history_records = self.env['membership.history'].search(domain)

#                 all_records = chain(partner_records, history_records)

#                 invoice_lines = []
#                 product_quantity = {}

#                 record.invoice_line_ids = [(5, 0, 0)]

#                 for rec in all_records:
#                     product_id = rec.product_template_id.id

#                     if product_id in product_quantity:
#                             product_quantity[product_id]["quantity"] += 1

#                     else:
#                         product_quantity[product_id] = {
#                             "product_id": product_id,
#                             "price_unit": rec.product_template_id.price_unit,
#                             "quantity": 1,
#                             "name": rec.product_template_id.name,
#                         }

#                 invoice_lines = [(0, 0, values)
#                                     for values in product_quantity.values()]
#                 print(invoice_lines)

#                 record.write({"invoice_line_ids":invoice_lines})

#     def action_report_invoice(self):
#         #pass
        
