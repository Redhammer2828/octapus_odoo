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

    # service_time = fields.Datetime(string="Service Time")
    is_today_service_time = fields.Boolean(string="Is Today", compute="_compute_is_today_service_time", store=True)

    @api.depends('service_time')
    def _compute_is_today_service_time(self):
        for rec in self:
            if rec.service_time:
                user_tz = self.env.user.tz or 'UTC'
                service_dt = fields.Datetime.context_timestamp(rec.with_context(tz=user_tz), rec.service_time)
                today = fields.Date.context_today(rec)
                rec.is_today_service_time = (service_dt.date() == today)
            else:
                rec.is_today_service_time = False