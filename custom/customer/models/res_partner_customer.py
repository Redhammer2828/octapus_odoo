#model/res_partner_customer.py
from odoo import fields, models ,api

class ResPartnerCustomer(models.Model):
    _inherit = 'res.partner'
    _description = 'Customer Information'

    customer_code = fields.Char(string='Code', tracking=True)
    function = fields.Char(string='Function', tracking=True)
    customer_timeline_ids = fields.One2many('membership.timeline', 'member_id', string='Timeline', readonly=True)

    member_count = fields.Integer(compute='_compute_member_count', string='Member Count')
    customer_service_count = fields.Integer(
        compute='_compute_service_count',
        string="Service Count",
        store=False
    )

    property_product_pricelist_id = fields.Many2one('product.pricelist', string='Price List', tracking=True)

    property_product_pricelist_id_vendor = fields.Many2one(
        'product.pricelist',
        string='Vendor Pricelist',
        domain="[('is_vendor', '=', True)]",
        tracking=True,
    )

    customer = fields.Binary('customer')  #Field (Flag) for Members (is_customer)

    #Page - Category
    customer_category_ids = fields.One2many('partner.category', 'partner_id', string='Customer Categories')

    invoicing_policy = fields.Selection([ ('individual', 'Individual'),
                                    ('consolidated', 'Consolidated') ], string='Invoicing Policy', tracking=True)
    
    trn_number = fields.Char('TRN Number', tracking=True)
          # Set the default value here
    #Action for Member Button
    def action_view_member(self):
        return {
            'name': 'Members',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('parent_customer_id', '=', self.id), ('is_customer','=',True)],
            'context': {
                'from_res_partner_member_form': True,
                'default_parent_customer_id': self.id,  # Pre-select the parent customer
            },
            'views': [(self.env.ref('customer.res_partner_member_tree').id, 'tree'),
                    (self.env.ref('customer.res_partner_member_form').id, 'form')],
            # Add any other action parameters as needed
        }

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if record.is_company:
            self.env['membership.timeline'].create({
                'member_id': record.id,
                'user': self.env.user.id,
                'time': fields.Datetime.now(),
                'status': 'Created',
                'timeline_status': 'confirm',
            })
        return record

    def write(self, vals):
        records_old = {}
        for rec in self:
            records_old[rec.id] = {}
            for field_name in vals.keys():
                if field_name in rec._fields:
                    records_old[rec.id][field_name] = rec[field_name]
        res = super().write(vals)
        for rec in self:
            if rec.is_company:
                pieces = []
                for field_name, new_val in vals.items():
                    if field_name not in rec._fields:
                        continue
                    field = rec._fields[field_name]
                    old_val = records_old.get(rec.id, {}).get(field_name)
                    old_disp = self._format_timeline_value(field, old_val)
                    new_disp = self._format_timeline_value(field, rec[field_name])
                    if old_disp != new_disp:
                        pieces.append(f"{field.string}: {old_disp} → {new_disp}")
                status = 'Updated' if not pieces else 'Updated: ' + '; '.join(pieces)
                self.env['membership.timeline'].create({
                    'member_id': rec.id,
                    'user': self.env.user.id,
                    'time': fields.Datetime.now(),
                    'status': status,
                    'timeline_status': 'confirm',
                })
        return res

    def _format_timeline_value(self, field, value):
        if field.type == 'many2one':
            if value:
                if isinstance(value, models.BaseModel):
                    return value.display_name
                else:
                    return self.env[field.comodel_name].browse(value).display_name if value else False
            return ''
        if field.type == 'selection':
            if value is False or value is None:
                return ''
            sel = dict(field.selection)
            return sel.get(value, str(value))
        if field.type in ('one2many', 'many2many'):
            return ''
        if value is False or value is None:
            return ''
        return str(value)

    #For Calculating Count of Memnbers
    @api.depends('parent_customer_id')
    def _compute_member_count(self):
        for record in self:
            if record.id:
                member_count = self.env['res.partner'].search_count([('parent_customer_id', '=', record.id)])
                record.member_count = member_count
            else:
                record.member_count = 0

    def action_view_customer_service(self):
        return {
            'name': 'Services',
            'type': 'ir.actions.act_window',
            'res_model': 'aaa.service',
            'view_mode': 'tree,form',
            'domain': [('customer_id', '=', self.id)],
            'context': {
                'from_res_partner_member_form': True,
                'default_parent_customer_id': self.id,  # Pre-select the parent customer
            },
            'views': [
                (self.env.ref('customer.call_center_all_service_view_tree').id, 'tree'),
                (self.env.ref('customer.call_center_service_form').id, 'form'),
            ],
        }

    @api.depends('customer')  # Triggered by changes to the partner record
    def _compute_service_count(self):
        for partner in self:
            # Count the number of `aaa.service` records related to this partner
            partner.customer_service_count = self.env['aaa.service'].search_count([
                ('customer_id', '=', partner.id)
            ])

    def waive_off_history(self):
        pass

    def duplicate_record(self):
        self.ensure_one()
        duplicate_record = self.copy()
        view_id = self.env.ref('customer.res_partner_customer_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Duplicate Record',
            'res_model': self._name,
            'res_id': duplicate_record.id,
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
        }

class PartnerCategory(models.Model):
    _name = 'partner.category'
    _description = 'Partner Category'
    _rec_name = 'description'

    partner_id = fields.Many2one('res.partner', string='Partner', inverse_name='customer_category_ids')

    name = fields.Char(string="Code")
    member_type = fields.Selection([
        ('policy', 'Policy'),
        ('credit', 'Credit'),
        ('adhoc', 'Adhoc')],
        string='Type')
    description = fields.Text(string="Description")
    default_member = fields.Many2one('res.partner',String="Default Member")
