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
        """
        Initialize OPP COPYandPAY facade.

        A `checkout_id` must be given to continue in step 3.
        It is initially retrieved and set in step 1 (prepare_checkout).

        :param checkout_id:
        """
        self.gateway = Gateway(
            host=settings.OPP_BASE_URL,
            auth_userid=settings.OPP_USER_ID,
            auth_entityid=settings.OPP_ENTITY_ID,
            auth_password=settings.OPP_PASSWORD,
        )
        self.transaction = None
        if checkout_id:
            self.transaction = Transaction.objects.get(checkout_id=checkout_id)

    @property
    def entity_id(self):
        if self.transaction:
            return self.transaction.entity_id

    @property
    def currency(self):
        if self.transaction:
            return self.transaction.currency

    @property
    def amount(self):
        if self.transaction:
            return self.transaction.amount

    def _update_transaction(self, **kwargs):
        """
        Update self.transaction with the given kwargs.

        :param commit: save transaction after update, default: False
        :param kwargs:
        :return: None
        """
        commit = kwargs.pop('commit', False)
        for key, value in kwargs.items():
            setattr(self.transaction, key, value)
        if commit:
            self.transaction.save()

    def prepare_checkout(
            self, amount, currency,
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
        if self.transaction:
            raise OpenPaymentPlatformError(
                "This instance is already linked to a Transaction"
            )

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

        if not response.ok:
            logger.error('prepare_checkout: %s', response.status_code)
        else:
            data = response.json()
            checkout_id = data.get('id')
            result_code, result_description = get_result(data)

            logger.info('prepare_checkout success: checkout_id="%s", '
                        'result_code="%s", result_description="%s"',
                         checkout_id, result_code, result_description)
            self._update_transaction(
                checkout_id=checkout_id,
                result_code=result_code,
                result_description=result_description,
            )

        self.transaction.save()

    def get_payment_status(self):
        """
        COPYandPAY step 3: Get the payment status

        https://docs.oppwa.com/tutorials/integration-guide#CNPStep3

        :return:
        """
        response = self.gateway.get_payment_status(self.transaction.checkout_id)
        if not response.ok:
            logger.error(
                'get_payment_status failed: checkout_id="%s", status_code=%s',
                self.transaction.checkout_id,
                response.status_code,
            )
            # TODO maybe return tuple with status and data?
            return PaymentStatusCode.UNKNOWN_ERROR

        data = response.json()
        entity_id = data.get('id')
        #paymentBrand = data.get('paymentBrand')
        result_code, result_description = get_result(data)
        logger.info(
            'get_payment_status success: checkout_id="%s", entity_id="%s", '
            'result_code="%s", result_description="%s"',
            self.transaction.checkout_id, entity_id, result_code,
            result_description,
        )

        self._update_transaction(
            # save payment transaction entity id (used in notifications)
            entity_id=entity_id,
            # overwrite fields with data from step 1
            result_code=result_code,
            result_description=result_description,
            raw_request=response.request.body or '',
            raw_response=response.content,
            response_time=response.elapsed.total_seconds() * 1000,
            # save
            commit=True,
        )

        try:
            # TODO maybe return tuple with status and data?
            return PaymentStatusCode(result_code)
        except ValueError:
            logger.warning('unknown result_code: %s', result_code)
            return PaymentStatusCode.UNKNOWN_ERROR

    def get_payment_brands(self, payment_method=None):
        # TODO settings should probably be loaded more careful, with defaults
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
