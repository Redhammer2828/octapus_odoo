from odoo import models, fields, api
import datetime
from datetime import timedelta
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
from pytz import timezone
from odoo.exceptions import UserError
import logging
# Set up logging for debugging purposes
_logger = logging.getLogger(__name__)

class ServiceReportWizard(models.TransientModel):
    _name = 'service.report.wizard'
    _description = 'Service Report Wizard'

    from_date = fields.Date(
        string="From Date",
        required=True)

    to_date = fields.Date(
        string="To Date",
        required=True)

    customer_id = fields.Many2one('res.partner', string="Customer", domain="[('is_company', '=', True)]")
    member_type = fields.Selection([('credit', 'CREDIT'),('adhoc','AD-HOC')], string="Member Type",default ='credit')
    sequence_id = fields.Many2one('partner.category', string="Customer Category",
    domain="[('partner_id','=', customer_id), ('member_type', '=', member_type)]")
    type = fields.Selection([('cash', 'Cash'), ('non_cash', 'Non-Cash')], string="Service Type")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('initiate', 'Initiate'),
        ('dispatch', 'Dispatch'),
        ('start', 'Start'),
        ('reach', 'Reach'),
        ('completed_by_driver', 'Completed by driver'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ('change', 'Changed' ),
        ('approved','Approved'),
        ('requested','Requeted')
    ], string="Status", readonly=True, default='initiate', tracking=True)

# FETCH RECORDS ----- INITIAL SEARCH FUNCTION
    def _fetch_service_records(self):

        print("DATE FROM ----------CREDIT-----",self.from_date)
        print("To DATE ------CREDIT---------",self.to_date)
                # Convert input dates to Dubai time
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
        if self.from_date:
            domain.append(('service_time', '>=', self.from_date))
        if self.to_date:
            domain.append(('service_time', '<=', self.to_date))
        if self.state:
            domain.append(('state', '=', 'done'))

        service_records = self.env['aaa.service'].search(domain)
        _logger.debug("Fetched %d records from the aaa.service model", len(service_records))
        return service_records

    def _calculate_amount(self, record):
        """Calculate the amount for a membership record."""
        amount = 0.0
        pricelist = self.customer_id.property_product_pricelist.id
        print("PRICELIST ID------",pricelist)
        if record.member_type == 'credit':
            if record.from_location and record.to_location and record.product_id and record.customer_id:
                service_rate = self.env['service.rate'].search([
                    ('product_pricelist_item_id.pricelist_id', '=' , pricelist),
                    ('product_pricelist_item_id.product_tmpl_id', '=', record.product_id.id),
                    ('from_loc_id', '=', record.from_location.id),
                    ('to_loc_id', '=', record.to_location.id)
                ], limit=1)
                amount = service_rate.price if service_rate else 0.0
        elif record.member_type == 'policy':
            if record.name and record.product_template_id:
                pricelist_item = self.env['product.pricelist.item'].search([
                    ('pricelist_id' , '=' , pricelist ),
                    ('product_tmpl_id', '=', record.product_template_id.id)
                ], limit=1)
                amount = pricelist_item.fixed_price if pricelist_item else 0.0
        return f"{float(amount or 0):.2f}"

# EXCEL REPORT GENERATOR------------
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
                        if record.service_time:
                            # Convert datetime to date for comparison
                            service_time_date = record.service_time.date()
                            if self.from_date <= service_time_date <= self.to_date:
                                field_value = record.service_time.strftime('%d/%m/%Y')
                            else:
                                field_value = ''
                        # if record.service_time and self.from_date <= record.service_time <= self.to_date:
                        #     field_value = record.service_time.strftime('%d/%m/%Y')
                        # else:
                        #     field_value = ''
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
                            customer_pricelist_id = self.customer_id.property_product_pricelist_id.id if self.customer_id else False
                            if customer_pricelist_id:
                                product_pricelist_item = self.env['product.pricelist.item'].search([
                                    ('pricelist_id', '=', customer_pricelist_id),
                                    ('product_tmpl_id', '=', record.product_id.id),
                                    ('date_start', '<=', record.service_time),
                                    ('date_end', '>=', record.service_time)
                                ], order="date_start desc", limit=1)
                                print('product_pricelist_item______________',product_pricelist_item)
                                if product_pricelist_item:
                                    service_rate = self.env['service.rate'].search([
                                        ('product_pricelist_item_id', '=', product_pricelist_item.id),
                                        ('from_loc_id', '=', record.from_location.id),
                                        ('to_loc_id', '=', record.to_location.id)
                                    ], limit=1)
                                else:
                                    raise UserError(f'validity not set for product: {record.product_id.name}')
                                rate = service_rate.price if service_rate else 0.00
                            else:
                                raise UserError(f'Pricelist Not Mapped for {self.customer_id.name}')

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
