# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint

import requests
from odoo.http import request
from werkzeug import urls

from odoo import _, fields, models, service
from odoo.exceptions import ValidationError

from odoo.addons.payment_globalpay import const

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('globalpay', 'globalpay')], ondelete={'globalpay': 'set default'}
    )
    globalpay_api_key = fields.Char(
        string="Merchant ID",
        help="The Test or Live API Key depending on the configuration of the provider",
        required_if_provider="globalpay", groups="base.group_system"
    )
    globalpay_shared_secret = fields.Char(
        string="Shared Secret",
        help="The Test or Live API Key depending on the configuration of the provider",
        required_if_provider="globalpay", groups="base.group_system", default="eoPSw5Ts9K"
    )
    globalpay_response_url = fields.Char(
        string="Response URL",
        help="Response URL",
        required_if_provider="globalpay", groups="base.group_system"
    )

    #=== BUSINESS METHODS ===#

    def _get_supported_currencies(self):
        """ Override of `payment` to return the supported currencies. """
        supported_currencies = super()._get_supported_currencies()
        if self.code == 'globalpay':
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in const.SUPPORTED_CURRENCIES
            )
        return supported_currencies

    def _globalpay_make_request(self, endpoint, data=None, method='POST'):
        """ Make a request at globalpay endpoint.

        Note: self.ensure_one()

        :param str endpoint: The endpoint to be reached by the request
        :param dict data: The payload of the request
        :param str method: The HTTP method of the request
        :return The JSON-formatted content of the response
        :rtype: dict
        :raise: ValidationError if an HTTP error occurs
        """
        self.ensure_one()
        # endpoint = f'/v2/{endpoint.strip("/")}'
        # url = urls.url_join('https://api.global.com/', endpoint)

        # odoo_version = service.common.exp_version()['server_version']
        # module_version = self.env.ref('base.module_payment_globalpay').installed_version
        # headers = {
        #     "Accept": "application/json",
        #     "Authorization": f'Bearer {self.globalpay_api_key}',
        #     "Content-Type": "application/json",
        #     # See https://docs.mollie.com/integration-partners/user-agent-strings
        #     "User-Agent": f'Odoo/{odoo_version} MollieNativeOdoo/{module_version}',
        # }
        return request.redirect('https://pay.sandbox.realexpayments.com/pay')
        # try:
        #     response = requests.request(method, url, json=data, headers=headers, timeout=60)
        #     try:
        #         response.raise_for_status()
        #     except requests.exceptions.HTTPError:
        #         _logger.exception(
        #             "Invalid API request at %s with data:\n%s", url, pprint.pformat(data)
        #         )
        #         raise ValidationError(
        #             "GlobalPay: " + _(
        #                 "The communication with the API failed. GlobalPay gave us the following "
        #                 "information: %s", response.json().get('detail', '')
        #             ))
        # except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        #     _logger.exception("Unable to reach endpoint at %s", url)
        #     raise ValidationError(
        #         "GlobalPay: " + _("Could not establish the connection to the API.")
        #     )
        # return response.json()

    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes. """
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'globalpay':
            return default_codes
        return const.DEFAULT_PAYMENT_METHODS_CODES
