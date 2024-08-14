# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint
from odoo.http import request


from werkzeug import urls

from odoo import _, models
from odoo.exceptions import ValidationError

from odoo.addons.payment_globalpay import const
from odoo.addons.payment_globalpay.controllers.main import MollieController


_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'


    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return Global Payments-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific rendering values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'globalpay':
            return res

        # Prepare the payload with the required fields
        payload = {
            'TIMESTAMP': self._get_timestamp(),  # Custom method to generate the timestamp
            'MERCHANT_ID': "MER_7e3e2c7df34f42819b3edee31022ee3f",
            'ACCOUNT': 'internet',
            'ORDER_ID': self.reference,  # Typically the order or transaction reference
            'AMOUNT': int(self.amount * 100),  # Convert amount to smallest currency unit (e.g., cents)
            'CURRENCY': self.currency_id.name,
            'SHA1HASH': self._generate_sha1_hash(),  # Custom method to generate the SHA1 hash
            'HPP_VERSION': '2',
            'HPP_CUSTOMER_COUNTRY': self.partner_country_id.code,  # Assuming country code is stored in the partner
            'HPP_CUSTOMER_FIRSTNAME': self.partner_first_name,  # Assuming partner first name is available
            'HPP_CUSTOMER_LASTNAME': self.partner_last_name,  # Assuming partner last name is available
            'MERCHANT_RESPONSE_URL': "http://165.227.98.165:8029/web",  # URL for response handling
            'HPP_TX_STATUS_URL': "http://165.227.98.165:8029/web",  # URL for transaction status handling
            'PM_METHODS': 'cards|paypal|testpay|sepapm|sofort',
        }

        # Return the URL and POST parameters for rendering
        return {
            'api_url': 'https://pay.sandbox.realexpayments.com/pay',
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
