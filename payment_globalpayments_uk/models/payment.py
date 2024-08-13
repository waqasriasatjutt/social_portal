from odoo import models, fields, api
import logging
import requests

_logger = logging.getLogger(__name__)

class PaymentAcquirerGlobalPayments(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('globalpayments_uk', 'Global Payments UK')])

    globalpayments_api_key = fields.Char(string="Global Payments API Key")
    globalpayments_environment = fields.Selection([
        ('test', 'Test'),
        ('production', 'Production')
    ], string="Environment", default='test')

    def _get_globalpayments_urls(self):
        if self.globalpayments_environment == 'test':
            return "https://api.sandbox.globalpay.com"
        return "https://api.globalpay.com"

    def globalpayments_form_generate_values(self, values):
        self.ensure_one()
        base_url = self._get_globalpayments_urls()

        payment_data = {
            'amount': values['amount'],
            'currency': values['currency'] and values['currency'].name or '',
            'return_url': values['return_url'],
            # Add more fields as required by the Global Payments API
        }

        response = requests.post(
            f"{base_url}/v1/payments",
            headers={
                "Authorization": f"Bearer {self.globalpayments_api_key}",
                "Content-Type": "application/json"
            },
            json=payment_data
        )

        if response.status_code == 200:
            result = response.json()
            values.update({
                'payment_url': result['payment_url'],
                'reference': result['reference']
            })
        else:
            _logger.error("Global Payments error: %s", response.text)
            raise ValueError("Error in processing the payment with Global Payments")

        return values

    def globalpayments_get_form_action_url(self):
        return "/payment/globalpayments/redirect"

class PaymentTransactionGlobalPayments(models.Model):
    _inherit = 'payment.transaction'

    def _globalpayments_form_get_tx_from_data(self, data):
        reference = data.get('reference')
        transaction = self.search([('reference', '=', reference)])
        if not transaction:
            _logger.error('Global Payments: Transaction with reference %s not found', reference)
            return None
        return transaction

    def _globalpayments_form_validate(self, data):
        self.ensure_one()
        status = data.get('status')
        if status == 'succeeded':
            self._set_done()
        elif status == 'failed':
            self._set_canceled()
        else:
            self._set_error("Payment status unknown.")
        return True
