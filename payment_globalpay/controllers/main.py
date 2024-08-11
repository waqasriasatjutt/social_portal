from odoo import http
from odoo.http import request

class GlobalPayController(http.Controller):

    @http.route(['/payment/globalpay/return'], type='http', auth='public', csrf=False)
    def globalpay_return(self, **post):
        payment_transaction = request.env['payment.transaction'].sudo().search([('reference', '=', post.get('ORDER_ID'))])
        if post.get('RESULT') == '00':
            payment_transaction._set_transaction_done()
        else:
            payment_transaction._set_transaction_cancel()
        return request.redirect('/payment/process')
