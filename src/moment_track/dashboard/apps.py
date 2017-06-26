# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig

from paypal.standard.ipn.signals import valid_ipn_received

from dashboard import signals


class WebsiteConfig(AppConfig):
    name = 'dashboard'

    def ready(self):
        valid_ipn_received.connect(
            signals.private_user_bought_credits_packet,
            dispatch_uid='private-user-bought-credits-packet'
        )
