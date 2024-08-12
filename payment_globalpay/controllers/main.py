from odoo import http
from odoo.http import request

class GlobalPayController(http.Controller):
    _return_url = '/payment/globalpay/return'

    @http.route(_return_url, type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def globalpay_return(self, **post):
        """ Handle the return data sent by Global Payments after checkout. """
        payment_transaction = request.env['payment.transaction'].sudo().search([('reference', '=', post.get('ORDER_ID'))])
        if post.get('RESULT') == '00':
            payment_transaction._set_transaction_done()
        else:
            payment_transaction._set_transaction_cancel()
        return request.redirect('/payment/status')
