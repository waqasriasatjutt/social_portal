# models/payment_provider.py
import logging
import requests
import pprint

from odoo import _, fields, models
from odoo.exceptions import ValidationError
from werkzeug import urls

_logger = logging.getLogger(__name__)

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('globalpay', 'Global Payments')], ondelete={'globalpay': 'set default'}
    )
    globalpay_merchant_id = fields.Char(
        string="Merchant ID",
        help="The Merchant ID provided by Global Payments",
        required_if_provider="globalpay", groups="base.group_system"
    )
    globalpay_account_id = fields.Char(
        string="Account ID",
        help="The Account ID provided by Global Payments",
        required_if_provider="globalpay", groups="base.group_system"
    )
    globalpay_shared_secret = fields.Char(
        string="Shared Secret", required_if_provider='globalpay', groups="base.group_system"
    )
    globalpay_service_url = fields.Char(
        string="Service URL", default="https://pay.sandbox.realexpayments.com/pay",
        required_if_provider='globalpay', groups="base.group_system"
    )

    def _get_supported_currencies(self):
        supported_currencies = super()._get_supported_currencies()
        if self.code == 'globalpay':
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in ['EUR', 'USD', 'GBP']
            )
        return supported_currencies

    def _globalpay_make_request(self, endpoint, data=None, method='POST'):
        self.ensure_one()
        url = urls.url_join(self.globalpay_service_url, endpoint)

        headers = {
            "Accept": "application/json",
            "Authorization": f'Bearer {self.globalpay_shared_secret}',
            "Content-Type": "application/json",
        }

        try:
            response = requests.request(method, url, json=data, headers=headers, timeout=60)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                _logger.exception(
                    "Invalid API request at %s with data:\n%s", url, pprint.pformat(data)
                )
                raise ValidationError(
                    "GlobalPay: " + _(
                        "The communication with the API failed. GlobalPay gave us the following "
                        "information: %s", response.json().get('detail', '')
                    ))
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            _logger.exception("Unable to reach endpoint at %s", url)
            raise ValidationError(
                "GlobalPay: " + _("Could not establish the connection to the API.")
            )
        return response.json()

    def _get_default_payment_method_codes(self):
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'globalpay':
            return default_codes
        return ['creditcard', 'debitcard']
