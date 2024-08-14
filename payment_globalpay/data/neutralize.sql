-- disable mollie payment provider
UPDATE payment_provider
   SET globalpay_api_key = NULL;
