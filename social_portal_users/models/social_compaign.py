from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SocialCampaign(models.Model):
    _inherit = 'utm.campaign'  # Ensure this is the correct model name for Odoo 17

    user_id = fields.Many2one('res.users', string='Owner', default=lambda self: self.env.user, required=True)

    @api.model
    def create(self, vals):
        vals['user_id'] = self.env.user.id
        return super(SocialCampaign, self).create(vals)

    def unlink(self):
        for campaign in self:
            if campaign.user_id != self.env.user:
                raise ValidationError("You cannot delete a campaign that you do not own.")
        return super(SocialCampaign, self).unlink()
