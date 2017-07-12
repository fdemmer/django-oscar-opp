# -*- coding: utf-8 -*-

from decimal import Decimal as D

from django.conf import settings
from django.template.loader import get_template

from ..exceptions import OpenPaymentPlatformError
from ..models import Transaction
from .gateway import Gateway


class Facade(object):

    PAYMENT_METHODS = {
        'opp_card': 'VISA MASTER AMEX',
        'opp_eps': 'EPS'

    }


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

    def prepare_checkout(self, amount, currency, correlation_id=None):
        if not self.transaction:
            response = self.gateway.get_checkout_id(
                amount=D(amount),
                currency=currency,
                payment_type='DB'
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
                self.transaction.checkout_id = response.json().get('id')
                self.transaction.result_code = response.json().get('result')['code']
            else:
                # add error handling
                pass
            self.transaction.save()

        else:
            raise OpenPaymentPlatformError(
                "This instance is already linked to a Transaction"
            )

    def get_payment_status(self):
        return self.gateway.get_payment_status(self.transaction.checkout_id)

    def get_form(self, callback, locale, payment_method=None, address=None):

        payment_method = self.PAYMENT_METHODS.get(
            payment_method,
            self.PAYMENT_METHODS.get('opp_card')
        )

        ctx = {
            'checkout_id': self.transaction.checkout_id,
            'locale': locale,
            'address': address,
            'payment_method': payment_method,
            'callback': callback,
        }
        template = get_template('oscar_opp/form.html')
        return template.render(ctx)
