from odoo import models, fields, api
import pytz
from itertools import chain
import io
import base64
import textwrap
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import inch
from datetime import datetime, timedelta
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from datetime import datetime, time
import base64, io
from collections import defaultdict
import logging
import json

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    member_type = fields.Selection([ ('policy', 'Policy Member'),
                                    ('credit', 'Credit Member') ], string='Member Type', default="policy")
    category_id = fields.Many2one('partner.category', 
                                  string="Customer Category",
                                  domain="[('partner_id','=', partner_id),('member_type','=',member_type)]")

    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    invoice_line_type = fields.Selection([ ('consolidated', 'Consolidated Invoice'),
                                          ('separate', 'Separate Invoice')], string='Invoice Type', default="consolidated")
    product_ids = fields.Many2many('product.template','product_service_rel', 'product_id', 'service_id', string="Product Ids")
    product_id = fields.Many2one('product.template', string="Package", domain="product_domain_char")
    service_ids = fields.Many2many('aaa.service', 'service_service_rel', 'invoice_id', 'service_id')
    service_id = fields.Many2one('aaa.service', string="Service", domain="service_domain_char")
    credit_service_line_ids = fields.One2many("credit.service.line", "credit_invoice_id", string="Services")
    policy_membership_line_ids = fields.One2many("policy.membership.line", "policy_invoice_id", string="Memberships")
    company_seal = fields.Binary(string="Stamp Image")
    is_rent_a_car = fields.Boolean(string="Is Rent a Car Service", default=False)
    debit_note_number = fields.Char(string="Debit Note Number", copy=False, readonly=True)
    reference_invoice_ids = fields.Many2many('account.move', 'reference_invoice_rel', 'credit_note_id', 'invoice_id', string="Reference Invoices", domain="[('move_type','=','out_invoice'), ('state','=','posted'), ('partner_id','=',partner_id)]")

    # Computed domain holders (Char) consumed by the XML view’s domain=""
    product_domain_char = fields.Char(compute="_compute_dynamic_domains", store=False)
    service_domain_char = fields.Char(compute="_compute_dynamic_domains", store=False)
    original_invoice_number = fields.Char(string="Original Invoice Number", readonly=True)
    

    def _get_last_sequence_domain(self, relaxed=False):
        where_string, param = super()._get_last_sequence_domain(relaxed)
        # Separate sequences for debit notes and regular invoices
        if self.debit_origin_id:
            where_string += " AND debit_origin_id IS NOT NULL"
        else:
            where_string += " AND debit_origin_id IS NULL"
        return where_string, param
    

    def _get_starting_sequence(self):
        # EXTENDS account sequence.mixin
        starting_sequence = super()._get_starting_sequence()
        # Add "D" prefix for debit notes (similar to "R" for credit notes)
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info(f"=== DEBIT NOTE DEBUG ===")
        _logger.info(f"Move ID: {self.id}")
        _logger.info(f"Move Name: {self.name}")
        _logger.info(f"Move Type: {self.move_type}")
        _logger.info(f"Debit Origin ID: {self.debit_origin_id}")
        _logger.info(f"Debit Origin ID Value: {self.debit_origin_id.id if self.debit_origin_id else False}")
        _logger.info(f"Has Debit Origin: {bool(self.debit_origin_id)}")
        _logger.info(f"Starting Sequence Before: {starting_sequence}")
        
        if self.debit_origin_id and self.move_type in ('out_invoice', 'in_invoice'):
            starting_sequence = "D" + starting_sequence
            _logger.info(f"Starting Sequence After (with D): {starting_sequence}")
        else:
            _logger.info(f"NOT adding D prefix - debit_origin_id: {bool(self.debit_origin_id)}, move_type: {self.move_type}")
        
        return starting_sequence

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'res.company'),
            ('res_id', '=', self.env.company.id),
            ('name', '=', 'aaa_seal.jpg')
        ], limit=1)
        if attachment:
            res.company_seal = attachment.datas
        return res
    

    def action_post(self):
        result = super().action_post()
        for record in self:
            if record.move_type == 'out_refund' and record.member_type == 'policy':
                if record.policy_membership_line_ids and record.reference_invoice_ids:
                    self.env['res.partner'].search([
                        ('invoice_id', 'in', record.reference_invoice_ids.ids),
                        ('issue_credit_note', '=', True),
                    ]).write({'issue_credit_note': False})

            elif record.move_type == 'out_invoice' and record.member_type == 'policy' and record.debit_origin_id:
                if record.policy_membership_line_ids:
                    self.env['res.partner'].search([
                        ('invoice_id', '=', record.debit_origin_id.id),
                        ('issue_debit_note', '=', True),
                    ]).write({'issue_debit_note': False})

            else:
                if record.invoice_line_type == 'separate':
                    if record.member_type == 'credit' and record.service_id:
                        record.service_id.write({
                            'invoice_state': 'invoiced',
                            'invoiced_by': self.env.user.id,
                            'invoiced_date': record.invoice_date,
                            'invoice_id': record.id,
                        })
                else:
                    if record.member_type == 'credit':
                        credit_services = record.credit_service_line_ids.mapped('service_number_id')
                        print("=== CREDIT SERVICES TO UPDATE ===", credit_services)
                        if credit_services:
                            # Add explicit checks
                            if not record.exists():
                                continue
                            
                            credit_services.write({
                                'invoice_state': 'invoiced',
                                'invoiced_by': self.env.user.id,
                                'invoiced_date': record.invoice_date or False,
                                'invoice_id': record.id,
                            })
                    else:
                        # POLICY path: optimized batch updates
                        self._update_policy_records_optimized(record)

        return result



    def _update_policy_records_optimized(self, record):
        """
        Optimized batch update for policy membership records (partners and renewal queue only).
        Uses chunked writes or SQL for performance on large datasets.
        """
        base_domain = [
            ('invoice_ref_date', '>=', record.from_date),
            ('invoice_ref_date', '<=', record.to_date),
            ('member_partner_category_id', '=', record.category_id.id),
            ('member_type', '=', record.member_type),
            ('invoice_state', '=', 'not_invoiced'),
        ]
        
        vals = {
            'invoice_state': 'invoiced',
            'invoiced_by': self.env.user.id,
            'invoice_id': record.id,
        }
        
        # Update partners with optimized batch processing
        try:
            partner_domain = base_domain + [
                ('parent_customer_id', '=', record.partner_id.id),
            ('membership_state', '=', 'confirm'),
            ]
            partners = self.env['res.partner'].search(partner_domain)
            
            if partners:
                count = len(partners)
                _logger.info(f"Updating {count} partner records for invoice {record.name}")
                
                if count > 1000:
                    # Use direct SQL for large datasets
                    self._sql_batch_update('res_partner', partners.ids, vals)
                elif count > 500:
                    # Use chunked ORM for medium datasets
                    self._chunked_write(partners, vals, chunk_size=500)
                else:
                    # Direct write for small datasets
                    partners.write(vals)
        except Exception as e:
            _logger.error(f"Error updating partners: {e}", exc_info=True)
        
        # Update renewal queue (unchanged)
        try:
            renewal_domain = [
                ('member_id.renewal_in_queue', '=', True),
                ('invoice_ref_date', '>=', record.from_date),
                ('invoice_ref_date', '<=', record.to_date),
                ('member_partner_category_id', '=', record.category_id.id),
                ('invoice_state', '=', 'not_invoiced'),
            ]
            renewals = self.env['renewal.queue.data'].search(renewal_domain)
            
            if renewals:
                count = len(renewals)
                _logger.info(f"Updating {count} renewal queue records for invoice {record.name}")
                
                if count > 1000:
                    self._sql_batch_update('renewal_queue_data', renewals.ids, vals)
                elif count > 500:
                    self._chunked_write(renewals, vals, chunk_size=500)
                else:
                    renewals.write(vals)
        except Exception as e:
            _logger.error(f"Error updating renewal queue: {e}", exc_info=True)


    def _sql_batch_update(self, table_name, record_ids, vals):
        """
        Perform batch update using direct SQL for maximum performance.
        Falls back to chunked ORM if SQL fails.
        """
        try:
            if not record_ids:
                return
            
            set_parts = []
            params = []
            for field, value in vals.items():
                set_parts.append(f"{field} = %s")
                params.append(value)
            params.append(tuple(record_ids))
            
            query = f"""
                UPDATE {table_name}
                SET {', '.join(set_parts)}
                WHERE id IN %s
            """
            self.env.cr.execute(query, params)
            _logger.info(f"SQL batch update completed: {len(record_ids)} records in {table_name}")
        except Exception as e:
            _logger.warning(f"SQL update failed for {table_name}, falling back to chunked ORM: {e}")
            model_name = table_name.replace('_', '.')
            if model_name in self.env:
                records = self.env[model_name].browse(record_ids)
                self._chunked_write(records, vals)


    def _chunked_write(self, records, vals, chunk_size=500):
        """
        Write records in chunks to prevent memory overflow and timeouts.
        """
        if not records:
            return
        
        total = len(records)
        chunks = (total + chunk_size - 1) // chunk_size
        _logger.info(f"Processing {total} records in {chunks} chunks of {chunk_size}")
        
        for i in range(0, total, chunk_size):
            try:
                chunk = records[i:i + chunk_size]
                chunk.write(vals)
                if total > 2000 and (i + chunk_size) % 2000 == 0:
                    _logger.info(f"Progress: {i + chunk_size}/{total} records updated")
            except Exception as e:
                _logger.error(f"Error updating chunk {i//chunk_size + 1}/{chunks}: {e}")
                continue



    # def action_post(self):
    #     result = super().action_post()
    #     for record in self:
    #         if record.move_type == 'out_refund' and record.member_type == 'policy':
    #             if record.policy_membership_line_ids and record.reference_invoice_ids:
    #                 # self._apply_credit_note_to_invoices(record)
    #                 self.env['res.partner'].search([
    #                     ('invoice_id', 'in', record.reference_invoice_ids.ids),
    #                     ('issue_credit_note', '=', True),
    #                 ]).write({'issue_credit_note': False})

    #         elif record.move_type == 'out_invoice' and record.member_type == 'policy' and record.debit_origin_id:
    #             if record.policy_membership_line_ids:
    #                 self.env['res.partner'].search([
    #                     ('invoice_id', '=', record.debit_origin_id.id),
    #                     ('issue_debit_note', '=', True),
    #                 ]).write({'issue_debit_note': False})

    #         else:
    #             if record.invoice_line_type == 'separate':
    #                 if record.member_type == 'credit' and record.service_id:
    #                     record.service_id.write({
    #                         'invoice_state': 'invoiced',
    #                         'invoiced_by': self.env.user.id,
    #                         'invoiced_date': record.invoice_date,
    #                         'invoice_id': record.id,
    #                     })
    #             else:
    #                 if record.member_type == 'credit':
    #                     credit_services = record.credit_service_line_ids.mapped('service_number_id')
    #                     if credit_services:
    #                         credit_services.write({
    #                             'invoice_state': 'invoiced',
    #                             'invoiced_by': self.env.user.id,
    #                             'invoiced_date': record.invoice_date,
    #                             'invoice_id': record.id,
    #                         })
    #                 else:
    #                     # POLICY path: build domains per model and write in batch
    #                     base_domain = [
    #                         ('invoice_ref_date', '>=', record.from_date),
    #                         ('invoice_ref_date', '<=', record.to_date),
    #                         ('member_partner_category_id', '=', record.category_id.id),
    #                         ('member_type', '=', record.member_type),
    #                         ('invoice_state', '=', 'not_invoiced'),
    #                     ]
    #                     partner_domain = base_domain + [
    #                         ('parent_customer_id', '=', record.partner_id.id),
    #                         ('membership_state', '=', 'confirm'),
    #                     ]

    #                     partners = self.env['res.partner'].search(partner_domain)
    #                     histories = self.env['membership.history'].search(
    #                         base_domain + [('parent_customer_id', '=', record.partner_id.id)]
    #                     )
    #                     renewals = self.env['renewal.queue.data'].search([
    #                         ('member_id.renewal_in_queue', '=', True),
    #                         ('invoice_ref_date', '>=', record.from_date),
    #                         ('invoice_ref_date', '<=', record.to_date),
    #                         ('member_partner_category_id', '=', record.category_id.id),
    #                         ('invoice_state', '=', 'not_invoiced'),
    #                         # add parent filter only if renewal has it; otherwise omit
    #                     ])

    #                     vals = {
    #                         'invoice_state': 'invoiced',
    #                         'invoiced_by': self.env.user.id,
    #                         'invoice_id': record.id,
    #                     }

    #                     if partners:
    #                         partners.write(vals)
    #                     if histories:
    #                         histories.write(vals)
    #                     if renewals:
    #                         renewals.write(vals)

    #     return result
    
    ########################################################################################################################################
  

    @api.onchange('from_date', 'to_date', 'partner_id', 'category_id', 'member_type', 'invoice_line_type')
    def _onchange_check_recompute_needed(self):
        # Check if recomputation is needed
        print("=== Onchange Check Recompute Needed Triggered ===")
        has_lines = (self.invoice_line_ids)
        
        if has_lines:
            
            # Optionally return a warning (without wizard)
            if self.invoice_line_type == 'consolidated':
                return {
                    'warning': {
                        'title': 'Recomputation Required',
                        'message': 'Field values have changed. Please click "Consolidated Invoice Lines" button to update invoice lines.'
                    }
                }
            
            else:
                return {
                    'warning': {
                        'title': 'Recomputation Required',
                        'message': 'Field values have changed. Please click "Add to Invoice Line" button to update invoice lines.'
                    }
                }

    @api.onchange('member_type', 'partner_id')
    def _onchange_member_type(self):
        if self.member_type and self.partner_id:
            domain = [
                ('partner_id', '=', self.partner_id.id),
                ('member_type', '=', self.member_type)
            ]
            first_category = self.env['partner.category'].search(domain, limit=1)
            self.category_id = first_category.id if first_category else False

    ##################################################################### OPTIMIZED CODE ############################################################################    
    
    def compute_services_based_on_date(self):
        """Compute invoice lines based on member type (credit/policy) and date range."""
        
        # Pre-fetch common data to reduce repeated queries
        country_ae = self.env['res.country'].search([('code', '=', 'AE')], limit=1)
        vat_tax = self.env['account.tax'].search([
            ('amount', '=', 5),
            ('type_tax_use', '=', 'sale'),
            ('active', '=', True),
            ('country_id', '=', country_ae.id)
        ], limit=1)
        
        for record in self:
            # Early validation
            if not self._validate_record(record):
                continue
            
            # Clear existing lines once
            record.invoice_line_ids = [(5, 0, 0)]
            
            if record.member_type == "credit":
                self._process_credit_member(record, vat_tax)
            elif record.member_type == "policy":
                self._process_policy_member(record, vat_tax)


    def _validate_record(self, record):
        """Validate record has required fields."""
        if record.move_type == 'out_invoice':
            return all([record.from_date, record.to_date, record.partner_id, record.category_id])
        elif record.move_type == 'out_refund':
            return all([record.partner_id, record.category_id])
        return False


    def _process_credit_member(self, record, vat_tax):
        """Process credit member type invoices."""
        record.credit_service_line_ids = [(5, 0, 0)]
        
        # Fetch all services in one query
        services = self.env["aaa.service"].search([
            ("customer_id", "=", record.partner_id.id),
            ("sequence_id", "=", record.category_id.id),
            ("state", "=", "done"),
            ("invoice_state", "=", "not_invoiced"),
            ("service_time", ">=", fields.Datetime.to_datetime(record.from_date)),
            ("service_time", "<=", fields.Datetime.to_datetime(record.to_date) + timedelta(days=1))
        ])
        
        if not services:
            return
        
        # Pre-fetch related data to minimize queries
        pricelist_id = record.partner_id.property_product_pricelist_id.id
        product_ids = services.mapped('product_id.id')
        
        # Fetch all pricelist items at once
        pricelist_items = self.env["product.pricelist.item"].search([
            ('product_tmpl_id', 'in', product_ids),
            ('pricelist_id', '=', pricelist_id),
            ('date_start', '<=', record.to_date),
            ('date_end', '>=', record.from_date)
        ])
        
        # Build lookup dictionaries for faster access
        # FIX: Convert date_start and date_end to date objects for comparison
        pricelist_map = {
            (item.product_tmpl_id.id, item.date_start, item.date_end): item
            for item in pricelist_items
        }
        
        # Fetch all service rates at once
        pricelist_item_ids = pricelist_items.ids
        service_rates = self.env["service.rate"].search([
            ('product_pricelist_item_id', 'in', pricelist_item_ids)
        ])
        
        # Build service rate lookup
        rate_map = {
            (sr.product_pricelist_item_id.id, sr.from_loc_id.id, sr.to_loc_id.id): sr.price
            for sr in service_rates
        }
        
        # Process services
        total = 0
        service_count = 0
        credit_services = {}
        is_rent_a_car = False
        
        for service in services:
            service_date = service.service_time.date()
            
            # Find matching pricelist item
            price_list_item = None
            for key, item in pricelist_map.items():
                product_id, date_start, date_end = key
                
                # FIX: Ensure all dates are date objects for comparison
                # Convert date_start and date_end to date if they're datetime
                if hasattr(date_start, 'date'):
                    date_start = date_start.date()
                if hasattr(date_end, 'date'):
                    date_end = date_end.date()
                
                if (product_id == service.product_id.id and 
                    date_start <= service_date <= date_end):
                    price_list_item = item
                    break
            
            if not price_list_item:
                continue
            
            # Get service rate
            rate_key = (price_list_item.id, service.from_location.id, service.to_location.id)
            service_price = rate_map.get(rate_key, 0)
            
            total += service_price
            service_count += 1
            
            # Check if rent a car
            product_name = service.product_id.name
            is_rac = product_name in ("RENT A CAR", "RENT A CAR - UPGRADE")
            if is_rac:
                is_rent_a_car = True
            
            credit_services[service.id] = {
                "service_date": service_date,
                "service_number_id": service.id,
                "trip_sheet_number": service.credit_proforma_number,
                "vehicle_model": service.vehicle_model,
                "vehicle_plate": service.vehicle_plate,
                "service_product_id": service.product_id.id,
                "from_location_id": service.from_location.id,
                "to_location_id": service.to_location.id,
                "date_time_from": service.date_time_from if is_rac else False,
                "date_time_to": service.date_time_to if is_rac else False,
                "quantity": service.quantity if is_rac else False,
                "price": service_price,
            }
        
        record.is_rent_a_car = is_rent_a_car
        
        # Create invoice lines
        if service_count > 0:
            invoice_lines = [(0, 0, {
                "name": f"Services Provided for Customer: {record.partner_id.name} "
                        f"from {record.from_date.strftime('%d/%m/%Y')} "
                        f"to {record.to_date.strftime('%d/%m/%Y')} ({service_count} services)",
                "price_unit": total,
                "quantity": service_count,
                "tax_ids": [(6, 0, [vat_tax.id])]
            })]
            
            credit_service_lines = [(0, 0, vals) for vals in credit_services.values()]
            
            record.write({
                "invoice_line_ids": invoice_lines,
                "credit_service_line_ids": credit_service_lines
            })
            
            # Update VAT amounts
            for line in record.invoice_line_ids:
                line.vat_amount = line.price_total - line.price_subtotal


    def _process_policy_member(self, record, vat_tax):
        """Process policy member type invoices."""
        record.policy_membership_line_ids = [(5, 0, 0)]
        
        if record.move_type == 'out_refund':
            all_records = self._get_credit_note_records(record)
            
            
        elif record.move_type == 'out_invoice' and record.debit_origin_id:
            all_records = self.env['res.partner'].search([
                ("parent_customer_id", "=", record.partner_id.id),
                ('member_partner_category_id', '=', record.category_id.id),
                ('member_type', '=', record.member_type),
                ("invoice_state", "=", "invoiced"),
                ('membership_state', '=', 'confirm'),
                ('issue_debit_note', '=', True),
            ])
        else:
            all_records = self._get_policy_invoice_records(record)
        
        if not all_records:
            return
        
        # Pre-fetch pricelist items
        product_ids = list(set(rec.product_template_id.id for rec in all_records))
        pricelist_id = record.partner_id.property_product_pricelist_id.id
        
        pricelist_items = self.env["product.pricelist.item"].search([
            ('product_tmpl_id', 'in', product_ids),
            ('pricelist_id', '=', pricelist_id)
        ])
        
        # Build pricelist lookup
        price_map = {item.product_tmpl_id.id: item.fixed_price for item in pricelist_items}
        
        # Process records
        policy_memberships = {}
        product_quantity = {}
        
        for rec in all_records:
            product_id = rec.product_template_id.id
            amount = price_map.get(product_id, 0)
            
            policy_memberships[rec.id] = {
                'membership_no': rec.old_membership_number or rec.ref_num or False,
                'name': rec.name or False,
                'plate_no': rec.vehicle_plate or False,
                'chasis_no': rec.vehicle_chasis_no or False,
                'policy_no': rec.policy_no or False,
                'start_date': rec.member_activate_date or False,
                'expiry_date': rec.member_expiry_date or False,
                'invoice_ref_date': rec.invoice_ref_date or False,
                'car_make': rec.vehicle_type or False,
                'amount': amount,
                'invoice_reference_id': rec.invoice_id.id if rec.invoice_id else False,
            }
            
            if product_id in product_quantity:
                product_quantity[product_id]["quantity"] += 1
            else:
                name_suffix = (f"MEMBERSHIP FOR THE PERIOD FROM {record.from_date.strftime('%d/%m/%Y')} "
                            f"TO {record.to_date.strftime('%d/%m/%Y')}"
                            if record.move_type == 'out_invoice'
                            else "MEMBERSHIP")
                
                product_quantity[product_id] = {
                    "product_id": product_id,
                    "price_unit": amount,
                    "quantity": 1,
                    "tax_ids": [(6, 0, [vat_tax.id])],
                    "name": f"{rec.product_template_id.name} {name_suffix}",
                }
        
        # Create invoice lines
        invoice_lines = [(0, 0, vals) for vals in product_quantity.values()]
        policy_membership_lines = [(0, 0, vals) for vals in policy_memberships.values()]
        
        record.write({
            "invoice_line_ids": invoice_lines,
            "policy_membership_line_ids": policy_membership_lines
        })
        
        # Update VAT amounts
        for line in record.invoice_line_ids:
            line.vat_amount = line.price_total - line.price_subtotal


    def _get_credit_note_records(self, record):
        """Get records for credit note generation."""
        return self.env['res.partner'].search([
            ("parent_customer_id", "=", record.partner_id.id),
            ('member_partner_category_id', '=', record.category_id.id),
            ('member_type', '=', record.member_type),
            ("invoice_state", "=", "invoiced"),
            ('membership_state', '=', 'cancel'),
            ('issue_credit_note', '=', True),
        ])


    def _get_policy_invoice_records(self, record):
        """Get records for policy invoice generation."""
        base_domain = [
            ('invoice_ref_date', '>=', record.from_date),
            ('invoice_ref_date', '<=', record.to_date),
            ("parent_customer_id", "=", record.partner_id.id),
            ('member_partner_category_id', '=', record.category_id.id),
            ('member_type', '=', record.member_type),
            ("invoice_state", "=", "not_invoiced")
        ]
        
        # Fetch partner records
        partner_domain = base_domain + [('membership_state', '=', 'confirm')]
        partner_records = self.env['res.partner'].search(partner_domain)
        
        # Fetch history records
        # history_records = self.env['membership.history'].search(base_domain)
        
        # Fetch renewal queue records
        renewal_queue_records = self.env['renewal.queue.data'].search([
            ('member_id.renewal_in_queue', '=', True),
            ('invoice_ref_date', '>=', record.from_date),
            ('invoice_ref_date', '<=', record.to_date),
            ('member_partner_category_id', '=', record.category_id.id),
            ('invoice_state', '=', 'not_invoiced'),
        ])
        
        # Chain all records together
        # return list(chain(partner_records, history_records, renewal_queue_records))
        return list(chain(partner_records, renewal_queue_records))

    #################################################################################################################################################################
    
    @api.depends('from_date', 'to_date', 'partner_id', 'category_id', 'member_type', 'invoice_line_type')
    def _compute_dynamic_domains(self):
        for rec in self:
            product_domain = []
            service_domain = []

            # Guard
            if not (rec.from_date and rec.to_date and rec.partner_id and rec.category_id) or rec.invoice_line_type != 'separate':
                rec.product_domain_char = json.dumps(product_domain)
                rec.service_domain_char = json.dumps(service_domain)
                continue

            if rec.member_type == 'credit':
                dt_from = fields.Datetime.to_string(datetime.combine(rec.from_date, time.min))
                dt_to = fields.Datetime.to_string(datetime.combine(rec.to_date, time.max))
                service_domain = [
                    ('customer_id', '=', rec.partner_id.id),
                    ('sequence_id', '=', rec.category_id.id),
                    ('state', '=', 'done'),
                    ('invoice_state', '=', 'not_invoiced'),
                    ('service_time', '>=', dt_from),
                    ('service_time', '<=', dt_to),
                ]
            elif rec.member_type == 'policy':
                base = [
                    ('invoice_ref_date', '>=', rec.from_date),
                    ('invoice_ref_date', '<=', rec.to_date),
                    ('parent_customer_id', '=', rec.partner_id.id),
                    ('member_partner_category_id', '=', rec.category_id.id),
                    ('member_type', '=', rec.member_type),
                ]
                partner_domain = base + [('membership_state', '=', 'confirm')]
                partner_groups = self.env['res.partner'].read_group(
                    partner_domain + [('product_template_id', '!=', False)],
                    ['product_template_id'],
                    ['product_template_id'],
                    lazy=False,
                )
                product_ids = [g['product_template_id'][0] for g in partner_groups if g.get('product_template_id')]
                product_domain = [('id', 'in', product_ids)]

            rec.product_domain_char = json.dumps(product_domain)
            rec.service_domain_char = json.dumps(service_domain)


    #################################################################################################################################################################


    # def compute_services_based_on_date(self):

    #     for record in self:
    #         if record.move_type == 'out_invoice':
    #             if not record.from_date or not record.to_date or not record.partner_id or not record.category_id:
    #                 continue
    #         elif record.move_type == 'out_refund':
    #             if not record.partner_id or not record.category_id:
    #                 continue
    #         # if record.state != 'draft':
    #         #     record.button_draft()
    #         # if record.state != 'draft':
    #         #     # If it's already posted, skip modifying
    #         #     if record.state == 'posted':
    #         #         continue
    #         #     # Otherwise, try setting it to draft
    #         #     record.button_draft()

    #         if record.member_type == "credit":

    #             all_services = self.env["aaa.service"].search(
    #                 [("customer_id", "=", record.partner_id.id),("sequence_id","=",record.category_id.id),("state","=","done"),("invoice_state","=","not_invoiced")] 
    #             )
    #             invoice_lines = []
    #             total = 0
    #             service_count = 0
    #             credit_services = {}
    #             # quantity = 0

    #             record.invoice_line_ids = [(5, 0, 0)]
    #             record.credit_service_line_ids = [(5, 0, 0)]

    #             for service in all_services:
    #                 service_date = service.service_time.date()
    #                 if record.from_date <= service_date <= record.to_date:

    #                     price_list_item = self.env["product.pricelist.item"].search([('product_tmpl_id','=',service.product_id.id), ('pricelist_id','=',record.partner_id.property_product_pricelist_id.id),
    #                     ('date_start', '<=', service_date),
    #                     ('date_end', '>=', service_date)])
                
    #                     service_rate = self.env["service.rate"].search([('product_pricelist_item_id','=',price_list_item.id),
    #                                                             ('from_loc_id','=',service.from_location.id),
    #                                                             ('to_loc_id','=',service.to_location.id),],limit=1)
                        
    #                     total += service_rate.price
    #                     service_count += 1
  

    #                     credit_services[service.id] = {
    #                         "service_date": service_date,
    #                         "service_number_id": service.id,
    #                         "trip_sheet_number": service.credit_proforma_number,
    #                         "vehicle_model": service.vehicle_model,
    #                         "vehicle_plate": service.vehicle_plate,
    #                         "service_product_id": service.product_id.id,
    #                         "from_location_id": service.from_location.id,
    #                         "to_location_id": service.to_location.id,
    #                         "date_time_from": service.date_time_from if service.product_id.name == "RENT A CAR" or service.product_id.name == "RENT A CAR - UPGRADE" else False,
    #                         "date_time_to": service.date_time_to if service.product_id.name == "RENT A CAR" or service.product_id.name == "RENT A CAR - UPGRADE" else False,
    #                         "quantity": service.quantity if service.product_id.name == "RENT A CAR" or service.product_id.name == "RENT A CAR - UPGRADE" else False,
    #                         "price": service_rate.price,
    #                         }
                        
    #                     if service.product_id.name == "RENT A CAR" or service.product_id.name == "RENT A CAR - UPGRADE":
    #                         record.is_rent_a_car = True
    #                     else:
    #                         record.is_rent_a_car = False

                       
    #             country_id = self.env['res.country'].search([('code', '=', 'AE')], limit=1)
    #             tax = self.env['account.tax'].search([('amount', '=', 5), ('type_tax_use', '=', 'sale'), ('active', '=', 'True'), ('country_id', '=', country_id.id)], limit=1)


    #             invoice_lines = [(0, 0, {
    #                         "name": f"Services Provided for Customer: {record.partner_id.name} from {record.from_date.strftime('%d/%m/%Y')} to {record.to_date.strftime('%d/%m/%Y')} ({service_count} services)",
    #                         "price_unit": total,
    #                         "quantity": 1,
    #                         "tax_ids": [(6, 0, [tax.id])]
    #                         })]
    #             credit_service_lines = [(0, 0, values)
    #                                         for values in credit_services.values()]

    #             record.write({"invoice_line_ids": invoice_lines,
    #                           "credit_service_line_ids": credit_service_lines})
                
    #             for line in record.invoice_line_ids:
    #                 line.vat_amount = line.price_total - line.price_subtotal


    #         elif record.member_type == "policy":
    #             print("Policy Member Selected")
    #             if record.move_type == 'out_refund':
    #                 print("Credit Note Selected")
                    
    #                 cancelled_records = self.env['res.partner'].search([("parent_customer_id", "=", record.partner_id.id),
    #                                                                     ('member_partner_category_id', '=', record.category_id.id),
    #                                                                     ('member_type', '=', record.member_type),
    #                                                                     ("invoice_state","=","invoiced"),
    #                                                                     ('membership_state', '=', 'cancel'),
    #                                                                     ('issue_credit_note', '=', True),])
    #                 all_records = cancelled_records
    #                 print(all_records, "all_records")

    #                 invoices = all_records.mapped('invoice_id')
    #                 record.reference_invoice_ids |= invoices
                        

    #                 # invoice_map = {}
    #                 # for rec in all_records:
    #                 #     if rec.invoice_id:
    #                 #         if rec.invoice_id.id in invoice_map:
    #                 #             invoice_map[rec.invoice_id.id].append(rec)
    #                 #         else:
    #                 #             invoice_map[rec.invoice_id.id] = [rec]


    #             else:
    #                 domain = [('invoice_ref_date', '>=', record.from_date), 
    #                         ('invoice_ref_date', '<=', record.to_date),
    #                         ("parent_customer_id", "=", record.partner_id.id),
    #                         ('member_partner_category_id', '=', record.category_id.id),
    #                         ('member_type', '=', record.member_type),
    #                         ("invoice_state","=","not_invoiced")]
                    
    #                 partner_domain = domain + [('membership_state', '=', 'confirm')]

    #                 partner_records = self.env['res.partner'].search(partner_domain)
    #                 history_records = self.env['membership.history'].search(domain)
                    
    #                 # renewal_queue_records = self.env['res.partner'].search([('renewal_in_queue', '=', True)]).mapped('renewal_queue_data_ids').filtered(lambda r: r.invoice_ref_date >= record.from_date and r.invoice_ref_date <= record.to_date and r.member_partner_category_id == record.category_id and r.invoice_state == 'not_invoiced')

    #                 renewal_queue_records = self.env['renewal.queue.data'].search([
    #                     ('member_id.renewal_in_queue', '=', True),
    #                     ('invoice_ref_date', '>=', record.from_date),
    #                     ('invoice_ref_date', '<=', record.to_date),
    #                     ('member_partner_category_id', '=', record.category_id.id),
    #                     ('invoice_state', '=', 'not_invoiced'),
    #                 ])


    #                 all_records = chain(partner_records, history_records, renewal_queue_records)

    #             invoice_lines = []
    #             policy_memberships = {}
    #             product_quantity = {}

    #             record.invoice_line_ids = [(5, 0, 0)]
    #             record.policy_membership_line_ids = [(5, 0, 0)]

    #             for rec in all_records:
    #                 product_id = rec.product_template_id.id

    #                 amount = self.env["product.pricelist.item"].search([('product_tmpl_id','=',product_id), ('pricelist_id','=',record.partner_id.property_product_pricelist_id.id)])

                    # policy_memberships[rec.id] = {
                    #     'membership_no': rec.old_membership_number or rec.ref_num or False,
                    #     'name': rec.name or False,
                    #     'plate_no': rec.vehicle_plate or False,
                    #     'chasis_no': rec.vehicle_chasis_no or False,
                    #     'policy_no': rec.policy_no or False,
                    #     'start_date': rec.member_activate_date if rec.member_activate_date else False,
                    #     'expiry_date': rec.member_expiry_date if rec.member_expiry_date else False,
                    #     'car_make': rec.vehicle_type or False,
                    #     'amount': amount.fixed_price,
                    # } 

    #                 country_id = self.env['res.country'].search([('code', '=', 'AE')], limit=1)
    #                 tax = self.env['account.tax'].search([('amount', '=', 5), ('type_tax_use', '=', 'sale'), ('active', '=', 'True'), ('country_id', '=', country_id.id)], limit=1)

    #                 if product_id in product_quantity:
    #                         product_quantity[product_id]["quantity"] += 1

    #                 else:
    #                     product_quantity[product_id] = {
    #                         "product_id": product_id,
    #                         "price_unit": 0,
    #                         "quantity": 1,
    #                         "tax_ids": [(6, 0, [tax.id])],
    #                         # "name": f"{rec.product_template_id.name} MEMBERSHIP FOR THE PERIOD FROM {record.from_date.strftime('%d/%m/%Y')} TO {record.to_date.strftime('%d/%m/%Y')}",
    #                         "name": f"{rec.product_template_id.name} MEMBERSHIP FOR THE PERIOD FROM {record.from_date.strftime('%d/%m/%Y')} TO {record.to_date.strftime('%d/%m/%Y')}"
    #                                 if record.move_type == 'out_invoice'
    #                                 else f"{rec.product_template_id.name} MEMBERSHIP",
    #                     }

    #             for key in product_quantity.keys():
    #                 pricelist_item = self.env["product.pricelist.item"].search([('product_tmpl_id','=',key), ('pricelist_id','=',record.partner_id.property_product_pricelist_id.id)])
                    
    #                 product_quantity[key]["price_unit"] = pricelist_item.fixed_price
                    

    #             invoice_lines = [(0, 0, values)
    #                                 for values in product_quantity.values()]
    #             policy_membership_lines = [(0, 0, values)
    #                                         for values in policy_memberships.values()]

    #             record.write({"invoice_line_ids": invoice_lines,
    #                           "policy_membership_line_ids": policy_membership_lines})
                
    #             for line in record.invoice_line_ids:
    #                 line.vat_amount = line.price_total - line.price_subtotal

 #################################################################################################################################################################
    


    # @api.onchange('from_date', 'to_date', 'partner_id', 'category_id', 'member_type', 'invoice_line_type')
    # def _onchange_compute_service_id_domain(self):
    #     self._compute_service_id_domain()




    def compute_separate_invoice_line(self):

        for record in self:

            if record.state != 'draft':
                # If it's already posted, skip modifying
                if record.state == 'posted':
                    continue
                # Otherwise, try setting it to draft
                record.button_draft()
            
            record.invoice_line_ids = [(5, 0, 0)]

            quantity = 0

            if record.member_type == "credit":

                if not record.service_id:
                    continue

                service_date = record.service_id.service_time.date()
                
                price_list_item = self.env["product.pricelist.item"].search([('product_tmpl_id','=',record.service_id.product_id.id), ('pricelist_id','=',record.partner_id.property_product_pricelist_id.id),
                ('date_start', '<=', service_date),
                ('date_end', '>=', service_date)])
                
                service_rate = self.env["service.rate"].search([('product_pricelist_item_id','=',price_list_item.id),
                                                                ('from_loc_id','=',record.service_id.from_location.id),
                                                                ('to_loc_id','=',record.service_id.to_location.id)],limit=1)
                
                if record.service_id.product_id.name == "RENT A CAR" or record.service_id.product_id.name == "RENT A CAR - UPGRADE":

                    from_time = fields.Datetime.context_timestamp(record, record.service_id.date_time_from).strftime('%d/%m/%Y %H:%M:%S')
                    to_time = fields.Datetime.context_timestamp(record, record.service_id.date_time_to).strftime('%d/%m/%Y %H:%M:%S')

                    name = f"{record.service_id.product_id.name} {record.service_id.vehicle_type or ''} {record.service_id.vehicle_model or ''} {record.service_id.vehicle_chasis_no} FROM: {from_time} TO: {to_time}"

                    quantity = record.service_id.quantity
                
                else:
                    name = f"{record.service_id.product_id.name} {record.service_id.vehicle_type or ''} {record.service_id.vehicle_model or ''} {record.service_id.vehicle_chasis_no} FROM: {record.service_id.from_location.name} TO: {record.service_id.to_location.name}"

                    quantity = 1

                country_ae = self.env['res.country'].search([('code', '=', 'AE')], limit=1)
                vat_tax = self.env['account.tax'].search([
                    ('amount', '=', 5),
                    ('type_tax_use', '=', 'sale'),
                    ('active', '=', True),
                    ('country_id', '=', country_ae.id)
                ], limit=1)

                invoice_line_items = {
                            "product_id": record.service_id.product_id.id,
                            "price_unit": service_rate.price,
                            "quantity": quantity,
                            "tax_ids": [(6, 0, [vat_tax.id])],
                            "name": name,
                            }
                record.write({"invoice_line_ids":[(0,0,invoice_line_items)]})
    

            elif record.member_type == "policy":

                if not record.product_id:
                    continue

                policy_memberships = {}

                domain = [('invoice_ref_date', '>=', record.from_date), 
                        ('invoice_ref_date', '<=', record.to_date),
                        ("parent_customer_id", "=", record.partner_id.id),
                        ('member_partner_category_id', '=', record.category_id.id),
                        ('member_type', '=', record.member_type),
                        ('product_template_id','=',record.product_id.id)]
                
                partner_domain = domain + [('membership_state', '=', 'confirm')]

                partner_records = self.env['res.partner'].search(partner_domain)
                # history_records = self.env['membership.history'].search(domain)
                renewal_queue_records = self.env['renewal.queue.data'].search([
                    ('member_id.renewal_in_queue', '=', True),
                    ('invoice_ref_date', '>=', record.from_date),
                    ('invoice_ref_date', '<=', record.to_date),
                    ('member_partner_category_id', '=', record.category_id.id),
                    ('invoice_state', '=', 'not_invoiced'),
                ])

                all_records = chain(partner_records, renewal_queue_records)

                pricelist_item = self.env["product.pricelist.item"].search([('product_tmpl_id','=',record.product_id.id), ('pricelist_id','=',record.partner_id.property_product_pricelist_id.id)])

                for rec in all_records:
                    quantity += 1

                    policy_memberships[rec.id] = {
                        'membership_no': rec.old_membership_number or rec.ref_num or False,
                        'name': rec.name or False,
                        'plate_no': rec.vehicle_plate or False,
                        'chasis_no': rec.vehicle_chasis_no or False,
                        'policy_no': rec.policy_no or False,
                        'start_date': rec.member_activate_date if rec.member_activate_date else False,
                        'expiry_date': rec.member_expiry_date if rec.member_expiry_date else False,
                        'invoice_ref_date': rec.invoice_ref_date or False,
                        'car_make': rec.vehicle_type or False,
                        'amount': pricelist_item.fixed_price,
                    } 
                
                country_ae = self.env['res.country'].search([('code', '=', 'AE')], limit=1)
                vat_tax = self.env['account.tax'].search([
                    ('amount', '=', 5),
                    ('type_tax_use', '=', 'sale'),
                    ('active', '=', True),
                    ('country_id', '=', country_ae.id)
                ], limit=1)

                invoice_line_items = {
                            "product_id": record.product_id.id,
                            "price_unit": pricelist_item.fixed_price,
                            "quantity": quantity,
                            "tax_ids": [(6, 0, [vat_tax.id])],
                            "name": f"{record.product_id.name} MEMBERSHIP FOR THE PERIOD FROM {record.from_date.strftime('%d/%m/%Y')} TO {record.to_date.strftime('%d/%m/%Y')}",
                            }

                policy_membership_lines = [(0, 0, values)
                                            for values in policy_memberships.values()]

            
                record.write({"invoice_line_ids":[(0,0,invoice_line_items)],
                        "policy_membership_line_ids": policy_membership_lines})

            for line in record.invoice_line_ids:
                    line.vat_amount = line.price_total - line.price_subtotal


    def compute_credit_service_line_total(self):
        for record in self:
            total_price = sum(line.price for line in record.credit_service_line_ids if line.add_to_invoice)
            for line_id in record.invoice_line_ids: 
                record.write({"invoice_line_ids":[(1,line_id.id,{"price_unit":total_price})]})


    def preview_invoice(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.report',
            'report_type': 'qweb-html',  # or 'qweb-html' for HTML preview
            'report_name': 'customer.report_credit_invoice_pdf',  # XML ID of your report
            'res_id': self.id,
            'res_model': self._name,
            'name': 'Invoice Preview',
        }


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    vat_amount = fields.Monetary(string="Tax Amount", readonly=True,
        currency_field='company_currency_id')                
            
            
