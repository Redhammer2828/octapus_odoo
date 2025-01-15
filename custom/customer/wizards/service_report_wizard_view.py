from odoo import models, fields, api
import datetime
from datetime import timedelta
#from pytz import timezone, utc
import pytz
import io
import xlsxwriter
import base64
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import BytesIO
from reportlab.lib.utils import ImageReader  # Import ImageReader
from datetime import datetime, time, timedelta

import logging
# Set up logging for debugging purposes
_logger = logging.getLogger(__name__)

class ServiceReportWizard(models.TransientModel):
    _name = 'service.report.wizard'
    _description = 'Service Report Wizard'

    # from_date = fields.Datetime(string="From Date", required=True)
    # to_date = fields.Datetime(string="To Date", required=True)
   

    # from_date = fields.Datetime(
    #     string="From Date",
    #     required=True,
    #     default=lambda self: self._get_datetime_with_midnight()
    # )

    # to_date = fields.Datetime(
    #     string="To Date",
    #     required=True,
    #     default=lambda self: self._get_datetime_with_midnight()
    # )

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

    # def _get_datetime_with_midnight(self):
    #     # Get today's date in the user's time zone
    #     user_tz = timezone(self.env.user.tz or 'UTC')  # Default to UTC if no timezone is set
    #     today_date = datetime.now(user_tz).date()  # Get today's date in user's time zone
        
    #     # Combine today's date with midnight time (00:05:00)
    #     midnight = datetime.combine(today_date, time(0, 5, 0))

    #     # Localize this time to the user's time zone and then convert to naive datetime
    #     midnight_user_tz = user_tz.localize(midnight)
    #     naive_midnight = midnight_user_tz.astimezone(timezone('UTC')).replace(tzinfo=None)

    #     return naive_midnight

    # def _get_datetime_with_midnight(self):
    #     # Get the user's timezone or default to UTC if none is set
    #     user_tz = pytz.timezone(self.env.user.tz or 'UTC')
        
    #     # Get the current date in the user's timezone
    #     now_in_user_tz = datetime.now(user_tz)
    #     today_date_in_user_tz = now_in_user_tz.date()
        
    #     # Create a datetime object for 00:05:00 on today's date in the user's timezone
    #     midnight_time_in_user_tz = datetime.combine(today_date_in_user_tz, time(0, 5))
    #     midnight_time_in_user_tz = user_tz.localize(midnight_time_in_user_tz, is_dst=None)
        
    #     # Convert this time to UTC
    #     utc_midnight_time = midnight_time_in_user_tz.astimezone(pytz.utc)

    #     # Check if the conversion has altered the day (if it went back a day, adjust it)
    #     if utc_midnight_time.date() < midnight_time_in_user_tz.date():
    #         # If the UTC time is behind and causes the date to shift back, add one day
    #         utc_midnight_time += timedelta(days=1)

    #     return utc_midnight_time.replace(tzinfo=None)  # Strip timezone information

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
  
    


    
    customer_id = fields.Many2one('res.partner', string="Customer", domain="[('is_company', '=', True)]")
    member_type = fields.Selection([('policy', 'POLICY'), ('credit', 'CREDIT'),('adhoc','AD-HOC')], string="Member Type")
    sequence_id = fields.Many2one('partner.category', string="Customer Category",
    domain="[('partner_id','=', customer_id), ('member_type', '=', member_type)]")
    type = fields.Selection([('cash', 'Cash'), ('non_cash', 'Non-Cash')], string="Service Type")

    def _fetch_service_records(self):
        """Fetches service records based on the wizard's filter criteria."""
        domain = []
        if self.customer_id:
            domain.append(('customer_id', '=', self.customer_id.id))
        if self.member_type:
            domain.append(('member_type', '=', self.member_type))
        if self.type:
            domain.append(('type', '=', self.type))
        if self.sequence_id:
            domain.append(('sequence_id', '=', self.sequence_id.id))

        # Filter by Service Time (Date Range)
        domain.append(('service_time', '>=', self.from_date))
        domain.append(('service_time', '<=', self.to_date))

        service_records = self.env['aaa.service'].search(domain)
        _logger.debug("Fetched %d records from the aaa.service model", len(service_records))
        return service_records
    
    def _calculate_amount(self, record):
        """Calculate the amount for a membership record."""
        amount = 0.0
        if record.member_type == 'credit':
            if record.from_location and record.to_location and record.product_id and record.customer_id:
                pricelist_id = record.customer_id.property_product_pricelist
                print("PRICELIST ID",pricelist_id)
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
   

   

    # def action_print_pdf(self):
    #     """Generate Membership Details PDF with renewals and extensions."""
    #     import textwrap
    #     from reportlab.lib.pagesizes import landscape, A4
    #     from reportlab.pdfgen import canvas
    #     from reportlab.lib.utils import ImageReader
    #     from reportlab.lib.units import inch
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

    #     # Collect data for the PDF
    #     all_data = []
    #     for record in service_records:
    #         all_data.append({
    #             'membership_no': record.old_membership_number or '',
    #             'name': record.name or '',
    #             'customer': record.parent_customer_id.name or '',
    #             'plate_no': record.vehicle_plate or '',
    #             'chasis_no': record.vehicle_chasis_no or '',
    #             'policy_no': record.policy_no or '',
    #             'start_date': record.member_activate_date.strftime('%d-%m-%Y') if record.member_activate_date else '',
    #             'expiry_date': record.member_expiry_date.strftime('%d-%m-%Y') if record.member_expiry_date else '',
    #             'car_make': record.vehicle_type or '',
    #             'amount': self._calculate_amount(record),
    #         })

    #         # Include renewals/extensions from membership history
    #         history_records = self.env['membership.history'].search([('history_id', '=', record.id)])
    #         for history in history_records:
    #             expiry_diff = (record.member_expiry_date - history.member_expiry_date).days
    #             if expiry_diff >= 365:
    #                 renewal_type = "Renewal"
    #             elif expiry_diff < 365:
    #                 renewal_type = "Extension"
    #             else:
    #                 continue

    #             all_data.append({
    #                 'membership_no': f"{record.old_membership_number} ({renewal_type})",
    #                 'name': record.name or '',
    #                 'customer': record.parent_customer_id.name or '',
    #                 'plate_no': record.vehicle_plate or '',
    #                 'chasis_no': record.vehicle_chasis_no or '',
    #                 'policy_no': record.policy_no or '',
    #                 'start_date': history.member_expiry_date.strftime('%d-%m-%Y') if history.member_expiry_date else '',
    #                 'expiry_date': record.member_expiry_date.strftime('%d-%m-%Y') if record.member_expiry_date else '',
    #                 'car_make': record.vehicle_type or '',
    #                 'amount': self._calculate_amount(record),
    #             })

        

    #     # Initialize PDF
    #     buffer = io.BytesIO()
    #     pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    #     width, height = landscape(A4)
    #     margin = 20
    #     table_y_start = height - 120

    #     # Company logo setup
    #     company = self.env['res.company'].search([], limit=1)
    #     logo_width, logo_height = 1.2 * inch, 1.2 * inch

    #     # Define headers and column widths
    #     headers = [
    #         'MEMBERSHIP\nNO.', 'NAME', 'CUSTOMER', 'PLATE\nNO.', 'CHASIS\nNO.', 'POLICY\nNO.',
    #         'START\nDATE', 'EXPIRY\nDATE', 'CAR\nMAKE', 'AMOUNT'
    #     ]
       
    #     col_widths = [65, 115, 115, 65, 95, 85, 65, 65, 75, 60]
    #     header_height = 40
    #     row_height = 30

    #     def draw_header(pdf):
    #         """Draw the header with logo, title, and filters."""
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
    #         title = "Membership Details"
    #         pdf.drawString((width - pdf.stringWidth(title, "Helvetica-Bold", 12)) / 2, height - 40, title)

    #         pdf.setFont("Helvetica", 10)
    #         date_range = f"From: {self.from_date.strftime('%d-%m-%Y')} To: {self.to_date.strftime('%d-%m-%Y')}"
    #         pdf.drawString((width - pdf.stringWidth(date_range, "Helvetica", 10)) / 2, height - 55, date_range)

    #         if self.customer_id:
    #             customer_name = f"Customer: {self.customer_id.name}"
    #             pdf.drawString((width - pdf.stringWidth(customer_name, "Helvetica", 10)) / 2, height - 70, customer_name)

    #         pdf.setFont("Helvetica", 8)
    #         tagline_y_position = height - logo_height - 15
    #         pdf.drawRightString(width - margin, tagline_y_position, "We guarantee to get you moving...")

    #     def draw_table_header(pdf, y_position):
    #         """Draw table headers."""
    #         x_offset = margin
    #         pdf.setFont("Helvetica-Bold", 8)
    #         for i, header in enumerate(headers):
    #             pdf.rect(x_offset, y_position - header_height, col_widths[i], header_height)
    #             text_lines = header.split('\n')
    #             starting_y = y_position - (header_height / 2) + (len(text_lines) * 5)
    #             for line in text_lines:
    #                 text_width = pdf.stringWidth(line, "Helvetica-Bold", 8)
    #                 x_text = x_offset + (col_widths[i] - text_width) / 2
    #                 pdf.drawString(x_text, starting_y, line)
    #                 starting_y -= 10
    #             x_offset += col_widths[i]
    #         return y_position - header_height

    #     def draw_data_row(pdf, data, y_position):
    #         """Draw each row with wrapped text and proper alignment."""
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

        

        

    #     # Generate PDF content
    #     draw_header(pdf)
    #     y_position = draw_table_header(pdf, table_y_start)
    #     for row_data in all_data:
    #         if y_position < 50:
    #             pdf.showPage()
    #             draw_header(pdf)
    #             y_position = draw_table_header(pdf, table_y_start)
    #         y_position = draw_data_row(pdf, row_data, y_position)

    #     pdf.save()
    #     buffer.seek(0)

    #     # Attach PDF
    #     attachment = self.env['ir.attachment'].create({
    #         'name': f"Membership Details_{self.id}.pdf",
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


    


    

   




