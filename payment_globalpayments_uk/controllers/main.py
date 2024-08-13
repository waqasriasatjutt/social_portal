from odoo import http

class GlobalPaymentsController(http.Controller):

    @http.route('/payment/globalpayments/redirect', type='http', auth='public', website=True)
    def globalpayments_redirect(self, **post):
        payment_url = post.get('payment_url')
        return http.redirect_with_hash(payment_url)