class CreditServiceLine(models.Model):
    _name = 'credit.service.line'
    _description = 'Credit Service Lines'

    credit_invoice_id = fields.Many2one('account.move', string="Invoice ID")
    service_date = fields.Date(string="Service Date")
    # service_number = fields.Char(string="Service Number")
    service_number_id = fields.Many2one('aaa.service', string="Service Number")
    trip_sheet_number = fields.Char(string="Trip Sheet No.")
    vehicle_model = fields.Char(string="Vehicle Model")
    vehicle_plate = fields.Char(string="Vehicle Plate")
    # service_product = fields.Char(string="Product")
    # from_location = fields.Char(string="From Location")
    # to_location = fields.Char(string="To Location")
    service_product_id = fields.Many2one('product.template', string="Service")
    from_location_id = fields.Many2one('aaa.location', string="From Location")
    to_location_id = fields.Many2one('aaa.location', string="To Location")
    date_time_from = fields.Datetime(string="From Date")
    date_time_to = fields.Datetime(string="To Date")
    quantity = fields.Float(string="Quantity")
    price = fields.Float(string="Price")
    add_to_invoice = fields.Boolean(string="Add to Invoice", default=True)


class PolicyMembershipLine(models.Model):
    _name = 'policy.membership.line'
    _description = 'Policy Membership Lines'
    
    policy_invoice_id = fields.Many2one('account.move', string="Invoice ID")
    membership_no = fields.Char(string="Membership No.")
    name = fields.Char(string="Name")
    plate_no = fields.Char(string="Plate No.")
    chasis_no = fields.Char(string="Chassis No.")
    policy_no = fields.Char(string="Policy No.")
    start_date = fields.Date(string="Start Date")
    expiry_date = fields.Date(string="Expiry Date")
    invoice_ref_date = fields.Date(string="Invoice Date")
    car_make = fields.Char(string="Vehicle Type")
    amount = fields.Float(string="Amount")
    invoice_reference_id = fields.Many2one('account.move', string="Invoice Reference ID")

    
