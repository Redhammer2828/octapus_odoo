from odoo import models, fields, api
import datetime
from datetime import timedelta
from datetime import datetime
import io
import xlsxwriter
import base64
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import BytesIO
from reportlab.lib.utils import ImageReader  # Import ImageReader

import logging
# Set up logging for debugging purposes
_logger = logging.getLogger(__name__)

class ServiceReportWizard(models.TransientModel):
    _name = 'service.report.wizard'
    _description = 'Service Report Wizard'

    from_date = fields.Datetime(string="From Date", required=True)
    to_date = fields.Datetime(string="To Date", required=True)
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
    
    def action_print_pdf(self):
        """Generate Membership Details PDF."""
        import textwrap
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        from reportlab.lib.units import inch
        import io
        import base64
 
        # Prepare domain filters
        domain = []
        if self.customer_id:
            domain.append(('customer_id', '=', self.customer_id.id))
        if self.member_type:
            domain.append(('member_type', '=', self.member_type))
 
        # Fetch data
        service_records = self.env['aaa.service'].search(domain)
 
        # PDF buffer
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
        width, height = landscape(A4)
        margin = 20
        table_y_start = height - 120  # Table starts after title/logo
 
        # Company logo setup
        company = self.env['res.company'].search([], limit=1)
        logo_width, logo_height = 1.2 * inch, 1.2 * inch
 
        # Define headers and column widths
        headers = [
            'MEMBERSHIP\nNO.', 'NAME', 'PLATE\nNO.', 'CHASIS\nNO.', 'POLICY\nNO.',
            'START\nDATE', 'EXPIRY\nDATE', 'CAR\nMAKE', 'AMOUNT'
        ]
        col_widths = [85, 130, 85, 115, 95, 75, 75, 85, 65]  # Adjusted widths
        header_height = 40  # Increased height for header row
        row_height = 30    # Standard height for data rows
 
        def draw_header(pdf):
            """Draw header with company logo and tagline."""
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
 
            # Center the title in the header
            pdf.setFont("Helvetica-Bold", 12)
            title = "Membership Details"
            pdf.drawString((width - pdf.stringWidth(title, "Helvetica-Bold", 12)) / 2, height - 40, title)
 
            # Draw the tagline below the logo
            pdf.setFont("Helvetica", 8)
            tagline_y_position = height - logo_height - 15
            pdf.drawRightString(width - margin, tagline_y_position, "We guarantee to get you moving...")
 
        def draw_table_header(pdf, y_position):
            """Draw table headers with proper spacing."""
            x_offset = margin
            pdf.setFont("Helvetica-Bold", 8)  # Slightly larger font for headers
           
            # Draw header cells
            for i, header in enumerate(headers):
                # Draw the cell rectangle
                pdf.rect(x_offset, y_position - header_height, col_widths[i], header_height)
               
                # Calculate center position for text
                text_lines = header.split('\n')
                total_text_height = len(text_lines) * 10  # 10 points per line
                starting_y = y_position - (header_height / 2) + (total_text_height / 2)
               
                # Draw each line of text centered in its cell
                for line in text_lines:
                    text_width = pdf.stringWidth(line, "Helvetica-Bold", 8)
                    x_text = x_offset + (col_widths[i] - text_width) / 2
                    pdf.drawString(x_text, starting_y - 10, line)
                    starting_y -= 10
                   
                x_offset += col_widths[i]
           
            return y_position - header_height
 
        def draw_data_row(pdf, record, y_position):
            """Draw each record row with proper text wrapping."""
            x_offset = margin
            pdf.setFont("Helvetica", 7)  # Consistent font size for data
           
            # Prepare data
            data = [
                record.member_id.old_membership_number or '',
                record.member_id.name or '',
                record.vehicle_plate or '',
                record.vehicle_chasis_no or '',
                record.policy_no or '',
                record.member_id.member_activate_date.strftime('%d-%m-%Y') if record.member_id.member_activate_date else '',
                record.member_id.member_expiry_date.strftime('%d-%m-%Y') if record.member_id.member_expiry_date else '',
                record.vehicle_type or '',
            ]
 
            # Calculate amount
            if record.member_type == 'credit':
                if record.from_location and record.to_location and record.product_id:
                    service_rate = self.env['service.rate'].search([
                        ('product_pricelist_item_id.product_tmpl_id', '=', record.product_id.id),
                        ('from_loc_id', '=', record.from_location.id),
                        ('to_loc_id', '=', record.to_location.id)
                    ], limit=1)
                    amount = service_rate.price if service_rate else 0.0
                else:
                    amount = 0.0
            elif record.member_type == 'policy':
                if record.member_id and record.member_id.product_template_id:
                    pricelist_item = self.env['product.pricelist.item'].search([
                        ('product_tmpl_id', '=', record.member_id.product_template_id.id)
                    ], limit=1)
                    amount = pricelist_item.fixed_price if pricelist_item else 0.0
                else:
                    amount = 0.0
            data.append(f"{float(amount or 0):.2f}")
 
            # Draw cells
            for i, value in enumerate(data):
                # Draw cell rectangle
                pdf.rect(x_offset, y_position - row_height, col_widths[i], row_height)
               
                # Handle text wrapping and positioning
                wrapped_text = textwrap.fill(str(value), width=int(col_widths[i]/5))
                text_lines = wrapped_text.split('\n')
               
                # Calculate vertical position for text
                line_height = 10
                total_text_height = len(text_lines) * line_height
                text_y = y_position - (row_height/2) + (total_text_height/2) - line_height
               
                for line in text_lines:
                    if i == 8:  # Amount column - right aligned
                        pdf.drawRightString(x_offset + col_widths[i] - 5, text_y, line)
                    else:  # Other columns - left aligned
                        pdf.drawString(x_offset + 5, text_y, line)
                    text_y -= line_height
               
                x_offset += col_widths[i]
           
            return y_position - row_height
 
        # Generate PDF
        draw_header(pdf)
        y_position = table_y_start
        y_position = draw_table_header(pdf, y_position)
 
        for record in service_records:
            if y_position < 50:  # Start new page if needed
                pdf.showPage()
                draw_header(pdf)
                y_position = table_y_start
                y_position = draw_table_header(pdf, y_position)
 
            y_position = draw_data_row(pdf, record, y_position)
 
        pdf.save()
        buffer.seek(0)
 
        # Create attachment
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
            # Include 'Type' only if customer_id is "AL MASAOOD AUTOMOBILES COMPANY LLC"
            *(['Type'] if self.customer_id and self.customer_id.name == 'AL MASAOOD AUTOMOBILES COMPANY LLC' else []),
            'Vehicle Type', 'Vehicle Model', 'Vehicle Plate', 'Chassis No', 'Service',
            'From Location', 'To Location', 'Trip Sheet No.', 'Quantity', 'Rate', 'Amount',
            'Tax', 'Total'
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
            total_service_amount_sum = 0
            total_tax_sum = 0
            total_sum = 0

            for record in service_records:
                # Initialize variables
                rate = 0.00
                amount = 0.00
                tax = 0.00
                total = 0.00

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
                    elif header == 'From Location':
                        if record.member_id.member_type in ['credit', 'adhoc']:
                            field_value = record.from_location.name if record.from_location else ''
                        else:
                            field_value = record.selected_from_location.name if record.selected_from_location else ''
                    elif header == 'To Location':
                        if record.member_id.member_type in ['credit', 'adhoc']:
                            field_value = record.to_location.name if record.to_location else ''
                        else:
                            field_value = record.selected_to_location.name if record.selected_to_location else ''
                    elif header == 'Trip Sheet No.':
                        field_value = record.credit_proforma_number or ''
                    elif header == 'Quantity':
                        field_value = str(record.service_quantity) or ''
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
                        field_value = rate
                    elif header == 'Amount':
                        amount = rate
                        field_value = amount
                    elif header == 'Tax':
                        tax = amount * 0.05
                        field_value = tax
                    elif header == 'Total':
                        total = amount + tax
                        field_value = total

                    # Write field value and adjust column width
                    worksheet.write(row, col_index, field_value)
                    column_widths[col_index] = max(column_widths[col_index], len(str(field_value)) + 2)
                    col_index += 1

                # Accumulate totals
                total_service_amount_sum += amount
                total_tax_sum += tax
                total_sum += total
                row += 1

            # Adjust column widths for better readability
            for col_num, width in enumerate(column_widths):
                worksheet.set_column(col_num, col_num, width)

            # Write totals at the end
            worksheet.write(row, len(headers) - 4, 'Total', total_format)
            worksheet.write(row, len(headers) - 3, total_service_amount_sum, total_format)
            worksheet.write(row, len(headers) - 2, total_tax_sum, total_format)
            worksheet.write(row, len(headers) - 1, total_sum, total_format)

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