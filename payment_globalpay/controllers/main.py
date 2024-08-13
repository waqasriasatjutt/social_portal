# controllers/main.py
import logging
import pprint

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class GlobalPayController(http.Controller):
    _return_url = '/payment/globalpay/return'
    _webhook_url = '/payment/globalpay/webhook'

    @http.route(
        _return_url, type='http', auth='public', methods=['GET', 'POST'], csrf=False,
        save_session=False
    )
    def globalpay_return_from_checkout(self, **data):
        _logger.info("handling redirection from GlobalPay with data:\n%s", pprint.pformat(data))
        request.env['payment.transaction'].sudo()._handle_notification_data('globalpay', data)
        return request.redirect('/payment/status')

    @http.route(_webhook_url, type='http', auth='public', methods=['POST'], csrf=False)
    def globalpay_webhook(self, **data):
        _logger.info("notification received from GlobalPay with data:\n%s", pprint.pformat(data))
        try:
            request.env['payment.transaction'].sudo()._handle_notification_data('globalpay', data)
        except ValidationError:
            _logger.exception("unable to handle the notification data; skipping to acknowledge")
        return ''  # Acknowledge the notification
