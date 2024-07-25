from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ServiceDispatchWizard(models.TransientModel):
    _name = 'service.dispatch.wizard'
    _description = 'Service Dispatch Wizard'

    service_id = fields.Many2one('aaa.service', string="Service")
    # message = fields.Text(string="Message", default="Service not in package, proceed with cash/credit service?")

    def action_cash_service(self):
        self.service_id.write({
            'type': 'cash',
            'state': 'dispatch'
        })
        # self.service_id.message_post(body=_("Service dispatched as cash service."))
        self.create_service_history()
        return {'type': 'ir.actions.act_window_close'}

    def action_credit_service(self):
        self.service_id.write({
            'member_type': 'credit',
            'state': 'dispatch'
        })
        # self.service_id.message_post(body=_("Service dispatched as credit service."))
        self.create_service_history()
        return {'type': 'ir.actions.act_window_close'}

    def create_service_history(self):
        self.env['service.history'].create({
            'service_id': self.service_id.id,
            'user': self.env.user.id,
            'time': fields.Datetime.now(),
            'status': self.service_id.state,
        })