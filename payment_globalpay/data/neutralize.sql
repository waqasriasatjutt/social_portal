-- disable mollie payment provider
UPDATE payment_provider
   SET global_api_key = NULL;
