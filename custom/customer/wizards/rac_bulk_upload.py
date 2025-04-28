from odoo import models, fields, api
import datetime
from datetime import timedelta
from pytz import timezone, UTC
import pytz
# from pytz import timezone, UTC
import io
import xlsxwriter
import base64
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import BytesIO
from reportlab.lib.utils import ImageReader  # Import ImageReader
from datetime import datetime, time

import logging
# Set up logging for debugging purposes
_logger = logging.getLogger(__name__)

class RACBulkUpload(models.TransientModel):
    _name = 'rac.bulk.upload'
    _description = 'RAC Bulk Upload'

    from_date = fields.Datetime(string="From Date", required=True)
    to_date = fields.Datetime(string="To Date", required=True)
   

    
    
    customer_id = fields.Many2one('res.partner', string="Customer", domain="[('is_company', '=', True)]")
    member_type = fields.Selection([('policy', 'POLICY'), ('credit', 'CREDIT'),('adhoc','AD-HOC')], string="Member Type")
    sequence_id = fields.Many2one('partner.category', string="Customer Category",
    domain="[('partner_id','=', customer_id), ('member_type', '=', member_type)]")
    type = fields.Selection([('cash', 'Cash'), ('non_cash', 'Non-Cash')], string="Service Type")
    provider_id = fields.Many2one('res.partner', string="Provider" ,domain=[('is_vendor', '=', True)])
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
    ], string="Status")
    product_id = fields.Many2one('product.template', string="Service",domain=[('bundle_product', '=', False)])
    service_based = fields.Selection(related='product_id.service_based', store=True, readonly=True)

    # Convert timestamps
    # local_tz = timezone('Asia/Kolkata')
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
        if self.provider_id:
            domain.append(('provider_id', '=', self.provider_id.id))

               # Filter by Service Time (Date Range)
        domain.append(('service_time', '>=', self.from_date))
        domain.append(('service_time', '<=', self.to_date))
        # Filter by State
        #domain.append(('state', 'in', ['done', 'completed_by_driver', 'cancel']))
        domain.append(('service_based', '=', 'location_duration'))

        service_records = self.env['aaa.service'].search(domain)
        _logger.debug("Fetched %d records from the aaa.service model", len(service_records))
        return service_records

    
    def action_export_excel(self):
        #pass
        import io
        import base64
        import xlsxwriter
        from odoo import _

        # Initialize buffer for Excel generation
        buffer = io.BytesIO()
        service_records = self._fetch_service_records()

        # Prepare Excel export
        workbook = xlsxwriter.Workbook(buffer)
        worksheet = workbook.add_worksheet('RAC Service Report')

        # Define formats
        title_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 14,
            'border': 1
        })
        metadata_label_format = workbook.add_format({
            'bold': True,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 10
        })
        metadata_value_format = workbook.add_format({
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 10
        })
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#D9D9D9',
            'border': 1
        })
        data_format = workbook.add_format({
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 10
        })

        # Title Row
        worksheet.merge_range('A1:AF1', 'RAC BULK REPORT', title_format)

        # Metadata Fields
        date_range = f"{self.from_date.strftime('%d/%m/%Y')} - {self.to_date.strftime('%d/%m/%Y')}" if self.from_date and self.to_date else ''
        customer_name = self.customer_id.customer_code if self.customer_id else ''
        type_name = self.type if self.type else ''
        member_type = self.member_type if self.member_type else ''

        worksheet.write('A3', _('Date Range:'), metadata_label_format)
        worksheet.write('B3', date_range, metadata_value_format)

        worksheet.write('A4', _('Customer:'), metadata_label_format)
        worksheet.write('B4', customer_name, metadata_value_format)

        worksheet.write('A5', _('Type:'), metadata_label_format)
        worksheet.write('B5', type_name, metadata_value_format)

        worksheet.write('A6', _('Member Type:'), metadata_label_format)
        worksheet.write('B6', member_type, metadata_value_format)

        # Define headers

        headers = [
            'ID', 'Customer', 'Service', 'Service Date Time', 'Number', 
            'Customer C/O', 'Member', 'Vehicle Plate', 'Claim No.', 'From Date Time', 
            'To Date Time', 'Vehicle Type', 'Vehicle Model', 'To Location', 'Policy No.', 
            'Provider', 'Status', 'Mobile No.', 'Email', 'Quantity']

        

        # Write headers
        for col_num, header in enumerate(headers):
            worksheet.write(7, col_num, header, header_format)

        # Populate data rows
        row = 8
        for record in service_records:
            col_index = 0
            for header in headers:
                field_value = ''
                if header == 'ID':
                    field_value = record.id or ''
               
                elif header == 'Customer':
                    field_value = record.customer_id.name or ''
                
                elif header == 'Service':
                    field_value = record.product_id.name or ''

                elif header == 'Service Date Time':
                    if record.service_time:
                        # Assuming `record.service_time` is in UTC
                        utc_time = record.service_time  # datetime object in UTC
                        target_timezone = timezone('Asia/Dubai')  # Replace with your logic for dynamic timezone if needed
                        local_time = UTC.localize(utc_time).astimezone(target_timezone)
                        field_value = local_time.strftime('%d/%m/%Y %H:%M:%S')  # Desired format: mm/dd/yyyy hh:mm:ss
                    else:
                        field_value = ''

                elif header == 'Number':
                    field_value = record.name or ''

                elif header == 'Customer C/O':
                    field_value = record.credit_customer_co or ''

                elif header == 'Member':
                    field_value = record.member_id.name or ''

                elif header == 'Vehicle Plate':
                    field_value = record.vehicle_plate or ''

                elif header == 'Claim No.':
                    field_value = record.claim_number or ''

                elif header == 'From Date Time':
                    local_tz = timezone('Asia/Dubai')  # Change this to your local timezone
                    field_value = record.date_time_from.astimezone(local_tz).strftime('%d/%m/%Y %H:%M:%S') if record.date_time_from else ''

                elif header == 'To Date Time':
                    field_value = record.date_time_to.astimezone(local_tz).strftime('%d/%m/%Y %H:%M:%S') if record.date_time_to else ''

                elif header == 'Vehicle Type':
                    field_value = record.vehicle_type or ''

                elif header == 'Vehicle Model':
                    field_value = record.vehicle_model or ''

                elif header == 'To Location':
                    if record.member_id.member_type in ['policy', 'adhoc']:
                        #field_value = record.selected_from_location.name if record.selected_from_location else ''
                        # If selected_from_location is not set, fallback to from_location
                        field_value = record.selected_to_location.name if record.selected_to_location else (record.to_location.name if record.to_location else '')
                        
                    else:
                        field_value = record.to_location.name if record.to_location else ''

                elif header == 'Policy No.':
                    field_value = record.policy_no or ''

                elif header == 'Provider':
                    field_value = record.provider_id.name or ''

                elif header == 'Status':
                    field_value = record.state or ''
               

                elif header == 'Mobile No.':
                    field_value = record.member_contact_no or ''

                
                elif header == 'Email':
                    field_value = record.email or ''


                elif header == 'Quantity':
                    field_value = record.quantity or ''
                 

                worksheet.write(row, col_index, field_value, data_format)
                col_index += 1

            row += 1

        # Adjust column widths
        worksheet.set_column(0, len(headers) - 1, 20)

        # Close workbook and prepare for download
        workbook.close()
        buffer.seek(0)

        # Create Excel attachment
        file_data = {
            'name': 'RAC_Bulk_Report.xlsx',
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