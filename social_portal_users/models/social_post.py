from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SocialPost(models.Model):
    _inherit = 'social.post'

    user_id = fields.Many2one(related='account_id.user_id', store=True, readonly=True)

    @api.model
    def create(self, vals):
        account = self.env['social.account'].browse(vals.get('account_id'))
        if account.user_id != self.env.user:
            raise ValidationError("You cannot create a post for an account you do not own.")
        return super(SocialPost, self).create(vals)

    def unlink(self):
        for post in self:
            if post.user_id != self.env.user:
                raise ValidationError("You cannot delete a post that you do not own.")
        return super(SocialPost, self).unlink()
