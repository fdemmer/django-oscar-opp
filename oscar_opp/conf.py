from django.conf import settings  # noqa

# this is not django's AppConf!
# https://django-appconf.readthedocs.io/en/latest/
from appconf import AppConf


class OpenPasswordPlatformConf(AppConf):
    USER_ID = None
    ENTITY_ID = None
    PASSWORD = None
    BASE_URL = "https://test.oppwa.com/v1/"
