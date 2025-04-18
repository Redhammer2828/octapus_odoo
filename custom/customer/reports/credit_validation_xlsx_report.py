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

        sheet.set_column(0, 0, 20)  
        sheet.set_column(1, 1, 30) 
        sheet.set_column(2, 2, 20)  
        sheet.set_column(3, 3, 25)  
        sheet.set_column(4, 4, 20)  
        sheet.set_column(5, 5, 30) 
        sheet.set_column(6, 6, 30)  
        sheet.set_column(7, 7, 30)  
        sheet.set_column(8, 8, 15)  
        

        sheet.merge_range('A1:I1', "SERVICE STATEMENT", title_format)

        headers = [
            "Service Date", "Service Number", "Trip Sheet No.",
            "Vehicle Model", "Vehicle Plate", "Product",
            "From Location", "To Location", "Price"
        ]

        for col, header in enumerate(headers):
            sheet.write(3, col, header, header_format)

        row = 4
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
                sheet.write(row, 8, rec.price)
                row += 1

            to_location_index = headers.index('To Location')
            price_index = headers.index('Price')
            sheet.write(row, to_location_index, 'Taxable Amount', total_format)
            sheet.write(row, price_index, line.taxable_amount, total_format)
            sheet.write(row+1, to_location_index, 'VAT 5%', total_format)
            sheet.write(row+1, price_index, line.vat, total_format)
            sheet.write(row+2, to_location_index, 'Total', total_format)
            sheet.write(row+2, price_index, line.total_amount, total_format)
