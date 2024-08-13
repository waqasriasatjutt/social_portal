from odoo import models, fields, api
import hmac
import hashlib
import base64

class PaymentProviderGlobalPay(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('globalpay', "Global Payments")], ondelete={'globalpay': 'set default'})
    globalpay_merchant_id = fields.Char(string='Merchant ID', required_if_provider='globalpay')
    globalpay_account_id = fields.Char(string='Account ID', required_if_provider='globalpay')
    globalpay_shared_secret = fields.Char(string='Shared Secret', required_if_provider='globalpay', groups='base.group_system')
    globalpay_service_url = fields.Char(string='Service URL', required_if_provider='globalpay', default='https://pay.sandbox.realexpayments.com/pay')

    def _generate_signature(self, values):
        """ Generate signature for Global Payments HPP """
        message = ".".join(values[key] for key in sorted(values.keys()))
        signature = hmac.new(self.globalpay_shared_secret.encode(), message.encode(), hashlib.sha256).digest()
        return base64.b64encode(signature).decode()

    def _send_payment_request(self):
        """ Override of payment to simulate a payment request.

        Note: self.ensure_one()

        :return: None
        """
        super()._send_payment_request()
        if self.provider_code != 'demo':
            return 'https://pay.sandbox.realexpayments.com/pay'

        if not self.token_id:
            return 'https://pay.sandbox.realexpayments.com/pay'

        return 'https://pay.sandbox.realexpayments.com/pay'


    def _globalpay_get_api_url(self):
        if self.state == 'enabled':
            return self.globalpay_service_url
        else:  # For testing purposes
            return 'https://pay.sandbox.realexpayments.com/pay'

    def globalpay_form_generate_values(self, values):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        globalpay_tx_values = {
            'MERCHANT_ID': self.globalpay_merchant_id,
            'ACCOUNT': self.globalpay_account_id,
            'ORDER_ID': values['reference'],
            'AMOUNT': str(int(values['amount'] * 100)),  # Amount in cents
            'CURRENCY': values['currency'].name,
            'TIMESTAMP': fields.Datetime.now().strftime('%Y%m%d%H%M%S'),
            'RETURN_URL': f"{base_url}/payment/globalpay/return",
            'AUTO_SETTLE_FLAG': '1',
            'HPP_VERSION': '2',
            'HPP_CHANNEL': 'ECOM',
            'HPP_LANG': 'en',
            'HPP_CUSTOMER_EMAIL': values.get('partner_email'),
            'HPP_CUSTOMER_PHONENUMBER_MOBILE': values.get('partner_phone'),
        }
        globalpay_tx_values['SHA1HASH'] = self._generate_signature(globalpay_tx_values)
        return globalpay_tx_values

    def _get_default_payment_method_codes(self):
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'globalpay':
            return default_codes
        return ['card']  # Replace with appropriate codes if needed
