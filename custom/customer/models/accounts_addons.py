from odoo import models, fields

class AccountAccount(models.Model):
    _inherit = "account.account"

    parent_chart_account = fields.Many2one(
        'account.account',
        string="Parent Chart Account",
        domain="[('id', '!=', id)]",
        ondelete="set null",
        help="Defines the parent account for hierarchical structuring of the chart of accounts."
    )
