# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig

from paypal.standard.ipn.signals import valid_ipn_received


class WebsiteConfig(AppConfig):
    name = 'dashboard'

    def ready(self):
        from dashboard import signals

        valid_ipn_received.connect(
            signals.private_user_bought_credits_packet,
            dispatch_uid='private-user-bought-credits-packet'
        )
