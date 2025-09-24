from odoo import http
from odoo.http import request

class RealtimeUpdateController(http.Controller):

    @http.route('/api/notify_users', type='http', auth='public', methods=['POST'], csrf=False)
    def notify_users(self, **kwargs):
        import json
        try:
            data = json.loads(request.httprequest.data.decode())  # raw JSON body
            service_number = data.get('service_number')
            if not service_number:
                return request.make_json_response({"status": "error", "message": "Missing Service Number"}, status=400)

            record = request.env['aaa.service'].sudo().search([('name', '=', service_number)], limit=1)
            if not record:
                return request.make_json_response({"status": "error", "message": "Service not found"}, status=404)

            # Broadcast bus event
            request.env["bus.bus"].sudo()._sendone(
                "broadcast",
                "page_refresh",
                {
                    "record_id": record.id,
                    "model_name": "aaa.service",
                },
            )

            return request.make_json_response({"status": "success", "message": f"Notification sent for {service_number}"}, status=200)

        except Exception as e:
            return request.make_json_response({"status": "error", "message": str(e)}, status=500)

