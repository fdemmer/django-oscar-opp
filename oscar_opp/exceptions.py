# -*- coding: utf-8 -*-
from __future__ import unicode_literals


try:
    from oscar.apps.payment.exceptions import PaymentError
except ImportError:
    class PaymentError(Exception):
        pass


class OpenPaymentPlatformError(PaymentError):
    pass
