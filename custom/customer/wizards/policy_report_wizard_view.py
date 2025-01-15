from odoo import models, fields, api
import datetime
from datetime import timedelta
#from pytz import timezone, utc
import pytz
import io
import xlsxwriter
import base64
from reportlab.lib.pagesizes import A4, portrait
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import BytesIO
from reportlab.lib.utils import ImageReader  # Import ImageReader
from datetime import datetime, time, timedelta

import logging
# Set up logging for debugging purposes
_logger = logging.getLogger(__name__)

class PolicyReportWizard(models.TransientModel):
    _name = 'policy.report.wizard'
    _description = 'Policy Report Wizard'

    
   

    from_date = fields.Datetime(
        string="From Date",
        required=True,
        default=lambda self: self._get_start_of_day()
    )

    to_date = fields.Datetime(
        string="To Date",
        required=True,
        default=lambda self: self._get_end_of_day()
    )
  

    # def _get_start_of_day(self):
    #     # Get the user's timezone or default to UTC
    #     user_tz = pytz.timezone(self.env.user.tz or 'UTC')
        
    #     # Get today's date in the user's timezone at midnight
    #     today = datetime.now(user_tz).date()
    #     midnight_user_tz = user_tz.localize(datetime.combine(today, time(0, 0, 0)))
        
    #     # Convert to UTC without shifting the date
    #     midnight_utc = midnight_user_tz.astimezone(pytz.utc)
        
    #     # Return as naive datetime for Odoo compatibility
    #     return midnight_utc.replace(tzinfo=None)

    def _get_start_of_day(self):
        # Ensure midnight is calculated directly in UTC without shifting the date
        utc_now = datetime.now(pytz.utc).date()  # Get today's date directly in UTC
        midnight_utc = datetime.combine(utc_now, time(0, 0, 0))  # Midnight in UTC
        return midnight_utc  # No need for timezone adjustments, already UTC-based


    def _get_end_of_day(self):
        # Get the user's timezone or default to UTC
        user_tz = pytz.timezone(self.env.user.tz or 'UTC')
        
        # Get today's date in the user's timezone at 23:59:59
        today = datetime.now(user_tz).date()
        end_of_day_user_tz = user_tz.localize(datetime.combine(today, time(23, 59, 59)))
        
        # Convert to UTC without shifting the date
        end_of_day_utc = end_of_day_user_tz.astimezone(pytz.utc)
        
        # Return as naive datetime for Odoo compatibility
        return end_of_day_utc.replace(tzinfo=None)
  
    


    product_template_id = fields.Many2one('product.template', string="Package", domain="[('bundle_product', '=', True)]")
    customer_id = fields.Many2one('res.partner', string="Customer", domain="[('is_company', '=', True)]")
    member_type = fields.Selection([('policy', 'POLICY'), ('credit', 'CREDIT'),('adhoc','AD-HOC')], string="Member Type")
    sequence_id = fields.Many2one('partner.category', string="Customer Category",
    domain="[('partner_id','=', customer_id), ('member_type', '=', member_type)]")
    type = fields.Selection([('cash', 'Cash'), ('non_cash', 'Non-Cash')], string="Service Type")

    
    def _calculate_amount(self, record):
        """Calculate the amount for a membership record."""
        amount = 0.0
        if record.member_type == 'credit':
            if record.from_location and record.to_location and record.product_id:
                service_rate = self.env['service.rate'].search([
                    ('product_pricelist_item_id.product_tmpl_id', '=', record.product_id.id),
                    ('from_loc_id', '=', record.from_location.id),
                    ('to_loc_id', '=', record.to_location.id)
                ], limit=1)
                amount = service_rate.price if service_rate else 0.0
        elif record.member_type == 'policy':
            if record.name and record.product_template_id:
                pricelist_item = self.env['product.pricelist.item'].search([
                    ('product_tmpl_id', '=', record.product_template_id.id)
                ], limit=1)
                amount = pricelist_item.fixed_price if pricelist_item else 0.0
        return f"{float(amount or 0):.2f}"
    

    def collect_data(self, domain, model):
        records = self.env[model].search(domain)
        data_list = []
        for record in records:
            data_list.append({
                'membership_no': getattr(record, 'old_membership_number', None) or '',
                'name': record.name or '',
                'customer': record.parent_customer_id.name if record.parent_customer_id else '',
                'plate_no': record.vehicle_plate or '',
                'chasis_no': record.vehicle_chasis_no or '',
                'policy_no': record.policy_no or '',
                'start_date': record.member_activate_date.strftime('%d-%m-%Y') if record.member_activate_date else '',
                'expiry_date': record.member_expiry_date.strftime('%d-%m-%Y') if record.member_expiry_date else '',
                'car_make': record.vehicle_type or '',
                'package': record.product_template_id.name if hasattr(record, 'product_template_id') and record.product_template_id else '',
                'amount': self._calculate_amount(record),
            })
        return data_list
   

   

    

    def action_print_pdf(self):
        """Generate Membership Details PDF with renewals and extensions."""
        import textwrap
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        from reportlab.lib.units import inch
        import io
        import base64

        # Initialize PDF
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
        width, height = landscape(A4)
        margin = 20

        # Company logo setup
        company = self.env['res.company'].search([], limit=1)
        logo_width, logo_height = 1.2 * inch, 1.2 * inch

        # Define headers and column widths
        headers = [
            'MEMBERSHIP\nNO.', 'NAME', 'CUSTOMER', 'PLATE\nNO.', 'CHASIS\nNO.', 'POLICY\nNO.',
            'START\nDATE', 'EXPIRY\nDATE', 'CAR\nMAKE', 'AMOUNT'
        ]
        col_widths = [65, 115, 115, 65, 95, 85, 65, 65, 75, 60]
        header_height = 40
        row_height = 30

        # Function to draw headers and data rows
        def draw_header(pdf):
            """Draw the header with logo, title, and filters."""
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
            title = "Membership Details"
            pdf.drawString((width - pdf.stringWidth(title, "Helvetica-Bold", 12)) / 2, height - 40, title)

            pdf.setFont("Helvetica", 10)
            date_range = f"From: {self.from_date.strftime('%d-%m-%Y')} To: {self.to_date.strftime('%d-%m-%Y')}"
            pdf.drawString((width - pdf.stringWidth(date_range, "Helvetica", 10)) / 2, height - 55, date_range)

            if self.customer_id:
                customer_name = f"Customer: {self.customer_id.name}"
                pdf.drawString((width - pdf.stringWidth(customer_name, "Helvetica", 10)) / 2, height - 70, customer_name)

            pdf.setFont("Helvetica", 8)
            tagline_y_position = height - logo_height - 15
            pdf.drawRightString(width - margin, tagline_y_position, "We guarantee to get you moving...")

        def draw_table_header(pdf, y_position):
            """Draw table headers."""
            x_offset = margin
            pdf.setFont("Helvetica-Bold", 8)
            for i, header in enumerate(headers):
                pdf.rect(x_offset, y_position - header_height, col_widths[i], header_height)
                text_lines = header.split('\n')
                starting_y = y_position - (header_height / 2) + (len(text_lines) * 5)
                for line in text_lines:
                    text_width = pdf.stringWidth(line, "Helvetica-Bold", 8)
                    x_text = x_offset + (col_widths[i] - text_width) / 2
                    pdf.drawString(x_text, starting_y, line)
                    starting_y -= 10
                x_offset += col_widths[i]
            return y_position - header_height

        def draw_data_row(pdf, data, y_position):
            """Draw each row with wrapped text and proper alignment."""
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

        # Collect data for each specific period based on user's interest
        def collect_and_print_data(from_date, to_date, is_renewal=False):
            domain = [('parent_customer_id', '=', self.customer_id.id),
                    #('product_template_id', '>=', self.product_template_id.id),
                    ('member_type', '=', 'policy'),
                    ('member_partner_category_id', '=', self.sequence_id.id),
                    ('invoice_ref_date', '>=', from_date),
                    ('invoice_ref_date', '<=', to_date)]

            if is_renewal:
                records = self.env['membership.history'].search(domain)
            else:
                records = self.env['res.partner'].search(domain)

            data_list = []
            for record in records:
                data_list.append({
                    'membership_no': record.old_membership_number or '',
                    'name': record.name or '',
                    'customer': record.parent_customer_id.name or '',
                    'plate_no': record.vehicle_plate or '',
                    'chasis_no': record.vehicle_chasis_no or '',
                    'policy_no': record.policy_no or '',
                    'start_date': record.member_activate_date.strftime('%d-%m-%Y') if record.member_activate_date else '',
                    'expiry_date': record.member_expiry_date.strftime('%d-%m-%Y') if record.member_expiry_date else '',
                    'car_make': record.vehicle_type or '',
                    'amount': self._calculate_amount(record),
                })

            # Generate PDF content for the collected data
            draw_header(pdf)
            y_position = draw_table_header(pdf, height - 120)
            for row_data in data_list:
                y_position = draw_data_row(pdf, row_data, y_position)
                if y_position < 50:  # Check if we need a new page
                    pdf.showPage()
                    y_position = draw_table_header(pdf, height - 120)

        # Generate PDF for initial memberships and renewals separately
        collect_and_print_data(self.from_date, self.to_date)  # Initial memberships
        collect_and_print_data(self.from_date, self.to_date, is_renewal=True)  # Renewals

        pdf.save()
        buffer.seek(0)

        # Attach PDF
        attachment = self.env['ir.attachment'].create({
            'name': f"Membership Details_{self.id}.pdf",
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


    
    # def action_export_excel(self):
    #     import xlsxwriter
    #     import io
    #     import base64
    
    #     # Prepare domain filters for policy members within the specified date range
    #     domain = []
    #     if self.customer_id:
    #         domain.append(('parent_customer_id', '=', self.customer_id.id))
    #     if self.member_type == 'policy':
    #         domain.append(('member_type', '=', 'policy'))
    #     if self.sequence_id:
    #         domain.append(('member_partner_category_id', '=', self.sequence_id.id))
    #     if self.from_date:
    #         domain.append(('invoice_ref_date', '>=', self.from_date))
    #     if self.to_date:
    #         domain.append(('invoice_ref_date', '<=', self.to_date))

    #     service_records = self.env['res.partner'].search(domain)

    #     # Collect data for the Excel
    #     all_data = []
    #     for record in service_records:
    #         all_data.append({
    #             #'membership_no': record.old_membership_number or '',
    #             'membership_no': record.ref_num or '',
    #             'name': record.name or '',
    #             'customer': record.parent_customer_id.name or '',
    #             'plate_no': record.vehicle_plate or '',
    #             'chasis_no': record.vehicle_chasis_no or '',
    #             'policy_no': record.policy_no or '',
    #             'start_date': record.member_activate_date.strftime('%d-%m-%Y') if record.member_activate_date else '',
    #             'expiry_date': record.member_expiry_date.strftime('%d-%m-%Y') if record.member_expiry_date else '',
    #             'car_make': record.vehicle_type or '',
    #             'product_template_id': record.product_template_id.name,
    #             'amount': self._calculate_amount(record),
    #         })
        

    #     # Initialize Excel file
    #     output = io.BytesIO()
    #     workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    #     worksheet = workbook.add_worksheet()

    #     # Define main header and sub-header
    #     main_header = "MEMBERSHIP STATEMENT"
    #     sub_header1 = f"Customer: {self.customer_id.name}" if self.customer_id else "All Customers"
    #     sub_header2 = f"Date Range: {self.from_date.strftime('%d-%m-%Y')} to {self.to_date.strftime('%d-%m-%Y')}" if self.from_date and self.to_date else "Full Period"

    #     # Write main header and sub-headers
    #     main_header_format = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 16})
    #     sub_header_format = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 12})
        
    #     worksheet.merge_range('A1:K1', main_header, main_header_format)
    #     worksheet.merge_range('A2:K2', sub_header1, sub_header_format)
    #     worksheet.merge_range('A3:K3', sub_header2, sub_header_format)

    #     # Define headers for data
    #     headers = [
    #         'MEMBERSHIP NO.', 'NAME', 'CUSTOMER', 'PLATE NO.', 'CHASIS NO.', 'POLICY NO.',
    #         'START DATE', 'EXPIRY DATE', 'CAR MAKE', 'PACKAGE', 'AMOUNT'
    #     ]

    #     # Write header
    #     header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
    #     start_row = 3  # Adjust start row for data headers and rows
    #     for col, header in enumerate(headers):
    #         worksheet.write(start_row, col, header, header_format)

    #     # Write data rows
    #     row = start_row + 1  # Adjust start row for data
    #     for data in all_data:
    #         for col, key in enumerate(data):
    #             worksheet.write(row, col, data[key])
    #         row += 1

    #     workbook.close()

    #     # Convert the bytes data to a base64 encoded string
    #     excel_data = base64.b64encode(output.getvalue())
    #     output.close()

    #     # Create an attachment
    #     attachment = self.env['ir.attachment'].create({
    #         'name': f"Membership Details_{self.id}.xlsx",
    #         'datas': excel_data,
    #         'type': 'binary',
    #     })

    #     return {
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'ir.attachment',
    #         'res_id': attachment.id,
    #         'view_mode': 'form',
    #         'target': 'new',
    #     }

    def action_export_excel(self):
        import xlsxwriter
        import io
        import base64

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        # Headers and formats setup
        main_header = "MEMBERSHIP STATEMENT"
        sub_header1 = f"Customer: {self.customer_id.name}" if self.customer_id else "All Customers"
        sub_header2 = f"Date Range: {self.from_date.strftime('%d-%m-%Y')} to {self.to_date.strftime('%d-%m-%Y')}" if self.from_date and self.to_date else "Full Period"

        main_header_format = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 16})
        sub_header_format = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 12})

        worksheet.merge_range('A1:K1', main_header, main_header_format)
        worksheet.merge_range('A2:K2', sub_header1, sub_header_format)
        worksheet.merge_range('A3:K3', sub_header2, sub_header_format)

        headers = [
            'MEMBERSHIP NO.', 'NAME', 'CUSTOMER', 'PLATE NO.', 'CHASIS NO.', 'POLICY NO.',
            'START DATE', 'EXPIRY DATE', 'CAR MAKE', 'PACKAGE', 'AMOUNT'
        ]
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1})
        for col, header in enumerate(headers):
            clean_key = header.lower().replace(' ', '_').strip('.')
            worksheet.write(4, col, header, header_format)
            headers[col] = clean_key  # Update headers list with clean keys for later use

        # Data fetching and writing
        domain = [
            ('parent_customer_id', '=', self.customer_id.id),
            ('member_type', '=', 'policy'),
            ('member_partner_category_id', '=', self.sequence_id.id),
            ('invoice_ref_date', '>=', self.from_date),
            ('invoice_ref_date', '<=', self.to_date)
        ]
        partner_data = self.collect_data(domain, 'res.partner')
        history_data = self.collect_data(domain, 'membership.history')
        all_data = partner_data + history_data

        row = 5
        for data in all_data:
            for col, key in enumerate(headers):
                worksheet.write(row, col, data[key])
            row += 1

        workbook.close()
        excel_data = base64.b64encode(output.getvalue())
        output.close()

        attachment = self.env['ir.attachment'].create({
            'name': f"Membership Details_{self.id}.xlsx",
            'datas': excel_data,
            'type': 'binary',
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'res_id': attachment.id,
            'view_mode': 'form',
            'target': 'new',
        }








