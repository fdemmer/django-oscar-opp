# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from decimal import Decimal as D

from django.conf import settings
from django.template.loader import get_template

from .gateway import Gateway
from ..exceptions import OpenPaymentPlatformError
from ..models import PaymentStatusCode, Transaction

logger = logging.getLogger('opp')


def get_result(data):
    result = data.get('result', {})
    return result.get('code'), result.get('description')


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

    def prepare_checkout(self, amount, currency,
                         payment_type='DB',
                         merchant_invoice_id=None,
                         merchant_transaction_id=None,
                         ):
        """
        COPYandPAY step 1: Prepare the checkout

        https://docs.oppwa.com/tutorials/integration-guide#CNPStep1

        :param amount:
        :param currency:
        :param payment_type: default: 'DB'
        :param merchant_invoice_id:
        :param merchant_transaction_id:
        :return:
        """
        if not self.transaction:
            response = self.gateway.get_checkout_id(
                amount=D(amount),
                currency=currency,
                payment_type=payment_type,
                merchant_transaction_id=merchant_transaction_id,
                merchant_invoice_id=merchant_invoice_id,
            )
            self.transaction = Transaction(
                amount=amount,
                currency=currency,
                raw_request=response.request.body,
                raw_response=response.content,
                response_time=response.elapsed.total_seconds() * 1000,
                correlation_id=merchant_invoice_id,
            )
            if response.ok:
                data = response.json()
                checkout_id = data.get('id')
                result_code, result_description = get_result(data)

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
        """
        COPYandPAY step 3: Get the payment status

        https://docs.oppwa.com/tutorials/integration-guide#CNPStep3

        :return:
        """
        response = self.gateway.get_payment_status(self.transaction.checkout_id)
        result_code = response.json().get('result', {}).get('code')
        logger.debug('get_payment_status: code=%s', result_code)

        try:
            return PaymentStatusCode(result_code)
        except ValueError:
            # response doesn't contain valid JSON or the result_code is unknown
            return PaymentStatusCode.UNKNOWN_ERROR

    def get_payment_brands(self, payment_method=None):
        payment_method = payment_method \
            if payment_method else settings.DEFAULT_PAYMENT_METHOD
        return settings.OPP_PAYMENT_METHODS.get(payment_method)

    def get_form(self, callback, locale, payment_method=None, address=None):
        """
        COPYandPAY step 2: Create the payment form

        https://docs.oppwa.com/tutorials/integration-guide#CNPStep2

        :param callback:
        :param locale:
        :param payment_method:
        :param address:
        :return:
        """
        ctx = {
            'checkout_id': self.transaction.checkout_id,
            'locale': locale,
            'address': address,
            'payment_method': self.get_payment_brands(payment_method),
            'shopper_result_url': callback,
            'gateway_host': self.gateway.host,
        }
        template = get_template('oscar_opp/form.html')
        return template.render(ctx)
