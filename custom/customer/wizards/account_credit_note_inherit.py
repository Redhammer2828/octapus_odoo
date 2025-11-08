from odoo import models, fields, api

class AccountMoveReversalInherit(models.TransientModel):
    _inherit = 'account.move.reversal'

    def refund_moves(self):
        """
        Override refund_moves to clear invoice lines from credit notes
        """
        action = super(AccountMoveReversalInherit, self).refund_moves()
        
        # Clear invoice lines from the newly created credit notes
        if self.new_move_ids:
            for move in self.new_move_ids:
                # Set move to draft if needed to allow modifications
                if move.state == 'posted':
                    move.button_draft()
                
                # Remove invoice lines
                if move.invoice_line_ids:
                    move.invoice_line_ids.unlink()
                
                # Note: The move will remain in draft state for manual entry
        
        return action
    
    def _prepare_default_reversal(self, move):
        vals = super()._prepare_default_reversal(move)

        vals.update({
            'original_invoice_number': move.name, 
        })
        return vals