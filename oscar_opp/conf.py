from django.conf import settings  # noqa

# this is not django's AppConf!
# https://django-appconf.readthedocs.io/en/latest/
from appconf import AppConf


class OpenPasswordPlatformConf(AppConf):
    USER_ID = None
    ENTITY_ID = None
    PASSWORD = None
    BASE_URL = "https://test.oppwa.com/v1/"
    # dictionary of payment-method: payment-brands
    # payment brands are documented at:
    # https://docs.oppwa.com/tutorials/integration-guide/customisation#optionsbrands
    PAYMENT_METHODS = {
        'opp_card': 'VISA MASTER AMEX',
        'opp_eps': 'EPS',
    }
    DEFAULT_PAYMENT_METHOD = 'opp_card'
