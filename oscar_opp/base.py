# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _


class ResponseModel(models.Model):
    """
    Originally copied from https://github.com/django-oscar/django-oscar-paypal/blob/master/paypal/base.py
    """
    # Debug information
    raw_request = models.TextField(max_length=512)
    raw_response = models.TextField(max_length=512)

    response_time = models.FloatField(help_text=_("Response time in milliseconds"))

    date_created = models.DateTimeField(_('Created'), auto_now_add=True)
    date_updated = models.DateTimeField(_('Last modified'), auto_now=True)

    class Meta:
        abstract = True
        ordering = ('-date_created',)
        app_label = 'opp'
