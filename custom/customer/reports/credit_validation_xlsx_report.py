from odoo import models


class CreditValidationXlsx(models.AbstractModel):
    _name = 'report.customer.credit_validation_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        sheet = workbook.add_worksheet('Service Statement')

        bold_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#00007A',
            'color': 'white'
        })

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center'
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

        date_format = workbook.add_format({
            'num_format': 'dd-mm-yyyy',
            'align': 'left'
        })

        datetime_format = workbook.add_format({
            'num_format': 'dd-mm-yyyy hh:mm',
            'align': 'left'
        })

        # Check if any service has rental car products to determine if extra columns are needed
        has_rental_car = any(
            rec.service_product in ["RENT A CAR", "RENT A CAR - UPGRADE"]
            for line in lines
            for rec in line.service_line_ids
        )

        # Set column widths based on whether rental car columns are needed
        if has_rental_car:
            sheet.set_column(0, 0, 20)   # Service Date
            sheet.set_column(1, 1, 30)   # Service Number
            sheet.set_column(2, 2, 20)   # Trip Sheet No.
            sheet.set_column(3, 3, 25)   # Vehicle Model
            sheet.set_column(4, 4, 20)   # Vehicle Plate
            sheet.set_column(5, 5, 30)   # Product
            sheet.set_column(6, 6, 30)   # From Location
            sheet.set_column(7, 7, 30)   # To Location
            sheet.set_column(8, 8, 25)   # Date Time From
            sheet.set_column(9, 9, 25)   # Date Time To
            sheet.set_column(10, 10, 15) # Quantity
            sheet.set_column(11, 11, 15) # Price
        else:
            sheet.set_column(0, 0, 20)   # Service Date
            sheet.set_column(1, 1, 30)   # Service Number
            sheet.set_column(2, 2, 20)   # Trip Sheet No.
            sheet.set_column(3, 3, 25)   # Vehicle Model
            sheet.set_column(4, 4, 20)   # Vehicle Plate
            sheet.set_column(5, 5, 30)   # Product
            sheet.set_column(6, 6, 30)   # From Location
            sheet.set_column(7, 7, 30)   # To Location
            sheet.set_column(8, 8, 15)   # Price

        # Set title merge range based on number of columns
        title_range = 'A1:L1' if has_rental_car else 'A1:I1'
        sheet.merge_range(title_range, "SERVICE STATEMENT", title_format)

        # Add customer information rows
        info_format = workbook.add_format({
            'bold': True,
            'align': 'left',
            'valign': 'vcenter'
        })
        
        # Assuming we're working with the first line for customer info
        for line in lines:
            sheet.write('A2', 'Customer:', info_format)
            sheet.write('B2', line.partner_id.name if line else '', info_format)
            
            sheet.write('A3', 'From Date:', info_format)
            sheet.write('B3', line.from_date if line else '', date_format)
            
            sheet.write('A4', 'To Date:', info_format)
            sheet.write('B4', line.to_date if line else '', date_format)

        # Define headers based on whether rental car columns are needed
        if has_rental_car:
            headers = [
                "Service Date", "Service Number", "Trip Sheet No.",
                "Vehicle Model", "Vehicle Plate", "Product",
                "From Location", "To Location", "Date From",
                "Date To", "Quantity", "Price"
            ]
        else:
            headers = [
                "Service Date", "Service Number", "Trip Sheet No.",
                "Vehicle Model", "Vehicle Plate", "Product",
                "From Location", "To Location", "Price"
            ]

        # Write headers (now starting from row 6 instead of row 4)
        for col, header in enumerate(headers):
            sheet.write(6, col, header, header_format)

        row = 7  # Start data from row 7
        for line in lines:
            for rec in line.service_line_ids:
                sheet.write(row, 0, rec.service_date or '', date_format)
                sheet.write(row, 1, rec.service_number or '')
                sheet.write(row, 2, rec.trip_sheet_number or '')
                sheet.write(row, 3, rec.vehicle_model or '')
                sheet.write(row, 4, rec.vehicle_plate or '')
                sheet.write(row, 5, rec.service_product or '')
                sheet.write(row, 6, rec.from_location or '')
                sheet.write(row, 7, rec.to_location or '')
                
                if has_rental_car:
                    # Add rental car specific columns
                    if rec.service_product in ["RENT A CAR", "RENT A CAR - UPGRADE"]:
                        sheet.write(row, 8, rec.date_time_from or '', datetime_format)
                        sheet.write(row, 9, rec.date_time_to or '', datetime_format)
                        sheet.write(row, 10, rec.quantity or '')
                    else:
                        # Leave rental car columns empty for non-rental services
                        sheet.write(row, 8, '')
                        sheet.write(row, 9, '')
                        sheet.write(row, 10, '')
                    sheet.write(row, 11, rec.price)
                else:
                    sheet.write(row, 8, rec.price)
                
                row += 1

            # Add totals section
            if has_rental_car:
                to_location_index = headers.index('To Location')
                price_index = headers.index('Price')
            else:
                to_location_index = headers.index('To Location')
                price_index = headers.index('Price')
                
            sheet.write(row, to_location_index, 'Taxable Amount', total_format)
            sheet.write(row, price_index, line.taxable_amount, total_format)
            sheet.write(row+1, to_location_index, 'VAT 5%', total_format)
            sheet.write(row+1, price_index, line.vat, total_format)
            sheet.write(row+2, to_location_index, 'Total', total_format)
            sheet.write(row+2, price_index, line.total_amount, total_format)
