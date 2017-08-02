# -*- coding: utf-8 -*-
import re

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from . import base

SUCCESS = '000.000.100'
SUCCESS_INTEGRATOR_TEST_MODE = '000.100.110'
SUCCESS_VALIDATOR_TEST_MODE = '000.100.111'
SUCCESS_CONNECTOR_TEST_MODE = '000.100.112'


@python_2_unicode_compatible
class Transaction(base.ResponseModel):
    """
    Model to store every confirmation for successful or failed payments.
    """
    CLEAN_REGEX = [
        (r'password=\w+&', 'password=XXXXXX&'),
        (r'userId=\w+&', 'userId=XXXXXX&'),
        (r'entityID=\w+&', 'entityID=XXXXXX&')
    ]

    SUCCESS_CODES = {
        SUCCESS,
        SUCCESS_CONNECTOR_TEST_MODE,
        SUCCESS_INTEGRATOR_TEST_MODE,
        SUCCESS_VALIDATOR_TEST_MODE,
    }

    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=8, null=True, blank=True)

    result_code = models.CharField(max_length=32)
    result_description = models.CharField(max_length=512, null=True, blank=True)

    checkout_id = models.CharField(max_length=48, unique=True, null=True, editable=False)
    correlation_id = models.CharField(max_length=32, null=True, editable=False)

    class Meta:
        verbose_name = _('Transaction')
        ordering = ('-date_created',)

    def __str__(self):
        return "Transaction %s" % self.id or 'unsaved'

    @property
    def is_success(self):
        return self.result_code in self.SUCCESS_CODES

    def save(self, *args, **kwargs):
        for regex, s in self.CLEAN_REGEX:
            self.raw_request = re.sub(regex, s, self.raw_request)
        return super(Transaction, self).save(*args, **kwargs)
