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

    # # Regular char fields for storing the selected locations
    # location_from = fields.Char(string="Location From")
    # location_to = fields.Char(string="Location To")
    
    # # Additional fields to store location details after selection
    # location_from_id = fields.Char(string="From Location ID", readonly=True)
    # location_from_latitude = fields.Char(string="From Latitude", readonly=True)
    # location_from_longitude = fields.Char(string="From Longitude", readonly=True)
    
    # location_to_id = fields.Char(string="To Location ID", readonly=True)
    # location_to_latitude = fields.Char(string="To Latitude", readonly=True)
    # location_to_longitude = fields.Char(string="To Longitude", readonly=True)

    # # service_time = fields.Datetime(string="Service Time")
    # is_today_service_time = fields.Boolean(string="Is Today", compute="_compute_is_today_service_time", store=True)

    # @api.depends('service_time')
    # def _compute_is_today_service_time(self):
    #     for rec in self:
    #         if rec.service_time:
    #             user_tz = self.env.user.tz or 'UTC'
    #             service_dt = fields.Datetime.context_timestamp(rec.with_context(tz=user_tz), rec.service_time)
    #             today = fields.Date.context_today(rec)
    #             rec.is_today_service_time = (service_dt.date() == today)
    #         else:
    #             rec.is_today_service_time = False


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
            'credit_proforma_number': 'Credit Proforma Number',
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
                
                self.env['service.comment'].sudo().create({
                    'service_id': record.id,
                    'comment': 'CHANGED',
                    'comment_date_and_time': fields.Datetime.now(),
                    'comment_user': self.env.user.id,
                    'comment_status': change_comment,
                })
        
        return result