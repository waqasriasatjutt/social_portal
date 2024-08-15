# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint
from odoo.http import request

import hashlib

from werkzeug import urls

from odoo import _, models
from odoo.exceptions import ValidationError

from odoo.addons.payment_globalpay import const
from odoo.addons.payment_globalpay.controllers.main import MollieController

from datetime import datetime  # Import datetime

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'


    def _get_timestamp(self):
        """Generate a timestamp in the format YYYYMMDDHHMMSS."""
        return datetime.utcnow().strftime('%Y%m%d%H%M%S')


    def _generate_sha1_hash(self):
        """Generate the SHA1 hash required for the payment request."""
        # Concatenate the required fields to form the string to hash
        sha_string = "".join([
            self._get_timestamp(),
            "baburrestaurant",
            self.reference,  # Assuming reference is the ORDER_ID
            str(int(self.amount * 100)),  # Amount in the smallest unit
            self.currency_id.name,
            "baburrestaurant"  # The secret key provided by Global Payments
        ])
        
        # Generate the SHA1 hash
        hash_object = hashlib.sha1(sha_string.encode('utf-8'))
        sha1hash = hash_object.hexdigest()

        return sha1hash.upper()  # Return the hash in uppercase as required by some gateways

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'globalpay':
            return res

        # Prepare the payload
        payload = {
            'TIMESTAMP': self._get_timestamp(),
            'MERCHANT_ID': "baburrestaurant",
            'ACCOUNT': 'internet',
            'ORDER_ID': self.reference,
            'AMOUNT': int(self.amount * 100),
            'CURRENCY': self.currency_id.name,
            'SHA1HASH': "308bb8dfbbfcc67c28d602d988ab104c3b08d012",
            'HPP_VERSION': '2',
            'HPP_CUSTOMER_COUNTRY': self.partner_country_id.code,
            'HPP_CUSTOMER_FIRSTNAME': self.partner_id.name.split()[0] if self.partner_id.name else '',
            'HPP_CUSTOMER_LASTNAME': ' '.join(self.partner_id.name.split()[1:]) if self.partner_id.name else '',
            'MERCHANT_RESPONSE_URL': "http://165.227.98.165:8029/web",
            'HPP_TX_STATUS_URL': "http://165.227.98.165:8029/web",
            'PM_METHODS': 'cards|paypal|testpay|sepapm|sofort',
        }

        _logger.info("GlobalPay Payload: %s", pprint.pformat(payload))

        return {
            'api_url': 'https://pay.sandbox.realexpayments.com/pay',
            'url_params': payload,
            'post_params': payload,
        }

    # def _get_specific_rendering_values(self, processing_values):
    #     """ Override of payment to return Mollie-specific rendering values.

    #     Note: self.ensure_one() from `_get_processing_values`

    #     :param dict processing_values: The generic and specific processing values of the transaction
    #     :return: The dict of provider-specific rendering values
    #     :rtype: dict
    #     """
    #     res = super()._get_specific_rendering_values(processing_values)
    #     if self.provider_code != 'globalpay':
    #         return res

    #     payload = self._globalpay_prepare_payment_request_payload()
    #     _logger.info("sending '/payments' request for link creation:\n%s", pprint.pformat(payload))
    #     return request.redirect('https://pay.sandbox.realexpayments.com/pay')
        # payment_data = self.provider_id._globalpay_make_request('/payments', data=payload)

        # # The provider reference is set now to allow fetching the payment status after redirection
        # self.provider_reference = payment_data.get('id')

        # # Extract the checkout URL from the payment data and add it with its query parameters to the
        # # rendering values. Passing the query parameters separately is necessary to prevent them
        # # from being stripped off when redirecting the user to the checkout URL, which can happen
        # # when only one payment method is enabled on Mollie and query parameters are provided.
        # checkout_url = payment_data['_links']['checkout']['href']
        # parsed_url = urls.url_parse(checkout_url)
        # url_params = urls.url_decode(parsed_url.query)
        # return {'api_url': checkout_url, 'url_params': url_params}

    def _globalpay_prepare_payment_request_payload(self):
        """ Create the payload for the payment request based on the transaction values.

        :return: The request payload
        :rtype: dict
        """
        user_lang = self.env.context.get('lang')
        base_url = self.provider_id.get_base_url()
        redirect_url = urls.url_join(base_url, MollieController._return_url)
        webhook_url = urls.url_join(base_url, MollieController._webhook_url)

        return {
            'description': self.reference,
            'amount': {
                'currency': self.currency_id.name,
                'value': f"{self.amount:.2f}",
            },
            'locale': user_lang if user_lang in const.SUPPORTED_LOCALES else 'en_US',
            'method': [const.PAYMENT_METHODS_MAPPING.get(
                self.payment_method_code, self.payment_method_code
            )],
            # Since Mollie does not provide the transaction reference when returning from
            # redirection, we include it in the redirect URL to be able to match the transaction.
            'redirectUrl': f'{redirect_url}?ref={self.reference}',
            'webhookUrl': f'{webhook_url}?ref={self.reference}',
        }

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override of payment to find the transaction based on Mollie data.

        :param str provider_code: The code of the provider that handled the transaction
        :param dict notification_data: The notification data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
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
        """ Override of payment to process the transaction based on Mollie data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider
        :return: None
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'globalpay':
            return

        payment_data = self.provider_id._globalpay_make_request(
            f'/payments/{self.provider_reference}', method="GET"
        )

        # Update the payment method.
        payment_method_type = payment_data.get('method', '')
        if payment_method_type == 'creditcard':
            payment_method_type = payment_data.get('details', {}).get('cardLabel', '').lower()
        payment_method = self.env['payment.method']._get_from_code(
            payment_method_type, mapping=const.PAYMENT_METHODS_MAPPING
        )
        self.payment_method_id = payment_method or self.payment_method_id

        # Update the payment state.
        payment_status = payment_data.get('status')
        if payment_status == 'pending':
            self._set_pending()
        elif payment_status == 'authorized':
            self._set_authorized()
        elif payment_status == 'paid':
            self._set_done()
        elif payment_status in ['expired', 'canceled', 'failed']:
            self._set_canceled("GlobalPay: " + _("Canceled payment with status: %s", payment_status))
        else:
            _logger.info(
                "received data with invalid payment status (%s) for transaction with reference %s",
                payment_status, self.reference
            )
            self._set_error(
                "GlobalPay: " + _("Received data with invalid payment status: %s", payment_status)
            )
