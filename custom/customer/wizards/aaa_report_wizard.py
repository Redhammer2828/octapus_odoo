from odoo import models, fields, api
import datetime
from datetime import timedelta
from pytz import timezone, UTC
import pytz
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

class AaaReportWizard(models.TransientModel):
    _name = 'aaa.report.wizard'
    _description = 'AAA Report Wizard'

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
    
    def action_print_pdf(self):
        pass

    def action_export_excel(self):
        import io
        import base64
        import xlsxwriter
        from odoo import _

        # Initialize buffer for Excel generation
        buffer = io.BytesIO()
        service_records = self._fetch_service_records()

        # Prepare Excel export
        workbook = xlsxwriter.Workbook(buffer)
        worksheet = workbook.add_worksheet('Daily Service Report')

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
        worksheet.merge_range('A1:AF1', 'SERVICE REPORT', title_format)

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
            'Number', 'Service Date & Time', 'Created Date & Time', 'Customer Name', 'Category',
            'Membership Number', 'Member Name', 'Membership State', 'Mobile', 'Policy Number',
            'Member Type', 'Service Type', 'Vehicle Type', 'Vehicle Plate', 'In Progress Date and Time',
            'Service', 'Provider', 'Driver', 'Driver Mobile Number', 'From - Location', 'To - Location',
            'From - Date', 'To - Date', 'Smart Tow ID', 'Status', 'Agent', 'Dispatcher', 'Comments',
            'Trip Sheet Number', 'Amount Collected', 'Rating', 'Rating Added By'
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
                if header == 'Number':
                    field_value = record.name or ''
                elif header == 'Service Date & Time':
                    if record.service_time:
                        # Assuming `record.service_time` is in UTC
                        utc_time = record.service_time  # datetime object in UTC
                        target_timezone = timezone('Asia/Kolkata')  # Replace with your logic for dynamic timezone if needed
                        local_time = UTC.localize(utc_time).astimezone(target_timezone)
                        field_value = local_time.strftime('%m/%d/%Y %H:%M:%S')  # Desired format: mm/dd/yyyy hh:mm:ss
                    else:
                        field_value = ''
                elif header == 'Created Date & Time':
                    if record.create_date:
                        # Assuming `record.service_time` is in UTC
                        utc_time = record.create_date  # datetime object in UTC
                        target_timezone = timezone('Asia/Kolkata')  # Replace with your logic for dynamic timezone if needed
                        local_time = UTC.localize(utc_time).astimezone(target_timezone)
                        field_value = local_time.strftime('%m/%d/%Y %H:%M:%S')  # Desired format: mm/dd/yyyy hh:mm:ss
                    else:
                        field_value = ''
                elif header == 'Customer Name':
                    field_value = record.customer_id.name or ''
                elif header == 'Category':
                    field_value = record.sequence_id.name or ''
                
                elif header == 'Membership Number':
                    field_value = record.membership_num or ''
                elif header == 'Member Name':
                    field_value = record.member_id.name or ''
                elif header == 'Membership State':
                    if record.member_id.member_type in ['credit', 'adhoc']:
                        field_value = 'confirm'
                    else:
                        field_value = record.member_id.membership_state
                elif header == 'Mobile':
                    field_value = record.member_contact_no or ''
                elif header == 'Policy Number':
                    field_value = record.policy_no or ''
                elif header == 'Member Type':
                    field_value = record.member_id.member_type or ''
                elif header == 'Service Type':
                    field_value = record.type or ''
                elif header == 'Vehicle Type':
                    field_value = record.vehicle_type or ''
                elif header == 'Vehicle Plate':
                    field_value = record.vehicle_plate or ''
                elif header == 'In Progress Date and Time':
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
                elif header == 'Service':
                    field_value = record.product_id.name or ''
                elif header == 'Provider':
                    field_value = record.provider_id.name or ''
                elif header == 'Driver':
                    field_value = record.driver_id.name or ''
                elif header == 'Driver Mobile Number':
                    field_value = record.driver_num or ''
                

                elif header == 'From - Location':
                    if record.member_id.member_type in ['policy', 'adhoc']:
                        # field_value = record.selected_from_location.name if record.selected_from_location else ''
                        # If selected_from_location is not set, fallback to from_location
                        field_value = record.selected_from_location.name if record.selected_from_location else (record.from_location.name if record.from_location else '')
                        
                    else:
                        field_value = record.from_location.name if record.from_location else ''
                elif header == 'To - Location':
                    if record.member_id.member_type in ['policy', 'adhoc']:
                        #field_value = record.selected_to_location.name if record.selected_to_location else ''
                        # If selected_to_location is not set, fallback to to_location
                        field_value = record.selected_to_location.name if record.selected_to_location else (record.to_location.name if record.to_location else '')
                        
                    else:
                        field_value = record.to_location.name if record.to_location else ''

                elif header == 'From - Date':
                    # field_value = record.date_time_from.strftime('%d/%m/%Y %H:%M:%S') if record.date_time_from else ''
                    if record.date_time_from:
                        # Assuming `record.service_time` is in UTC
                        utc_time = record.date_time_from  # datetime object in UTC
                        target_timezone = timezone('Asia/Kolkata')  # Replace with your logic for dynamic timezone if needed
                        local_time = UTC.localize(utc_time).astimezone(target_timezone)
                        field_value = local_time.strftime('%m/%d/%Y %H:%M:%S')  # Desired format: mm/dd/yyyy hh:mm:ss
                    else:
                        field_value = ''
                elif header == 'To - Date':
                    if record.date_time_to:
                        # Assuming `record.service_time` is in UTC
                        utc_time = record.date_time_to  # datetime object in UTC
                        target_timezone = timezone('Asia/Kolkata')  # Replace with your logic for dynamic timezone if needed
                        local_time = UTC.localize(utc_time).astimezone(target_timezone)
                        field_value = local_time.strftime('%m/%d/%Y %H:%M:%S')  # Desired format: mm/dd/yyyy hh:mm:ss
                    else:
                        field_value = ''
                elif header == 'Smart Tow ID':
                    field_value = record.smarto_id or ''
                elif header == 'Status':
                    field_value = record.state or ''
                elif header == 'Agent':
                    service_history = self.env['service.history'].search([
                        ('service_id', '=', record.id),
                        ('status', '=', 'initiate')
                    ], limit=1)
                    field_value = service_history.user.login if service_history and service_history.user else ''
                elif header == 'Dispatcher':
                #     field_value = record.dispatcher_from_history
                    service_history = self.env['service.history'].search([
                        ('service_id', '=', record.id),
                        ('status', '=', 'dispatch')
                    ], limit=1)
                    field_value = service_history.user.login if service_history and service_history.user else ''

                elif header == 'Comments':
                    service_comment = self.env['service.comment'].search([
                        ('service_id', '=', record.id),
                        ('comment_status', '=', record.state)
                    ], limit=1)
                    field_value = service_comment.comment if service_comment and service_comment.comment else ''
                elif header == 'Trip Sheet Number':
                    field_value = record.credit_proforma_number or ''
                elif header == 'Amount Collected':
                    field_value = record.cash_collected or 0.00
                elif header == 'Rating':
                    field_value = record.vendor_rating or 0
                elif header == 'Rating Added By':
                    field_value = record.rating_user_id.name or ''

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
            'name': 'Service_Report.xlsx',
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
