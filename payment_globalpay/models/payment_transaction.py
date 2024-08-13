# models/payment_transaction.py
import logging
import pprint

from werkzeug import urls

from odoo import _, models
from odoo.exceptions import ValidationError

from odoo.addons.payment_globalpay.controllers.main import GlobalPayController

_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        """ Override to return GlobalPay-specific rendering values. """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'globalpay':
            return res

        # Prepare the payload for GlobalPay
        payload = self._globalpay_prepare_payment_request_payload()
        _logger.info("sending payment request with payload:\n%s", pprint.pformat(payload))
        payment_data = self.provider_id._globalpay_make_request('', data=payload)

        # The provider reference is set now to allow fetching the payment status after redirection
        self.provider_reference = payment_data.get('id')

        # Extract the checkout URL from the payment data
        checkout_url = payment_data.get('checkout_url')
        parsed_url = urls.url_parse(checkout_url)
        url_params = urls.url_decode(parsed_url.query)
        return {'api_url': checkout_url, 'url_params': url_params}

    def _globalpay_prepare_payment_request_payload(self):
        """ Create the payload for the payment request based on the transaction values. """
        user_lang = self.env.context.get('lang')
        base_url = self.provider_id.get_base_url()
        redirect_url = urls.url_join(base_url, GlobalPayController._return_url)

        return {
            'MERCHANT_ID': self.provider_id.globalpay_merchant_id,
            'ACCOUNT': self.provider_id.globalpay_account_id,
            'ORDER_ID': self.reference,
            'AMOUNT': str(int(self.amount * 100)),  # Amount in cents
            'CURRENCY': self.currency_id.name,
            'RETURN_URL': f'{redirect_url}?ref={self.reference}',
            'AUTO_SETTLE_FLAG': '1',
            'HPP_VERSION': '2',
            'HPP_CHANNEL': 'ECOM',
            'HPP_LANG': user_lang if user_lang else 'en',
            'HPP_CUSTOMER_EMAIL': self.partner_email,
            'HPP_CUSTOMER_PHONENUMBER_MOBILE': self.partner_phone,
        }

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override to find the transaction based on GlobalPay data. """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'globalpay' or len(tx) == 1:
            return tx

        tx = self.search(
            [('reference', '=', notification_data.get('ref')), ('provider_code', '=', 'globalpay')]
        )
        if not tx:
            raise ValidationError("GlobalPay: " + _(
                "No transaction found matching reference %s.", notification_data.get('ref')
            ))
        return tx

    def _process_notification_data(self, notification_data):
        """ Override to process the transaction based on GlobalPay data. """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'globalpay':
            return

        payment_status = notification_data.get('RESULT')
        if payment_status == '00':
            self._set_done()
        elif payment_status in ['02', '05']:
            self._set_canceled("GlobalPay: " + _("Canceled payment with status: %s", payment_status))
        else:
            _logger.info(
                "received data with invalid payment status (%s) for transaction with reference %s",
                payment_status, self.reference
            )
            self._set_error(
                "GlobalPay: " + _("Received data with invalid payment status: %s", payment_status)
            )
