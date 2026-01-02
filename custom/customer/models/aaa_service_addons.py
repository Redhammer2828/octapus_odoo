from odoo import api, fields, models, _
from odoo.exceptions import ValidationError , UserError
import datetime
from datetime import timedelta,datetime
import requests
import json
import re
from dotenv import load_dotenv
import os
import logging
from pytz import timezone
import pytz
from dateutil.relativedelta import relativedelta
import pytz
from dateutil.relativedelta import relativedelta
from datetime import datetime, time, timedelta
load_dotenv()
_logger = logging.getLogger(__name__)
base_url = os.getenv("BASE_URL")

class AAAServiceAddons(models.Model):
    _inherit = 'aaa.service'

    service_from_app = fields.Boolean(string="Service From App", default=False)
    driver_comment = fields.Text(string="Driver Comment")
    garage_driver_comment = fields.Text(string="Garage Driver Comment")
    invoice_state = fields.Selection([
        ('not_invoiced', 'Not Invoiced'),
        ('invoiced', 'Invoiced'),
        ], string="Invoice Status", readonly=True, default='not_invoiced')
    invoiced_by = fields.Many2one('res.users', string="Invoiced By")
    invoiced_date = fields.Date(string="Invoiced Date")
    invoice_id = fields.Many2one('account.move', string="Invoice Number")

    country_from_id = fields.Many2one('country.code', string="Country From")
    country_to_id = fields.Many2one('country.code', string="Country To")

    # Regular char fields for storing the selected locations
    location_from_external = fields.Char(string="Location From")
    location_to_external = fields.Char(string="Location To")
    
    # Additional fields to store location details after selection
    location_from_id = fields.Char(string="From Location ID")
    location_from_latitude = fields.Char(string="From Latitude")
    location_from_longitude = fields.Char(string="From Longitude")
    emirate_from_location = fields.Char(string="Emirate From")
    
    location_to_id = fields.Char(string="To Location ID")
    location_to_latitude = fields.Char(string="To Latitude")
    location_to_longitude = fields.Char(string="To Longitude")
    emirate_to_location = fields.Char(string="Emirate To")

    state = fields.Selection(
        selection_add=[
            ('whatsapp_cancel', 'Whatsapp Cancelled'),
        ])


    driver_assigned_by = fields.Char(string="Driver Assigned By")
    is_transferred_service = fields.Boolean(string="Is Transferred Service", default=False, index=True)


    def write(self, vals):
        # Fields to track for changes
        tracked_fields = {
            'product_id': 'Service',
            'from_location': 'From Location', 
            'to_location': 'To Location',
            'vehicle_type_id': 'Vehicle Type',
            'vehicle_model_id': 'Vehicle Model',
            'vehicle_plate': 'Vehicle Plate',
            'vehicle_chasis_no': 'Vehicle Chassis No',
            'policy_no': 'Policy No',
            'provider_id': 'Provider',
            'driver_name': 'Driver Name',
            'credit_proforma_number': 'Trip Sheet Number',
            'driver_id': 'Driver',
        }
        
        # Store original values before the write operation
        original_values = {}
        for record in self:
            original_values[record.id] = {}
            for field in tracked_fields.keys():
                if hasattr(record, field):
                    if field in ['product_id', 'from_location', 'to_location', 'provider_id', 'vehicle_type_id', 'vehicle_model_id', 'driver_id']:
                        # For many2one fields, store the ID
                        field_value = getattr(record, field)
                        original_values[record.id][field] = field_value.id if field_value else False
                    else:
                        # For regular fields, store the value directly
                        original_values[record.id][field] = getattr(record, field)
        
        # Perform the actual write operation
        result = super().write(vals)
        
        # Check if any tracked fields were changed and record is not being created
        for record in self:
            # Skip tracking if this is during record creation (no create_date means it's being created)
            if not record.create_date:
                continue
                
            changes = []
            
            for field_name, field_label in tracked_fields.items():
                if field_name in vals:  # Only check fields that were actually updated
                    old_value = original_values[record.id].get(field_name)
                    
                    # Get new value after write
                    if field_name in ['product_id', 'from_location', 'to_location', 'provider_id', 'vehicle_type_id', 'vehicle_model_id', 'driver_id']:
                        # For many2one fields
                        new_field_value = getattr(record, field_name)
                        new_value = new_field_value.id if new_field_value else False
                    else:
                        # For regular fields
                        new_value = getattr(record, field_name)
                    
                    # Compare old and new values
                    if old_value != new_value:
                        old_display = "None"
                        new_display = "None"
                        
                        # Get display names for many2one fields
                        if field_name == 'product_id':
                            if old_value:
                                old_display = self.env['product.template'].browse(old_value).name
                            if new_value:
                                new_display = getattr(record, field_name).name

                        elif field_name in ['from_location', 'to_location']:
                            if old_value:
                                old_display = self.env['aaa.location'].browse(old_value).name
                            if new_value:
                                new_display = getattr(record, field_name).name

                        elif field_name == 'provider_id':
                            if old_value:
                                old_display = self.env['res.partner'].browse(old_value).name  
                            if new_value:
                                new_display = getattr(record, field_name).name
                        
                        elif field_name == 'vehicle_type_id':
                            if old_value:
                                old_display = self.env['member.vehicle.type'].browse(old_value).name 
                            if new_value:
                                new_display = getattr(record, field_name).name

                        elif field_name == 'vehicle_model_id':
                            if old_value:
                                old_display = self.env['member.vehicle.model'].browse(old_value).name  
                            if new_value:
                                new_display = getattr(record, field_name).name

                        elif field_name == 'driver_id':
                            if old_value:
                                old_display = self.env['hr.employee'].browse(old_value).name  
                            if new_value:
                                new_display = getattr(record, field_name).name

                        else:
                            # For regular text/char fields
                            old_display = old_value or "None"
                            new_display = new_value or "None"
                        
                        changes.append(f"{field_label}: {old_display} → {new_display}")
            
            # Create service comment record if there are changes
            if changes:
                change_comment = ", ".join(changes)
                
                # self.env['service.comment'].sudo().create({
                #     'service_id': record.id,
                #     'comment': 'CHANGED',
                #     'comment_date_and_time': fields.Datetime.now(),
                #     'comment_user': self.env.user.id,
                #     'comment_status': change_comment,
                # })

                self.env['service.history'].create({
                    'service_id': record.id,
                    'user': self.env.user.id,
                    'time': fields.Datetime.now(),
                    'status': change_comment,
                    'timeline_status': record.state,
                })

            # uid = self.env.context.get('uid')

            # self.env["bus.bus"].sudo()._sendone(
            #     "broadcast",
            #     "page_refresh", 
            #     {
            #         "record_id": self.id,
            #         "model_name": self._name,
            #         "uid": uid,
            #         })
            # print(f"Request ID: {uid}")

        return result
    
    def trigger_reload_service_page(self):
        # uid = self.env.uid
        uid = self.env.context.get('uid')

        try:
            self.env["bus.bus"].sudo()._sendone(
                    "broadcast",
                    "page_refresh", 
                    {
                        "record_id": self.id,
                        # "model_name": self._name,
                        "uid": uid,
                        })
            _logger.info(f"Page refresh broadcast: {self._name} ID {self.id} by user {uid}")
        
        except Exception as e:
            # Don't crash the main action if bus fails
            _logger.error(f"Failed to broadcast page refresh: {e}")
            # Optionally: Return a warning to user
            return {'warning': {'message': 'Could not notify other users'}}


    def _dispatch_service(self):
        res = super()._dispatch_service()
        
        self.trigger_reload_service_page()
        return res
    
    def action_start_service(self):
        res = super().action_start_service()
        
        self.trigger_reload_service_page()
        return res
    
    def action_reach_service(self):
        res = super().action_reach_service()
        
        self.trigger_reload_service_page()
        return res
    
    def action_done_service(self):
        res = super().action_done_service()
        
        self.trigger_reload_service_page()
        return res
    
    def action_cancel_service(self):
        res = super().action_cancel_service()
        
        self.trigger_reload_service_page()
        return res
    
    def action_new_change(self):
        res = super().action_new_change()
        
        self.trigger_reload_service_page()
        return res
    
    def action_completed_rac(self):
        res = super().action_completed_rac()
        
        self.trigger_reload_service_page()
        return res
    
    def action_cancel_done_service(self):
        res = super().action_cancel_done_service()
        
        self.trigger_reload_service_page()
        return res

    
    # def create(self, vals_list):
    #     recs = super().create(vals_list)
        
    #     self.env["bus.bus"].sudo()._sendone(
    #             "broadcast",
    #             "page_refresh", 
    #             {
    #                 "record_id": self.id,
    #                 "model_name": self._name,
    #                 "is_create_mode": True,
    #                 })
        
    #     return recs
    
    def action_approve_whatsapp_cancel_service(self):

        self.state = 'cancel'
        self.env['service.history'].create({
                'service_id': self.id,  # Assuming service_id is a Many2one field
                'user': self.env.user.id,
                'time': fields.Datetime.now(),
                'status': 'Whatsapp Service Cancel Request Approved',
                'timeline_status': self.state,
        })




class ServiceHistory(models.Model):
    _inherit = 'service.history'

    timeline_status = fields.Selection(
        selection_add=[
            ('whatsapp_cancel', 'Whatsapp Cancelled'),
        ])