# Note: Ensure the helper functions `draw_header`, `draw_table_header`, and `draw_data_row` are complete and available within your implementation.







    def action_export_excel(self):
        # Initialize buffer for Excel generation
        buffer = io.BytesIO()
        service_records = self._fetch_service_records()

        # If no records found, log warning and still generate an empty sheet
        if not service_records:
            _logger.warning("No records found for the specified filter criteria.")

        # Prepare Excel export
        workbook = xlsxwriter.Workbook(buffer)
        worksheet = workbook.add_worksheet('Proforma Statement')

        # Define the header formats
        bold_format = workbook.add_format({
            'bold': True,
            'align': 'left',
            'valign': 'vcenter',
            'bg_color': '#00007A',
            'color': 'white'
        })

        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#00007A',
            'color': 'white'
        })

        total_format = workbook.add_format({
            'bold': True,
            'align': 'right',
            'valign': 'vcenter',
            'color': 'black'
        })

        # Merge cells for the main title
        worksheet.merge_range('A1:D1', 'SERVICE STATEMENT', bold_format)

        # Merge cells for "Date Range", "Customer", and "Category"
        worksheet.merge_range('A2:B2', 'Date Range', header_format)
        worksheet.merge_range('C2:D2', 'Customer', header_format)
        worksheet.merge_range('E2:F2', 'Category', header_format)
        worksheet.merge_range('E3:F3', '', header_format)

        # Get formatted date range
        date_range = f"{self.from_date.strftime('%d/%m/%Y')}-{self.to_date.strftime('%d/%m/%Y')}"
        customer_name = self.customer_id.name if self.customer_id else ''

        # Write date range and customer details
        worksheet.merge_range('A3:B3', date_range, header_format)
        worksheet.merge_range('C3:D3', customer_name, header_format)

        # Define the main headers conditionally
        headers = [
            'Service Date', 'Service Number', 'Customer C/O',
            # Include 'Type' and 'Customer category' only if customer_id is "AL MASAOOD AUTOMOBILES COMPANY LLC"
            *(['Customer Category'] if self.customer_id and self.customer_id.name == 'AL MASAOOD AUTOMOBILES COMPANY LLC' else []),
            *(['Type'] if self.customer_id and self.customer_id.name == 'AL MASAOOD AUTOMOBILES COMPANY LLC' else []),
           
            'Vehicle Type', 'Vehicle Model', 'Vehicle Plate', 'Chassis No', 'Service',
            'From Location', 'To Location', 'Trip Sheet No.', 'Quantity', 'Rate', 'Amount',
            'VAT(5%)', 'Total'
        ]

        # Write main headers
        for col_num, header in enumerate(headers):
            worksheet.write(7, col_num, header, header_format)

        # Adjust column widths based on headers
        column_widths = [len(header) + 2 for header in headers]

        # If no records, still generate the Excel with headers and empty data
        if not service_records:
            worksheet.write(8, 0, 'No data available', bold_format)
            for col_num, width in enumerate(column_widths):
                worksheet.set_column(col_num, col_num, width)
        else:
            row = 8
           


           # Initialize totals
            total_service_amount_sum = 0
            total_vat_sum = 0
            total_sum = 0
            total_service_quantity = 0  # Track total quantity
            total_rate_sum = 0  # Track total rate

            for record in service_records:
                # Initialize variables
                rate = 0.00
                amount = 0.00
                vat = 0.00
                total = 0.00
                quantity = 0.00  # Ensure quantity is reset per record

                # Write data for each column
                col_index = 0  # Tracks the column index dynamically
                for header in headers:
                    field_value = ''
                    if header == 'Service Date':
                        if record.service_time and self.from_date <= record.service_time <= self.to_date:
                            field_value = record.service_time.strftime('%d/%m/%Y')
                        else:
                            field_value = ''
                    elif header == 'Service Number':
                        field_value = record.name or ''
                    elif header == 'Customer C/O':
                        field_value = record.credit_customer_co or ''
                    elif header == 'Type':
                        # This column exists only if the customer is "AL MASAOOD AUTOMOBILES COMPANY LLC"
                        field_value = record.member_id.name or ''
                    elif header == 'Customer Category':
                        # This column exists only if the customer is "AL MASAOOD AUTOMOBILES COMPANY LLC"
                        field_value = record.sequence_id.description or ''
                    elif header == 'Vehicle Type':
                        field_value = record.vehicle_type or ''
                    elif header == 'Vehicle Model':
                        field_value = record.vehicle_model or ''
                    elif header == 'Vehicle Plate':
                        field_value = record.vehicle_plate or ''
                    elif header == 'Chassis No':
                        field_value = record.vehicle_chasis_no or ''
                    elif header == 'Service':
                        field_value = record.product_id.name or ''
                    # elif header == 'From Location':
                    #     if record.member_id.member_type in ['credit', 'adhoc']:
                    #         field_value = record.from_location.name if record.from_location else ''
                    #     else:
                    #         field_value = record.selected_from_location.name if record.selected_from_location else ''
                    # elif header == 'To Location':
                    #     if record.member_id.member_type in ['credit', 'adhoc']:
                    #         field_value = record.to_location.name if record.to_location else ''
                    #     else:
                    #         field_value = record.selected_to_location.name if record.selected_to_location else ''
                    elif header == 'From Location':
                        if record.member_id.member_type in ['policy', 'adhoc']:
                            # If selected_from_location is not set, fallback to from_location
                            field_value = record.selected_from_location.name if record.selected_from_location else (record.from_location.name if record.from_location else '')
                            
                        else:
                            field_value = record.from_location.name if record.from_location else ''
                           

                    elif header == 'To Location':
                        if record.member_id.member_type in ['policy', 'adhoc']:
                            # If selected_to_location is not set, fallback to to_location
                            field_value = record.selected_to_location.name if record.selected_to_location else (record.to_location.name if record.to_location else '')
                           
                        else:
                             field_value = record.to_location.name if record.to_location else ''
                           

                    elif header == 'Trip Sheet No.':
                        field_value = record.credit_proforma_number or ''
                    elif header == 'Quantity':
                        quantity = 1.00
                        total_service_quantity += quantity  # Add to total quantity
                        field_value = str(quantity)
                    elif header == 'Rate':
                        if record.member_id.member_type == 'policy':
                            pricelist_item = self.env['product.pricelist.item'].search([
                                ('product_tmpl_id', '=', record.member_id.product_template_id.id)
                            ], limit=1)
                            rate = pricelist_item.fixed_price if pricelist_item else 0.00
                        else:
                            service_rate = self.env['service.rate'].search([
                                ('product_pricelist_item_id.product_tmpl_id', '=', record.product_id.id),
                                ('from_loc_id', '=', record.from_location.id),
                                ('to_loc_id', '=', record.to_location.id)
                            ], limit=1)
                            rate = service_rate.price if service_rate else 0.00
                        total_rate_sum += rate  # Add to total rate
                        field_value = rate
                    elif header == 'Amount':
                        # Ensure rate and amount are the same
                        amount = rate
                        total_service_amount_sum += amount
                        field_value = amount
                    elif header == 'VAT(5%)':
                        vat = amount * 0.05
                        total_vat_sum += vat
                        field_value = vat
                    elif header == 'Total':
                        total = amount + vat
                        total_sum += total
                        field_value = total

                    # Write field value and adjust column width
                    worksheet.write(row, col_index, field_value)
                    column_widths[col_index] = max(column_widths[col_index], len(str(field_value)) + 2)
                    col_index += 1

                row += 1

            # Adjust column widths for better readability
            for col_num, width in enumerate(column_widths):
                worksheet.set_column(col_num, col_num, width)

            
            total_row_label_col = headers.index('Trip Sheet No.')  # Find column for "Trip Sheet No."
            worksheet.write(row, total_row_label_col, 'TOTAL', total_format)  # Write "TOTAL" header
            worksheet.write(row, headers.index('Quantity'), total_service_quantity, total_format)  # Total Quantity
            worksheet.write(row, headers.index('Rate'), total_rate_sum, total_format)             # Total Rate
            worksheet.write(row, headers.index('Amount'), total_service_amount_sum, total_format)  # Total Amount
            worksheet.write(row, headers.index('VAT(5%)'), total_vat_sum, total_format)           # Total VAT
            worksheet.write(row, headers.index('Total'), total_sum, total_format)                 # Grand Total

            row += 1  # Move to next row after totals
        # Close the workbook and prepare for download
        workbook.close()

        # Create Excel attachment
        buffer.seek(0)
        file_data = {
            'name': 'Service Report.xlsx',
            'datas': base64.b64encode(buffer.getvalue()),
            'type': 'binary',
        }
        attachment = self.env['ir.attachment'].create(file_data)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'res_id': attachment.id,
            'view_mode': 'form',
            'target': 'new',
        }