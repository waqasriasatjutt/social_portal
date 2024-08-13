from odoo import http
from odoo.http import request

class GlobalPayController(http.Controller):
    _return_url = '/payment/globalpay/return'


    @http.route('/shop/payment', type='http', auth='public', website=True, sitemap=False)
    def shop_payment(self, **post):
        return 'https://pay.sandbox.realexpayments.com/pay'

        # """ Payment step. This page proposes several payment means based on available
        # payment.provider. State at this point :

        #  - a draft sales order with lines; otherwise, clean context / session and
        #    back to the shop
        #  - no transaction in context / session, or only a draft one, if the customer
        #    did go to a payment.provider website but closed the tab without
        #    paying / canceling
        # """
        # order = request.website.sale_get_order()

        # if order and (request.httprequest.method == 'POST' or not order.carrier_id):
        #     # Update order's carrier_id (will be the one of the partner if not defined)
        #     # If a carrier_id is (re)defined, redirect to "/shop/payment" (GET method to avoid infinite loop)
        #     carrier_id = post.get('carrier_id')
        #     keep_carrier = post.get('keep_carrier', False)
        #     if keep_carrier:
        #         keep_carrier = bool(int(keep_carrier))
        #     if carrier_id:
        #         carrier_id = int(carrier_id)
        #     order._check_carrier_quotation(force_carrier_id=carrier_id, keep_carrier=keep_carrier)
        #     if carrier_id:
        #         return request.redirect("/shop/payment")

        # redirection = self.checkout_redirection(order) or self.checkout_check_address(order)
        # if redirection:
        #     return redirection

        # render_values = self._get_shop_payment_values(order, **post)
        # render_values['only_services'] = order and order.only_services or False

        # if render_values['errors']:
        #     render_values.pop('payment_methods_sudo', '')
        #     render_values.pop('tokens_sudo', '')

        # return request.render("website_sale.payment", render_values)


    @http.route(_return_url, type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def globalpay_return(self, **post):
        """ Handle the return data sent by Global Payments after checkout. """
        payment_transaction = request.env['payment.transaction'].sudo().search([('reference', '=', post.get('ORDER_ID'))])
        if post.get('RESULT') == '00':
            payment_transaction._set_transaction_done()
        else:
            payment_transaction._set_transaction_cancel()
        return request.redirect('/payment/status')
