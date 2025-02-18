import hashlib
import json
from odoo import http
from odoo.http import request, Response

class FileChecksumAPI(http.Controller):

    def _compute_checksum(self, bin_data):
        """Compute the SHA-1 checksum for the given binary data."""
        return hashlib.sha1(bin_data or b'').hexdigest()

    @http.route('/api/compute_checksum', type='json', auth='public', methods=['POST'], csrf=False)
    def compute_checksum_api(self, **post):
        """API Endpoint to compute checksum for provided file data."""
        try:
            # Get JSON data from request
            request_data = request.jsonrequest

            if not isinstance(request_data, list):
                return {"error": "Invalid input format. Expected a list of dictionaries."}

            response_data = []

            for file_dict in request_data:
                if not isinstance(file_dict, dict) or not file_dict:
                    continue  # Skip invalid entries

                for filename, hex_data in file_dict.items():
                    try:
                        # Convert hex string to binary
                        bin_data = bytes.fromhex(hex_data)

                        # Compute checksum
                        checksum = self._compute_checksum(bin_data)

                        # Append formatted response
                        response_data.append({filename: checksum})

                    except ValueError:
                        return {"error": f"Invalid hex data for file {filename}"}

            return response_data

        except Exception as e:
            return {"error": str(e)}
