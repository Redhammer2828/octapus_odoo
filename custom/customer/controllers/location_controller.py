from odoo import http
from odoo.http import request
import requests
import json
import logging
from werkzeug.exceptions import BadRequest
import time

_logger = logging.getLogger(__name__)

class LocationController(http.Controller):
    
    @http.route('/api/location/search', type='json')
    def search_locations(self, query=None, **kwargs):
        if not query:
            return []
            
        try:
            # Replace with your actual API endpoint and parameters
            api_url = "https://nominatim.kirkos.ae/"
            # api_url = "https://nominatim-dev.kirkos.ae/"
            params = {
                'q': query,
                'format': 'geocodejson',
                'addressdetails': 1,
            }
            headers = {
                        'Accept-Language': 'en'
                    }
            
            response = requests.get(api_url, params=params, headers=headers, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                
                # Transform API response to a format suitable for the frontend
                locations = []

                if 'features' in data:
                    for feature in data['features']:
                        geocoding = feature.get('properties', {}).get('geocoding', {})
                        place_id = geocoding.get('place_id')
                        label = geocoding.get('label')
                        name = geocoding.get('name')
                        coordinates = feature.get('geometry', {}).get('coordinates', [None, None])
                        # Prefer state, then country, else fallback
                        emirate = geocoding.get('state') or geocoding.get('country') or "UNKNOWN"

                        if name == "Reconcile":
                            locations.append({
                                'id': False,
                                'name': "RECONCILE",
                                'longitude': False,
                                'latitude': False,
                                'emirate': "RECONCILE",
                            })
                            return locations

                        locations.append({
                            'id': place_id,
                            'name': label,
                            'longitude': coordinates[0],
                            'latitude': coordinates[1],
                            'emirate': emirate,
                        })
                return locations
            else:
                _logger.error("API error: %s", response.text)
                return []
                
        except Exception as e:
            _logger.exception("Error calling location API: %s", str(e))
            return []