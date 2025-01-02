from odoo import models, fields, api
from odoo import http
from odoo.http import request
import requests
import json

class Service(models.Model):
    _inherit = 'aaa.service'

    location_name = fields.Char("Location")
    location_lat = fields.Float("Latitude", readonly=True)
    location_lon = fields.Float("Longitude", readonly=True)


    # @api.model
    # def get_places(self, query):
    #     """
    #     Calls the external Elasticsearch API to search for places
    #     matching the user-typed `query`. Returns a list of dicts
    #     with name, latitude, longitude.
    #     """
    #     url = "http://elastic:password@20.204.180.229:9200/osm_places/_search"
    #     payload = {
    #         "query": {
    #             "match": {
    #                 "tags.name": query
    #             }
    #         }
    #     }
    #     headers = {'Content-Type': 'application/json'}

    #     response = requests.request("GET", url, headers=headers, data=json.dumps(payload))
    #     if response.status_code != 200:
    #         return []

    #     data = response.json()
    #     hits = data.get('hits', {}).get('hits', [])
    #     results = []

    #     for h in hits:
    #         _source = h.get('_source', {})
    #         tags = _source.get('tags', {})
    #         lat = _source.get('latitude')
    #         lon = _source.get('longitude')
    #         place_name = tags.get('name', '')

    #         results.append({
    #             'name': place_name,
    #             'latitude': lat,
    #             'longitude': lon,
    #         })

    #     return results

    # def get_places(self, query):
    #     """
    #     Replace this dummy logic with an actual call to Elasticsearch or
    #     any external API if needed.
    #     """
    #     # Example static data:
    #     dummy_places = [
    #         {"name": "Dubai", "latitude": 25.2048, "longitude": 55.2708},
    #         {"name": "Abu Dhabi", "latitude": 24.4539, "longitude": 54.3773},
    #         {"name": "Sharjah", "latitude": 25.3463, "longitude": 55.4209},
    #     ]
    #     # Filter by substring matching, ignoring case
    #     filtered = [
    #         p for p in dummy_places
    #         if query.lower() in p["name"].lower()
    #     ]
    #     return filtered