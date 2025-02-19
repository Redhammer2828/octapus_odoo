import hashlib
import json
import base64
import logging
from odoo import http, _
from odoo.http import request

_logger = logging.getLogger(__name__)

class FileChecksumAPI(http.Controller):

    def _compute_checksum(self, bin_data, mimetype):
        """
        Mimics Odoo’s attachment processing to compute the checksum.
        This calls _check_contents on a temporary values dict so that any
        image postprocessing (e.g. resizing) is applied before computing
        the checksum.
        """
        # Get the ir.attachment model from the current environment.
        attachment_obj = request.env['ir.attachment']
        # Build a minimal values dictionary similar to what is passed when
        # creating an attachment.
        values = {
            'raw': bin_data,
            'mimetype': mimetype,
            'name': 'dummy'
        }
        # Process the contents (this may, for instance, resize an image)
        values = attachment_obj._check_contents(values)
        # The processed binary data is stored in 'raw' if available,
        # otherwise in 'datas' (which is base64-encoded)
        processed = values.get('raw')
        if not processed and values.get('datas'):
            processed = base64.b64decode(values['datas'])
        if not processed:
            processed = b''
        return hashlib.sha1(processed).hexdigest()

    @http.route('/api/compute_checksum', type='http', auth='public', methods=['POST'], csrf=False)
    def compute_checksum_api(self, **post):
        """
        API endpoint that reads the uploaded file(s), processes them using
        the same logic as Odoo’s attachment creation, and returns the SHA‑1 checksum.
        """
        try:
            uploaded_files = request.httprequest.files
            if not uploaded_files:
                return http.Response(
                    json.dumps({"error": _("No files uploaded")}),
                    status=400,
                    content_type="application/json"
                )

            response_data = []
            for filename, file_data in uploaded_files.items():
                try:
                    # Read the raw binary content from the uploaded file.
                    bin_data = file_data.read()
                    # Use the provided mimetype (or fallback to empty string)
                    mimetype = file_data.content_type or ''
                    _logger.info("Processing file %s (%d bytes) with mimetype %s",
                                 filename, len(bin_data), mimetype)
                    checksum = self._compute_checksum(bin_data, mimetype)
                    response_data.append({filename: checksum})
                except Exception as file_error:
                    error_message = _("Error processing file %s: %s") % (filename, str(file_error))
                    _logger.error(error_message)
                    return http.Response(
                        json.dumps({"error": error_message}),
                        status=500,
                        content_type="application/json"
                    )

            return http.Response(
                json.dumps(response_data),
                status=200,
                content_type="application/json"
            )

        except Exception as e:
            _logger.exception("Error in compute_checksum_api")
            return http.Response(
                json.dumps({"error": str(e)}),
                status=500,
                content_type="application/json"
            )
