import os
from odoo import models

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'
    
    def _run_wkhtmltopdf(self, bodies, **kwargs):
        # Check environment variable
        if os.environ.get('ODOO_PLATFORM') == 'linux':
            specific_paperformat_args = kwargs.get('specific_paperformat_args', {})
            specific_paperformat_args.update({
                '--disable-smart-shrinking': '',
                '--zoom': '1',
            })
            kwargs['specific_paperformat_args'] = specific_paperformat_args
        
        return super()._run_wkhtmltopdf(bodies, **kwargs)