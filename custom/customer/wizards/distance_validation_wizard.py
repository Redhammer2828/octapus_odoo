from odoo import models, fields, api, _
from odoo.exceptions import UserError


class DistanceValidationWizard(models.TransientModel):
    _name = 'distance.validation.wizard'
    _description = 'Distance Validation Wizard'

    service_id = fields.Many2one('aaa.service', string='Service', required=True)
    calculated_distance = fields.Float(string='Calculated Distance (KM)', readonly=True)
    distance_limit = fields.Float(string='Distance Limit (KM)', readonly=True)
    from_location = fields.Char(string='From Location', readonly=True)
    to_location = fields.Char(string='To Location', readonly=True)
    message = fields.Html(string='Message', readonly=True)

    @api.model
    def default_get(self, fields_list):
        """Set default values from context"""
        res = super().default_get(fields_list)
        context = self.env.context
        
        if context.get('service_id'):
            res['service_id'] = context['service_id']
        if context.get('calculated_distance'):
            res['calculated_distance'] = context['calculated_distance']
        if context.get('distance_limit'):
            res['distance_limit'] = context['distance_limit']
        if context.get('from_location'):
            res['from_location'] = context['from_location']
        if context.get('to_location'):
            res['to_location'] = context['to_location']
            
        # Create message
        if res.get('calculated_distance') and res.get('distance_limit'):
            message = f"""
            <div style="text-align: center; padding: 20px;">
                <h3 style="color: #d9534f;">Distance Limit Exceeded</h3>
                <p><strong>From:</strong> {res.get('from_location', 'N/A')}</p>
                <p><strong>To:</strong> {res.get('to_location', 'N/A')}</p>
                <p><strong>Calculated Distance:</strong> <span style="color: #d9534f; font-weight: bold;">{res['calculated_distance']:.2f} KM</span></p>
                <p><strong>Allowed Distance:</strong> <span style="color: #5cb85c; font-weight: bold;">{res['distance_limit']:.2f} KM</span></p>
                <p style="margin-top: 20px;">The calculated distance exceeds the allowed limit. What would you like to do?</p>
            </div>
            """
            res['message'] = message
            
        return res

    def action_proceed(self):
        """Allow the service to proceed despite distance limit"""
        if self.service_id:
            # Mark service as having distance override
            # self.service_id.write({
            #     'comments': (self.service_id.comments or '') + 
            #                f"\n[Distance Override] Proceeded with {self.calculated_distance:.2f}KM (Limit: {self.distance_limit:.2f}KM)"
            # })

            message = _((self.service_id.comments or '') + 
                        f"\nProceeded with {self.calculated_distance:.2f}KM (Limit: {self.distance_limit:.2f}KM)")
            
            
            # Continue with the dispatch process by calling _dispatch_service directly
            self.service_id._dispatch_service()
            
            # Return action to close wizard and refresh the service form
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Distance Override'),
                    'message': message,
                    'type': 'info',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'}
                }
            }
        
        return {'type': 'ir.actions.act_window_close'}

    def action_restrict(self):
        """Restrict the service due to distance limit"""

        message = _((self.service_id.comments or '') + 
                    f"\nService restricted due to {self.calculated_distance:.2f}KM exceeding limit of {self.distance_limit:.2f}KM")
        
        # Display notification and close wizard
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Distance Restriction'),
                'message': message,
                'type': 'info',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }
    
        # if self.service_id:
        #     # Add comment about restriction
        #     self.service_id.write({
        #         'comments': (self.service_id.comments or '') + 
        #                    f"\n[Distance Restriction] Service restricted due to {self.calculated_distance:.2f}KM exceeding limit of {self.distance_limit:.2f}KM"
        #     })
        
        # Close wizard and show error
        # raise UserError(f"Service restricted: Distance {self.calculated_distance:.2f}KM exceeds the allowed limit of {self.distance_limit:.2f}KM for same emirate services.")