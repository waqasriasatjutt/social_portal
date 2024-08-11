from odoo import models, fields, api
import hmac
import hashlib
import base64

class PaymentAcquirerGlobalPay(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('globalpay', 'Global Payments')])
    globalpay_merchant_id = fields.Char(string='Merchant ID', required_if_provider='globalpay')
    globalpay_account_id = fields.Char(string='Account ID', default='internet', required_if_provider='globalpay')
    globalpay_shared_secret = fields.Char(string='Shared Secret', required_if_provider='globalpay')
    globalpay_service_url = fields.Char(string='Service URL', default='https://pay.sandbox.realexpayments.com/pay', required_if_provider='globalpay')

    def _generate_signature(self, values):
        """ Generate signature for Global Payments HPP """
        message = ".".join(values[key] for key in sorted(values.keys()))
        signature = hmac.new(self.globalpay_shared_secret.encode(), message.encode(), hashlib.sha256).digest()
        return base64.b64encode(signature).decode()

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
            'MERCHANT_RESPONSE_URL': f"{base_url}/payment/globalpay/return",
            'AUTO_SETTLE_FLAG': '1',
            'HPP_VERSION': '2',
            'HPP_CHANNEL': 'ECOM',
            'HPP_LANG': 'en',
            'HPP_CUSTOMER_EMAIL': values['partner_email'],
            'HPP_CUSTOMER_PHONENUMBER_MOBILE': values['partner_phone'],
            'HPP_BILLING_STREET1': values['billing_address'],
            'HPP_BILLING_CITY': values['billing_city'],
            'HPP_BILLING_POSTALCODE': values['billing_postcode'],
            'HPP_BILLING_COUNTRY': values['billing_country_code'],
            'HPP_SHIPPING_STREET1': values['shipping_address'],
            'HPP_SHIPPING_CITY': values['shipping_city'],
            'HPP_SHIPPING_STATE': values['shipping_state'],
            'HPP_SHIPPING_POSTALCODE': values['shipping_postcode'],
            'HPP_SHIPPING_COUNTRY': values['shipping_country_code'],
        }
        globalpay_tx_values['SHA1HASH'] = self._generate_signature(globalpay_tx_values)
        return globalpay_tx_values

    def globalpay_get_form_action_url(self):
        return self.globalpay_service_url
