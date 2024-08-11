from odoo import models, fields

class SocialAccount(models.Model):
    _inherit = 'social.account'

    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, required=True)

class SocialCampaign(models.Model):
    _inherit = 'social.campaign'

    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, required=True)
