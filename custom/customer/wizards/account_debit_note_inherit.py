from odoo import models, fields, api

class AccountMoveReversalInherit(models.TransientModel):
    _inherit = 'account.debit.note'

    def _prepare_default_values(self, move):
        vals = super()._prepare_default_values(move)

        vals.update({
            'original_invoice_number': move.name, 
        })
        return vals