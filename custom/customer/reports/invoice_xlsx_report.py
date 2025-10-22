from odoo import models


class ReportInvoiceXlsx(models.AbstractModel):
    _name = 'report.customer.invoice_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'


    def generate_xlsx_report(self, workbook, data, lines):
        # Guard
        if not lines:
            sheet = workbook.add_worksheet('Report')
            sheet.merge_range('A1:C1', 'No data', workbook.add_format({'align': 'center', 'bold': True}))
            return

        # Formats (create once)
        title_fmt = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'})
        header_fmt = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter',
                                        'bg_color': '#00007A', 'color': 'white'})
        info_fmt = workbook.add_format({'bold': True, 'align': 'left', 'valign': 'vcenter'})
        money_right = workbook.add_format({'num_format': '#,##0.00', 'align': 'right'})
        total_fmt = workbook.add_format({'bold': True, 'align': 'right', 'valign': 'vcenter', 'color': 'black'})

        # Fast string formatting for dates/datetimes
        from datetime import date, datetime

        def fmt_date(val):
            if isinstance(val, (date, datetime)):
                return val.strftime('%d-%m-%Y')
            return val or ''

        def fmt_dt(val):
            if isinstance(val, datetime):
                return val.strftime('%d-%m-%Y %H:%M')
            if isinstance(val, date):
                return val.strftime('%d-%m-%Y')
            return val or ''

        # Deterministic mode selection
        first = lines[0]
        inv_type = getattr(first, 'invoice_line_type', None)
        member_type = getattr(first, 'member_type', None)
        is_policy_mode = (inv_type == 'consolidated' and member_type == 'policy') or (inv_type == 'separate' and member_type == 'policy')
        is_credit_mode = (inv_type == 'consolidated' and member_type == 'credit')

        # Common info block
        def write_info_block(sheet):
            w = sheet.write
            partner_name = getattr(getattr(first, 'partner_id', None), 'name', '') or ''
            from_date_s = fmt_date(getattr(first, 'from_date', ''))
            to_date_s = fmt_date(getattr(first, 'to_date', ''))
            w('A2', 'Customer:', info_fmt)
            w('B2', partner_name, info_fmt)
            w('A3', 'From Date:', info_fmt)
            w('B3', from_date_s)
            w('A4', 'To Date:', info_fmt)
            w('B4', to_date_s)

        if is_policy_mode:
            # MEMBERSHIP DETAILS with INVOICE DATE after EXPIRY DATE
            sheet = workbook.add_worksheet('Membership Details')
            w, wn, wr = sheet.write, sheet.write_number, sheet.write_row

            # Column widths aligned to new order:
            # NAME, PLATE, CHASSIS, POLICY, START, EXPIRY, INVOICE DATE, CAR MAKE, AMOUNT
            # Amount at index 8 keeps money format
            widths = [24, 14, 20, 18, 14, 14, 14, 16, 14]
            for idx, width in enumerate(widths):
                if idx == 8:
                    sheet.set_column(idx, idx, width, money_right)
                else:
                    sheet.set_column(idx, idx, width)

            # Title and info
            sheet.merge_range('A1:I1', 'MEMBERSHIP DETAILS', title_fmt)
            write_info_block(sheet)

            # Headers reflect new position of INVOICE DATE (index 6)
            headers = [
                'NAME', 'PLATE NO.', 'CHASSIS NO.',
                'POLICY NO.', 'START DATE', 'EXPIRY DATE',
                'INVOICE DATE', 'CAR MAKE', 'AMOUNT'
            ]
            header_row = 6
            for c, h in enumerate(headers):
                w(header_row, c, h, header_fmt)
            sheet.freeze_panes(header_row + 1, 0)

            row = header_row + 1
            max_rows = 1_000_000
            sheet_idx = 1

            for line in lines:
                for rec in getattr(line, 'policy_membership_line_ids', []):
                    if row >= max_rows:
                        # New chunked sheet
                        sheet_idx += 1
                        sheet = workbook.add_worksheet(f'Membership {sheet_idx}')
                        w, wn, wr = sheet.write, sheet.write_number, sheet.write_row
                        for idx, width in enumerate(widths):
                            if idx == 8:
                                sheet.set_column(idx, idx, width, money_right)
                            else:
                                sheet.set_column(idx, idx, width)
                        sheet.merge_range('A1:I1', 'MEMBERSHIP DETAILS', title_fmt)
                        write_info_block(sheet)
                        for c, h in enumerate(headers):
                            w(header_row, c, h, header_fmt)
                        sheet.freeze_panes(header_row + 1, 0)
                        row = header_row + 1

                    name = getattr(rec, 'name', '') or ''
                    plate_no = getattr(rec, 'plate_no', '') or ''
                    chasis_no = getattr(rec, 'chasis_no', '') or ''
                    policy_no = getattr(rec, 'policy_no', '') or ''
                    start_s = fmt_date(getattr(rec, 'start_date', ''))
                    expiry_s = fmt_date(getattr(rec, 'expiry_date', ''))
                    invoice_date_s = fmt_date(getattr(rec, 'invoice_ref_date', ''))
                    car_make = getattr(rec, 'car_make', '') or ''
                    amount = getattr(rec, 'amount', 0.0) or 0.0

                    # INVOICE DATE is written before CAR MAKE per new order
                    wr(row, 0, [
                        name, plate_no, chasis_no,
                        policy_no, start_s, expiry_s,
                        invoice_date_s, car_make, amount
                    ])
                    row += 1
            return

        if is_credit_mode:
            # SERVICE STATEMENT (unchanged)
            sheet = workbook.add_worksheet('Service Statement')
            w, wn, wr = sheet.write, sheet.write_number, sheet.write_row

            widths = [20, 30, 20, 25, 20, 30, 30, 30, 25, 25, 15, 15]
            for idx, width in enumerate(widths):
                if idx == 11:
                    sheet.set_column(idx, idx, width, money_right)
                else:
                    sheet.set_column(idx, idx, width)

            sheet.merge_range('A1:L1', 'SERVICE STATEMENT', title_fmt)
            write_info_block(sheet)

            headers = [
                "Service Date", "Service Number", "Trip Sheet No.",
                "Vehicle Model", "Vehicle Plate", "Product",
                "From Location", "To Location", "Date From",
                "Date To", "Quantity", "Price"
            ]
            header_row = 6
            for c, h in enumerate(headers):
                w(header_row, c, h, header_fmt)
            sheet.freeze_panes(header_row + 1, 0)

            row = header_row + 1
            max_rows = 1_000_000
            sheet_idx = 1

            for line in lines:
                taxable = getattr(line, 'taxable_amount', 0.0) or 0.0
                vat = getattr(line, 'vat', 0.0) or 0.0
                total = getattr(line, 'total_amount', 0.0) or 0.0

                for rec in getattr(line, 'credit_service_line_ids', []):
                    if row >= max_rows:
                        sheet_idx += 1
                        sheet = workbook.add_worksheet(f'Services {sheet_idx}')
                        w, wn, wr = sheet.write, sheet.write_number, sheet.write_row
                        for idx, width in enumerate(widths):
                            if idx == 11:
                                sheet.set_column(idx, idx, width, money_right)
                            else:
                                sheet.set_column(idx, idx, width)
                        sheet.merge_range('A1:L1', 'SERVICE STATEMENT', title_fmt)
                        write_info_block(sheet)
                        for c, h in enumerate(headers):
                            w(header_row, c, h, header_fmt)
                        sheet.freeze_panes(header_row + 1, 0)
                        row = header_row + 1

                    service_date_s = fmt_date(getattr(rec, 'service_date', ''))
                    sn = getattr(getattr(rec, 'service_number_id', None), 'name', '') or ''
                    trip = getattr(rec, 'trip_sheet_number', '') or ''
                    v_model = getattr(rec, 'vehicle_model', '') or ''
                    v_plate = getattr(rec, 'vehicle_plate', '') or ''
                    prod_name = getattr(getattr(rec, 'service_product_id', None), 'name', '') or ''
                    from_loc = getattr(getattr(rec, 'from_location_id', None), 'name', '') or ''
                    to_loc = getattr(getattr(rec, 'to_location_id', None), 'name', '') or ''
                    is_rental = getattr(rec, 'service_product', '') in ("RENT A CAR", "RENT A CAR - UPGRADE")
                    dt_from_s = fmt_dt(getattr(rec, 'date_time_from', '')) if is_rental else ''
                    dt_to_s = fmt_dt(getattr(rec, 'date_time_to', '')) if is_rental else ''
                    qty = getattr(rec, 'quantity', '') if is_rental else ''
                    price = getattr(rec, 'price', 0.0) or 0.0

                    wr(row, 0, [
                        service_date_s, sn, trip,
                        v_model, v_plate, prod_name,
                        from_loc, to_loc, dt_from_s,
                        dt_to_s, qty, price
                    ])
                    row += 1

                w(row, 7, 'Taxable Amount', total_fmt)
                wn(row, 11, taxable)
                w(row + 1, 7, 'VAT 5%', total_fmt)
                wn(row + 1, 11, vat)
                w(row + 2, 7, 'Total', total_fmt)
                wn(row + 2, 11, total)
                row += 3

            return

        # Should not reach here if defaults guarantee a mode
        sheet = workbook.add_worksheet('Report')
        sheet.merge_range('A1:C1', 'Unsupported mode', workbook.add_format({'align': 'center', 'bold': True}))

