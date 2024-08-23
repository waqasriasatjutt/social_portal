# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class MollieController(http.Controller):
    _return_url = '/payment/mollie/return'
    _webhook_url = '/payment/mollie/webhook'


    @http.route('/payment/globalpay/return', type='http', auth='public', csrf=False)
    def globalpay_return(self, **post):
        # Extract relevant data from the POST request
        result = post.get('RESULT')
        message = post.get('MESSAGE')
        order_id = post.get('ORDER_ID')
        sha1hash = post.get('SHA1HASH')

        # Validate the SHA1HASH to ensure the data is not tampered with
        computed_sha1hash = self._compute_sha1hash(post)
        if sha1hash != computed_sha1hash:
            return request.render('your_module.payment_invalid', {})

        # Find the corresponding sale order
        sale_order = request.env['sale.order'].sudo().search([('name', '=', order_id)], limit=1)

        if not sale_order:
            return request.render('your_module.payment_invalid', {})

        # Check the result and update the order accordingly
        if result == '00':  # Payment successful
            sale_order.action_confirm()
            sale_order.message_post(body=f"Payment successful. Message: {message}")
            return request.render('your_module.payment_success', {'sale_order': sale_order})
        else:  # Payment failed
            sale_order.message_post(body=f"Payment failed. Message: {message}")
            return request.render('your_module.payment_failed', {'sale_order': sale_order})

    def _compute_sha1hash(self, post):
        # Recompute the SHA1 hash to validate the integrity of the data
        # Ensure that the keys are in the correct order as per the documentation
        to_hash = f"{post.get('TIMESTAMP')}." \
                  f"{post.get('MERCHANT_ID')}." \
                  f"{post.get('ORDER_ID')}." \
                  f"{post.get('AMOUNT')}." \
                  f"{post.get('CURRENCY')}." \
                  f"{post.get('RESULT')}." \
                  f"{post.get('MESSAGE')}." \
                  f"{post.get('PASREF')}." \
                  f"{post.get('AUTHCODE')}"
        secret_key = request.env['ir.config_parameter'].sudo().get_param('globalpay.secret_key')
        sha1 = hashlib.sha1(to_hash.encode('utf-8')).hexdigest()
        sha1hash = hashlib.sha1(f"{sha1}.{secret_key}".encode('utf-8')).hexdigest().upper()
        return sha1hash

    @http.route(
        _return_url, type='http', auth='public', methods=['GET', 'POST'], csrf=False,
        save_session=False
    )
    def mollie_return_from_checkout(self, **data):
        """ Process the notification data sent by Mollie after redirection from checkout.

        The route is flagged with `save_session=False` to prevent Odoo from assigning a new session
        to the user if they are redirected to this route with a POST request. Indeed, as the session
        cookie is created without a `SameSite` attribute, some browsers that don't implement the
        recommended default `SameSite=Lax` behavior will not include the cookie in the redirection
        request from the payment provider to Odoo. As the redirection to the '/payment/status' page
        will satisfy any specification of the `SameSite` attribute, the session of the user will be
        retrieved and with it the transaction which will be immediately post-processed.

        :param dict data: The notification data (only `id`) and the transaction reference (`ref`)
                          embedded in the return URL
        """
        _logger.info("handling redirection from Mollie with data:\n%s", pprint.pformat(data))
        request.env['payment.transaction'].sudo()._handle_notification_data('globalpay', data)
        return request.redirect('/payment/status')

    @http.route(_webhook_url, type='http', auth='public', methods=['POST'], csrf=False)
    def mollie_webhook(self, **data):
        """ Process the notification data sent by Mollie to the webhook.

        :param dict data: The notification data (only `id`) and the transaction reference (`ref`)
                          embedded in the return URL
        :return: An empty string to acknowledge the notification
        :rtype: str
        """
        _logger.info("notification received from Mollie with data:\n%s", pprint.pformat(data))
        try:
            request.env['payment.transaction'].sudo()._handle_notification_data('globalpay', data)
        except ValidationError:  # Acknowledge the notification to avoid getting spammed
            _logger.exception("unable to handle the notification data; skipping to acknowledge")
        return ''  # Acknowledge the notification
