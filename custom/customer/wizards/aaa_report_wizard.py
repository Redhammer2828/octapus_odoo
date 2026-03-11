from odoo import models, fields, api
import io
import xlsxwriter
import base64
from pytz import timezone, UTC
import logging
from datetime import datetime, time
import pytz
 
_logger = logging.getLogger(__name__)
 
class AaaReportWizard(models.TransientModel):
    _name = 'aaa.report.wizard'
    _description = 'AAA Report Wizard'
 
    from_date = fields.Date(string="From Date", required=True)
    to_date = fields.Date(string="To Date", required=True)
    customer_id = fields.Many2one('res.partner', string="Customer", domain="[('is_company', '=', True)]")
    member_type = fields.Selection([('policy', 'POLICY'), ('credit', 'CREDIT'), ('adhoc', 'AD-HOC')], string="Member Type")
    sequence_id = fields.Many2one('partner.category', string="Customer Category", domain="[('partner_id','=', customer_id), ('member_type', '=', member_type)]")
    type = fields.Selection([('cash', 'Cash'), ('non_cash', 'Non-Cash')], string="Service Type")
    provider_id = fields.Many2one('res.partner', string="Provider", domain="[('is_vendor', '=', True)]")
    product_id = fields.Many2one('product.template', string='Service', domain="[('bundle_product', '=', False)]")
 
    # def _fetch_service_records(self):
    #     domain = [('service_time', '>=', self.from_date), ('service_time', '<=', self.to_date)]
    #     if self.customer_id:
    #         domain.append(('customer_id', '=', self.customer_id.id))
    #     if self.member_type:
    #         domain.append(('member_type', '=', self.member_type))
    #     if self.type:
    #         domain.append(('type', '=', self.type))
    #     if self.sequence_id:
    #         domain.append(('sequence_id', '=', self.sequence_id.id))
    #     if self.provider_id:
    #         domain.append(('provider_id', '=', self.provider_id.id))

    def _fetch_service_records(self):
        # Define timezone
        local_tz = pytz.timezone('Asia/Dubai')
        
        # Convert to timezone-aware UTC datetimes
        start_local = local_tz.localize(datetime.combine(self.from_date, time.min))
        end_local = local_tz.localize(datetime.combine(self.to_date, time.max))
        
        # Convert to UTC for comparison with stored UTC timestamps
        start_datetime = start_local.astimezone(pytz.UTC)
        end_datetime = end_local.astimezone(pytz.UTC)

        domain = [('service_time', '>=', start_datetime), ('service_time', '<=', end_datetime)]
        
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
        if self.product_id:
            domain.append(('product_id', '=', self.product_id.id))
 
        fields_to_fetch = [
            'name', 'service_time', 'create_date', 'customer_id', 'sequence_id',
            'membership_num', 'member_id','member_type', 'member_contact_no', 'policy_no',
            'type', 'vehicle_type', 'vehicle_plate', 'vehicle_chasis_no', 'product_id', 'provider_id',
            'driver_id', 'driver_name', 'driver_num','is_jafza_service', 'jafza_provider_id', 'jafza_driver_id', 
            'jafza_driver_name', 'is_aditional_duty', 'selected_from_location', 'from_location',
            'from_location_emirate', 'selected_to_location', 'to_location',
            'to_location_emirate', 'date_time_from', 'date_time_to', 'smarto_id',
            'state', 'credit_proforma_number', 'cash_collected', 'vendor_rating',
            'rating_user_id', 'create_uid', 'dispatcher_from_history', 'dispatch_done_by'
        ]
 
        #return self.env['aaa.service'].search_read(domain, fields_to_fetch)

        # service_records = self.env['aaa.service'].search_read(domain, fields_to_fetch)
        
        # # Fetch membership states for all member_ids in one go
        # member_ids = [record['member_id'][0] for record in service_records if record.get('member_id')]
        # member_states = {}
        # if member_ids:
        #     partners = self.env['res.partner'].search_read(
        #         [('id', 'in', member_ids)],
        #         ['id', 'membership_state']
        #     )
        #     member_states = {partner['id']: partner['membership_state'] for partner in partners}
            
        # # Add membership_state to each service record
        # for record in service_records:
        #     if record.get('member_id'):
        #         record['membership_state'] = member_states.get(record['member_id'][0], '')
                
        # return service_records

        service_records = self.env['aaa.service'].search_read(domain, fields_to_fetch)
        
        # Fetch membership states only for policy type members
        policy_member_ids = [record['member_id'][0] for record in service_records 
                           if record.get('member_id') and record.get('member_type') == 'policy']
        
        member_states = {}
        if policy_member_ids:
            partners = self.env['res.partner'].search_read(
                [('id', 'in', policy_member_ids)],
                ['id', 'membership_state']
            )
            member_states = {partner['id']: partner['membership_state'] for partner in partners}
            
        # Add membership_state to each service record based on member_type
        for record in service_records:
            if record.get('member_type') in ['credit', 'adhoc']:
                record['membership_state'] = 'confirm'
            elif record.get('member_type') == 'policy' and record.get('member_id'):
                record['membership_state'] = member_states.get(record['member_id'][0], '')



             # Fetch the latest service comment
            service_comment = self.env['service.comment'].search([
                ('service_id', '=', record['id']),
                ('comment_status', '=', record['state'])
            ], order="create_date desc", limit=1)

            # Assign comment or fallback to import_comments
            record['Comments'] = service_comment.comment if service_comment and service_comment.comment else record.get('import_comments', '')
                
        return service_records
        
        
        
       
 
    def action_export_excel(self):
        buffer = io.BytesIO()
        service_records = self._fetch_service_records()
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
 
        worksheet.write('A3', 'Date Range:', metadata_label_format)
        worksheet.write('B3', date_range, metadata_value_format)
 
        worksheet.write('A4', 'Customer:', metadata_label_format)
        worksheet.write('B4', customer_name, metadata_value_format)
 
        worksheet.write('A5', 'Type:', metadata_label_format)
        worksheet.write('B5', type_name, metadata_value_format)
 
        worksheet.write('A6', 'Member Type:', metadata_label_format)
        worksheet.write('B6', member_type, metadata_value_format)
 
        # # Full headers
        # headers = [
        #     'Number', 'Service Date & Time', 'Created Date & Time', 'Customer Name', 'Category',
        #     'Membership Number', 'Member Name', 'Membership State', 'Mobile', 'Policy Number',
        #     'Member Type', 'Service Type', 'Vehicle Type', 'Vehicle Plate', 'In Progress Date and Time',
        #     'Service', 'Provider', 'Driver', 'Driver Mobile Number', 'From - Location',
        #     'To - Location',  *(['From Emirate'] if self.member_type in ['policy', 'adhoc'] else []), *(['To Emirate'] if self.member_type in ['policy', 'adhoc'] else []), 'From - Date', 'To - Date', 'Smart Tow ID', 'Status',
        #     'Agent', 'Dispatcher', 'Comments', 'Trip Sheet Number', 'Amount Collected', 'Rating', 'Rating Added By'
        # ]

        #  # Base headers without emirate columns
        # base_headers = [
        #     'Number', 'Service Date & Time', 'Created Date & Time', 'Customer Name', 'Category',
        #     'Membership Number', 'Member Name', 'Membership State', 'Mobile', 'Policy Number',
        #     'Member Type', 'Service Type', 'Vehicle Type', 'Vehicle Plate', 'Vehicle Chasis No.', 'In Progress Date and Time',
        #     'Service', 'Provider', 'Driver', 'Driver Mobile Number', 'From - Location',
        #     'To - Location'
        # ]
        
        # # Add emirate columns conditionally
        # if self.member_type in ['policy', 'adhoc']:
        #     base_headers.extend(['From Emirate', 'To Emirate'])
        
        # # Add remaining headers
        # base_headers.extend([
        #     'From - Date', 'To - Date', 'Smart Tow ID', 'Status',
        #     'Agent', 'Dispatcher', 'Comments', 'Trip Sheet Number', 'Amount Collected', 'Rating', 'Rating Added By'
        # ])

        # Base headers without emirate columns
        base_headers = [
            'Number', 'Service Date & Time', 'Created Date & Time', 'Customer Name', 'Category',
            'Membership Number', 'Member Name', 'Membership State', 'Mobile', 'Policy Number',
            'Member Type', 'Service Type', 'Vehicle Type', 'Vehicle Plate', 'Vehicle Chasis No.', 'In Progress Date and Time',
            'Service', 'Provider', 'Driver', 'Driver Mobile Number', 'Jafza Driver', 'After Duty', 'From - Location',
            'To - Location',
            'From Emirate', 'To Emirate',
            'From - Date', 'To - Date', 'Smart Tow ID', 'Status',
            'Agent', 'Comments', 'Trip Sheet Number', 'Amount Collected', 'Rating', 'Rating Added By', 'Dispatched By'
        ]

 
        # worksheet.write_row(7, 0, headers, header_format)
        worksheet.write_row(7, 0, base_headers, header_format)
 
        target_timezone = timezone('Asia/Dubai')
 
        for row_num, record in enumerate(service_records, start=8):
            service_time = record['service_time']
            create_date = record['create_date']
       

             # Get membership state for the member_id
            # member_id = record.get('member_id', [None])[0]  # Get the first element, member_id is a tuple
            # membership_state = partner_data.get(member_id, 'N/A')  # Get membership_state from partner_data     

            
 
            # Convert timestamps
            def convert_time(utc_dt):
                if utc_dt:
                    return UTC.localize(fields.Datetime.from_string(utc_dt)).astimezone(target_timezone).strftime('%d/%m/%Y %H:%M:%S')
                return ''
            
            
            
        

 
            # data = [
            #     record.get('name', ''),
            #     convert_time(service_time),
            #     convert_time(create_date),
            #     record.get('customer_id')[1] if record.get('customer_id') else '',
            #     record.get('sequence_id')[1] if record.get('sequence_id') else '',
            #     record.get('membership_num', ''),
            #     record.get('member_id')[1] if record.get('member_id') else '',
            #     #record.get('member_id')[1] if record.get('member_id') else '',  # Membership State
            #     record.get('membership_state', ''),
            #     record.get('member_contact_no', ''),
            #     record.get('policy_no', ''),
            #     # record.get('member_id')[1] if record.get('member_type') else '',  # Member Type
            #     record.get('member_type', ''),
            #     record.get('type', ''),
            #     record.get('vehicle_type', ''),
            #     record.get('vehicle_plate', ''),
            #     convert_time(record.get('date_time_from', '')),  # In Progress Date and Time
            #     record.get('product_id')[1] if record.get('product_id') else '',
            #     record.get('provider_id')[1] if record.get('provider_id') else '',
            #     record.get('driver_id')[1] if record.get('driver_id') else '',
            #     record.get('driver_num', ''),
            #     # record.get('from_location')[1] if record.get('from_location') else '',
            #     record.get('selected_from_location')[1] if (record.get('selected_from_location') and record.get('member_type') in ['policy', 'adhoc']) else (
            #     record.get('from_location')[1] if record.get('from_location') else ''
            # ),

                
            #     # record.get('to_location')[1] if record.get('to_location') else '',
            #     record.get('selected_to_location')[1] if (record.get('selected_to_location') and record.get('member_type')in ['policy', 'adhoc']) else (
            #     record.get('to_location')[1] if record.get('to_location') else ''
            # ),
            #     record.get('from_location_emirate', ''),

            #     record.get('to_location_emirate', ''),

            #     convert_time(record.get('date_time_from', '')),
            #     convert_time(record.get('date_time_to', '')),
            #     record.get('smarto_id', ''),
            #     record.get('state', ''),
            #     # record.get('provider_id')[1] if record.get('provider_id') else '',  # Agent
            #     # record.get('provider_id')[1] if record.get('provider_id') else '',  # Dispatcher
            #     record.get('create_uid')[1] if record.get('create_uid') else '',  # Agent
            #     record.get('dispatcher_from_history')[1] if record.get('dispatcher_from_history') else '',  # Dispatcher
            #     '',  # Comments placeholder
            #     record.get('credit_proforma_number', ''),
            #     record.get('cash_collected', 0.00),
            #     record.get('vendor_rating', 0),
            #     record.get('rating_user_id')[1] if record.get('rating_user_id') else ''
            # ]

             # Base data without emirate values
            base_data = [
                record.get('name', ''),
                convert_time(record.get('service_time')),
                convert_time(record.get('create_date')),
                record.get('customer_id')[1] if record.get('customer_id') else '',
                record.get('sequence_id')[1] if record.get('sequence_id') else '',
                record.get('membership_num', ''),
                record.get('member_id')[1] if record.get('member_id') else '',
                record.get('membership_state', ''),
                record.get('member_contact_no', ''),
                record.get('policy_no', ''),
                record.get('member_type', ''),
                record.get('type', ''),
                record.get('vehicle_type', ''),
                record.get('vehicle_plate', ''),
                record.get('vehicle_chasis_no', ''),
                convert_time(record.get('date_time_from', '')),
                record.get('product_id')[1] if record.get('product_id') else '',
                record.get('provider_id')[1] if record.get('provider_id') else '',
                # record.get('driver_id')[1] if record.get('driver_id') else '',
                record.get('driver_id')[1] if record.get('driver_id') else record.get('driver_name', ''),

                record.get('driver_num', ''),
                record.get('jafza_driver_id')[1] if record.get('jafza_driver_id') else record.get('jafza_driver_name', ''),
                #record.get('jafza_driver_id', '') if record.get('jafza_provider_id') == "ARABIAN AUTOMOBILE ASSOCIATION" else record.get('jafza_driver_name', ''),
                record.get('is_aditional_duty',''),

                record.get('selected_from_location')[1] if (record.get('selected_from_location') and record.get('member_type') in ['policy', 'adhoc']) else (
                    record.get('from_location')[1] if record.get('from_location') else ''
                ),
                record.get('selected_to_location')[1] if (record.get('selected_to_location') and record.get('member_type') in ['policy', 'adhoc']) else (
                    record.get('to_location')[1] if record.get('to_location') else ''
                ),
                record.get('from_location_emirate', ''),
                record.get('to_location_emirate', '')
            ]

            # Add emirate data conditionally
            # if self.member_type in ['policy', 'adhoc']:
            #     base_data.extend([
            #         record.get('from_location_emirate', ''),
            #         record.get('to_location_emirate', '')
            #     ])

            # Add remaining data
            base_data.extend([
                convert_time(record.get('date_time_from', '')),
                convert_time(record.get('date_time_to', '')),
                record.get('smarto_id', ''),
                record.get('state', ''),
                record.get('create_uid')[1] if record.get('create_uid') else '',
                # record.get('dispatcher_from_history')[1] if record.get('dispatcher_from_history') else '',  # Dispatcher
                record.get('Comments', ''),  # ✅ Fetch and write Comments here
                record.get('credit_proforma_number', ''),
                record.get('cash_collected', 0.00),
                record.get('vendor_rating', 0),
                record.get('rating_user_id')[1] if record.get('rating_user_id') else '',
                record.get('dispatch_done_by')[1] if record.get('dispatch_done_by') else ''
            ])
 
        #     worksheet.write_row(row_num, 0, data, data_format)
 
        # worksheet.set_column(0, len(headers) - 1, 20)

            worksheet.write_row(row_num, 0, base_data, data_format)

        worksheet.set_column(0, len(base_headers) - 1, 20)
        workbook.close()
        buffer.seek(0)
 
        attachment = self.env['ir.attachment'].create({
            'name': 'Service_Report.xlsx',
            'datas': base64.b64encode(buffer.getvalue()),
            'type': 'binary',
        })
 
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'res_id': attachment.id,
            'view_mode': 'form',
            'target': 'new',
        }
 