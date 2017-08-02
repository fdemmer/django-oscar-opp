# -*- coding: utf-8 -*-
import logging
from decimal import Decimal as D

from django.conf import settings
from django.template.loader import get_template

from .gateway import Gateway
from ..exceptions import OpenPaymentPlatformError
from ..models import Transaction

logger = logging.getLogger('opp')


class Facade(object):
    def __init__(self, checkout_id=None):
        self.gateway = Gateway(
            host=settings.OPP_BASE_URL,
            auth_userid=settings.OPP_USER_ID,
            auth_entityid=settings.OPP_ENTITY_ID,
            auth_password=settings.OPP_PASSWORD
        )
        if checkout_id:
            self.transaction = Transaction.objects.get(
                checkout_id=checkout_id,
            )
        else:
            self.transaction = None

    def prepare_checkout(self, amount, currency, correlation_id=None,
                         merchant_transaction_id=None):
        if not self.transaction:
            response = self.gateway.get_checkout_id(
                amount=D(amount),
                currency=currency,
                payment_type='DB',
                merchant_transaction_id=merchant_transaction_id,
                merchant_invoice_id=correlation_id,
            )
            self.transaction = Transaction(
                amount=amount,
                currency=currency,
                raw_request=response.request.body,
                raw_response=response.content,
                response_time=response.elapsed.total_seconds() * 1000,
                correlation_id=correlation_id,
            )
            if response.ok:
                data = response.json()
                checkout_id = data.get('id')
                result = data.get('result', {})
                result_code = result.get('code')
                result_description = result.get('description')

                logger.debug('prepare_checkout success: id=%s, code=%s "%s"',
                             checkout_id, result_code, result_description)
                self.transaction.checkout_id = checkout_id
                self.transaction.result_code = result_code
                self.transaction.result_description = result_description
            else:
                #TODO: Add error handling
                pass
            self.transaction.save()

        else:
            raise OpenPaymentPlatformError(
                "This instance is already linked to a Transaction"
            )

    def get_payment_status(self):
        response = self.gateway.get_payment_status(self.transaction.checkout_id)

        data = response.json()
        result = data.get('result', {})
        result_code = result.get('code')

        self.transaction.result_code = result.get('code')
        self.transaction.result_description = result.get('description')
        self.transaction.save()
        logger.debug('get_payment_status success: code=%s', result_code)

        return self.transaction.is_success

    @property
    def payment_status(self):
        return self.transaction.result_code, self.transaction.result_description

    def get_payment_brands(self, payment_method=None):
        payment_method = payment_method \
            if payment_method else settings.DEFAULT_PAYMENT_METHOD
        return settings.OPP_PAYMENT_METHODS.get(payment_method)

    def get_form(self, callback, locale, payment_method=None, address=None):
        ctx = {
            'checkout_id': self.transaction.checkout_id,
            'locale': locale,
            'address': address,
            'payment_method': self.get_payment_brands(payment_method),
            'callback': callback,
            'gateway_host': self.gateway.host,
        }
        template = get_template('oscar_opp/form.html')
        return template.render(ctx)
