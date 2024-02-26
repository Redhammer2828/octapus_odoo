#model/res_partner_customer.py
from odoo import fields,models,api

class ResPartnerCustomer(models.Model):
    _inherit = 'res.partner'
    _description = 'Customer Information'

    customer_code = fields.Char(string='Customer Code')
    function = fields.Char(string='Function')

    members_count = fields.Integer(compute='_compute_members_count', string='Member Count')

    customer = fields.Binary('customer')

    def action_view_member(self):
        return {
            'name': 'Members',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('parent_customer_id', '=', self.id), ('is_customer','=',True)],
            'context': {'from_res_partner_member_form': True},
            'views': [(self.env.ref('customer.res_partner_member_tree').id, 'tree'),
                    (self.env.ref('customer.res_partner_member_form').id, 'form')],
            # Add any other action parameters as needed
        }


    def _compute_members_count(self):
        # Retrieve all children partners and prefetch 'parent_id' on them
        all_partners = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
        
        # Group partners by parent_id and count members
        member_groups = all_partners.read_group(
            domain=[('member_id', 'in', all_partners.ids)],
            fields=['member_id'],
            groupby=['member_id']
        )
        
        # Assign member count to each partner
        for partner in self:
            partner.member_count = sum(group['member_id_count'] for group in member_groups if group['member_id'][0] == partner.id)
