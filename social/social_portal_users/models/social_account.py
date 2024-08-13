from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SocialAccount(models.Model):
    _inherit = 'social.account'

    user_id = fields.Many2one('res.users', string='Owner', default=lambda self: self.env.user, required=True)

    @api.model
    def create(self, vals):
        vals['user_id'] = self.env.user.id
        return super(SocialAccount, self).create(vals)

    def write(self, vals):
        if 'user_id' in vals and vals['user_id'] != self.env.user.id:
            raise ValidationError("You cannot change the owner of this social account.")
        return super(SocialAccount, self).write(vals)

    def unlink(self):
        for account in self:
            if account.user_id != self.env.user:
                raise ValidationError("You cannot delete an account that you do not own.")
        return super(SocialAccount, self).unlink()
