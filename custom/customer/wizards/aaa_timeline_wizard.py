from odoo import models, fields, api
import datetime
from datetime import timedelta
from pytz import timezone, UTC
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

class AaaTimelineWizard(models.TransientModel):
    _name = 'aaa.timeline.wizard'
    _description = 'AAA Timeline Wizard'

    from_date = fields.Datetime(string="From Date", required=True)
    to_date = fields.Datetime(string="To Date", required=True)
   

    from_date = fields.Datetime(
        string="From Date",
        required=True,
        default=lambda self: self._get_datetime_with_midnight()
    )

    to_date = fields.Datetime(
        string="To Date",
        required=True,
        default=lambda self: self._get_datetime_with_midnight()
    )

    def _get_datetime_with_midnight(self):
        # Get today's date in the user's time zone
        user_tz = timezone(self.env.user.tz or 'UTC')  # Default to UTC if no timezone is set
        today_date = datetime.now(user_tz).date()  # Get today's date in user's time zone
        
        # Combine today's date with midnight time (00:00:00)
        midnight = datetime.combine(today_date, time(0, 0, 0))

        # Localize this time to the user's time zone and then convert to naive datetime
        midnight_user_tz = user_tz.localize(midnight)
        naive_midnight = midnight_user_tz.astimezone(timezone('UTC')).replace(tzinfo=None)

        return naive_midnight
    
    customer_id = fields.Many2one('res.partner', string="Customer", domain="[('is_company', '=', True)]")
    member_type = fields.Selection([('policy', 'POLICY'), ('credit', 'CREDIT'),('adhoc','AD-HOC')], string="Member Type")
    sequence_id = fields.Many2one('partner.category', string="Customer Category",
    domain="[('partner_id','=', customer_id), ('member_type', '=', member_type)]")
    type = fields.Selection([('cash', 'Cash'), ('non_cash', 'Non-Cash')], string="Service Type")
    provider_id = fields.Many2one('res.partner', string="Provider" ,domain=[('is_vendor', '=', True)])

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
        worksheet = workbook.add_worksheet('Timeline Service Report')

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
        worksheet.merge_range('A1:AF1', 'TIMELINE REPORT', title_format)

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
            'Id Request', 'User Details', 'User Vehicle Details', 'User Location', 'Provider', 'Driver Name',
            'Requested Services', 'Request Date', 'Request Status', 'Request Completed On', 'Driver Start Time', 'Driver Arrival Time',
            'Service Started Time', 'Service Completed Time', 'Cancellation Time', 'Dispatch Center Notes'
        ]

        # Write headers
        for col_num, header in enumerate(headers):
            worksheet.write(7, col_num, header, header_format)

        # Populate data rows
        row = 8
        for record in service_records:
            col_index = 0
            for header in headers:
                field_value = ''
                if header == 'Id Request':
                    field_value = record.name or ''
               
                elif header == 'User Details':
                    field_value = record.member_id.name or ''
               
                elif header == 'User Vehicle Details':
                    field_value = record.vehicle_type or ''
                
                elif header == 'User Location':
                    if record.member_id.member_type in ['policy', 'adhoc']:
                        field_value = record.selected_from_location.name if record.selected_from_location else ''
                        
                    else:
                        field_value = record.from_location.name if record.from_location else ''
                
                
                elif header == 'Provider':
                    field_value = record.provider_id.name or ''
                elif header == 'Driver Name':
                    field_value = record.driver_id.name or ''
                elif header == 'Requested Services':
                    field_value = record.product_id.name or ''
                elif header == 'Request Date':
                    if record.service_time:
                        # Assuming `record.service_time` is in UTC
                        utc_time = record.service_time  # datetime object in UTC
                        target_timezone = timezone('Asia/Kolkata')  # Replace with your logic for dynamic timezone if needed
                        local_time = UTC.localize(utc_time).astimezone(target_timezone)
                        field_value = local_time.strftime('%m/%d/%Y %H:%M:%S')  # Desired format: mm/dd/yyyy hh:mm:ss
                    else:
                        field_value = ''
                elif header == 'Request Status':
                    field_value = record.state or ''
                elif header == 'Request Completed On':
                    service_history = self.env['service.history'].search([
                        ('service_id', '=', record.id),
                        ('status', '=', 'done')
                    ], limit=1)
                    if service_history:
                        utc_time = service_history.time  # Assuming this is a datetime object
                        target_timezone = timezone('Asia/Kolkata')  # Replace with your target timezone
                        local_time = UTC.localize(utc_time).astimezone(target_timezone)
                        field_value = local_time.strftime('%m/%d/%Y %H:%M:%S')
                    else:
                        field_value = ''
               

                elif header == 'Driver Start Time':
                    service_history = self.env['service.history'].search([
                            ('service_id', '=', record.id),
                            ('status', '=', 'start')
                        ], limit=1)
                    
                    if service_history:
                        utc_time = service_history.time  # Assuming this is a datetime object
                        target_timezone = timezone('Asia/Kolkata')  # Replace with your target timezone
                        local_time = UTC.localize(utc_time).astimezone(target_timezone)
                        field_value = local_time.strftime('%m/%d/%Y %H:%M:%S')
                    else:
                        field_value = ''
                elif header == 'Driver Arrival Time':
                    service_history = self.env['service.history'].search([
                            ('service_id', '=', record.id),
                            ('status', '=', 'reach')
                        ], limit=1)
                    if service_history:
                        utc_time = service_history.time  # Assuming this is a datetime object
                        target_timezone = timezone('Asia/Kolkata')  # Replace with your target timezone
                        local_time = UTC.localize(utc_time).astimezone(target_timezone)
                        field_value = local_time.strftime('%m/%d/%Y %H:%M:%S')
                    else:
                        field_value = ''
                elif header == 'Service Started Time':
                    service_history = self.env['service.history'].search([
                        ('service_id', '=', record.id),
                        ('status', '=', 'start')
                    ], limit=1)
                    if service_history:
                        utc_time = service_history.time  # Assuming this is a datetime object
                        target_timezone = timezone('Asia/Kolkata')  # Replace with your target timezone
                        local_time = UTC.localize(utc_time).astimezone(target_timezone)
                        field_value = local_time.strftime('%m/%d/%Y %H:%M:%S')
                    else:
                        field_value = ''
                elif header == 'Service Completed Time':
                    service_history = self.env['service.history'].search([
                        ('service_id', '=', record.id),
                        ('status', '=', 'done')
                    ], limit=1)
                    if service_history:
                        utc_time = service_history.time  # Assuming this is a datetime object
                        target_timezone = timezone('Asia/Kolkata')  # Replace with your target timezone
                        local_time = UTC.localize(utc_time).astimezone(target_timezone)
                        field_value = local_time.strftime('%m/%d/%Y %H:%M:%S')
                    else:
                        field_value = ''
                elif header == 'Cancellation Time':
                    service_history = self.env['service.history'].search([
                        ('service_id', '=', record.id),
                        ('status', '=', 'cancel')
                    ], limit=1)
                    if service_history:
                        utc_time = service_history.time  # Assuming this is a datetime object
                        target_timezone = timezone('Asia/Kolkata')  # Replace with your target timezone
                        local_time = UTC.localize(utc_time).astimezone(target_timezone)
                        field_value = local_time.strftime('%m/%d/%Y %H:%M:%S')
                    else:
                        field_value = ''
                elif header == 'Dispatch Center Notes':
                    service_comment = self.env['service.comment'].search([
                        ('service_id', '=', record.id),
                        ('comment_status', '=', record.state)
                    ], limit=1)
                    field_value = service_comment.comment if service_comment and service_comment.comment else ''
                
                
                

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
            'name': 'Timeline_Report.xlsx',
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