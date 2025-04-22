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
load_dotenv()
_logger = logging.getLogger(__name__)
base_url = os.getenv("BASE_URL")

class AAAServiceAddons(models.Model):
    _inherit = 'aaa.service'

    