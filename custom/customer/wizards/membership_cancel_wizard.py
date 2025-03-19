from odoo import models , fields , api

class MembershipCancelWizard(models.TransientModel):
    _name = 'membership.cancel.wizard'
    _description = 'Membership Cancellation Wizard'

    cancel_date = fields.Date('Cancel Date')
    comment = fields.Text('comment')

    def action_cancel(self):
        partner = self.env['res.partner'].browse(self._context.get('active_id'))
        self.env['membership.timeline'].create({
            'member_id': partner.id,
            'user': self.env.user.id,
            'time': fields.Datetime.now(),
            'status': 'Membership Cancelled',
            'timeline_status': 'cancel',
        })
        partner.write({
            'membership_state': 'cancel',
            'membership_cancel_date': self.cancel_date,
            'cancellation_comment': self.comment,
        })