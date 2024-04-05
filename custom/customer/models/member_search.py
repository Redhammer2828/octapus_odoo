from odoo import fields, models

class MemberSearch(models.Model):
    _name = 'member.search'
    _description = 'Member Search Form'

    policy_no = fields.Char(string="Policy")
    vehicle_chasis_no = fields.Char(string="Chasis Number")
    ref_num = fields.Char(string="Membership")
    mobile = fields.Char(string="Mobile")
    email = fields.Char(string="Email")
    old_membership_number = fields.Char(string="Old Membership Number")
    vehicle_plate = fields.Char(string="Plate Number")
    member_name = fields.Char(string="Member Name")
    customer_id = fields.Many2one('res.partner', string="Customer", domain="[('is_company', '=', True), ('customer', '=', True)]")

    def search_member(self):
        partner_obj = self.env['res.partner']
        search_domain = []

        # Build the search domain based on the user-entered criteria
        if self.policy_no:
            search_domain.append(('policy_no', 'ilike', self.policy_no))
        if self.ref_num:
            search_domain.append(('ref_num', 'ilike', self.ref_num))
        if self.mobile:
            search_domain.append(('mobile', 'ilike', self.mobile))
        if self.email:
            search_domain.append(('email', 'ilike', self.email))
        if self.old_membership_number:
            search_domain.append(('old_membership_number', 'ilike', self.old_membership_number))
        if self.vehicle_chasis_no:
            search_domain.append(('vehicle_chasis_no', 'ilike', self.vehicle_chasis_no))
        if self.vehicle_plate:
            search_domain.append(('vehicle_plate', 'ilike', self.vehicle_plate))
        if self.member_name:
            search_domain.append(('name', 'ilike', self.member_name))
        if self.customer_id:
            search_domain.append(('id', '=', self.customer_id.id))

        # Search for partners based on the search domain
        partner_ids = partner_obj.search(search_domain)

        # Open the tree view with the search results
        return {
            'name': 'Policy Member Search Results',
            'view_mode': 'tree,form',
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', partner_ids.ids)],
            'views': [(self.env.ref('customer.policy_member_search_view_tree').id, 'tree')],
        }