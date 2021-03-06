# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig
from django.db import models

from paypal.standard.ipn.signals import valid_ipn_received


class DashboardConfig(AppConfig):
    """Web app configuration"""
    name = 'dashboard'

    def ready(self):
        """Connect some signals on framework start"""
        from dashboard import signals
        from dashboard.models import AudioFile

        valid_ipn_received.connect(
            signals.user_bought_credits_packet,
            dispatch_uid='user-bought-credits-packet'
        )

        models.signals.post_delete.connect(
            signals.delete_file_on_model_deletion,
            sender=AudioFile,
            dispatch_uid='delete-file-on-audiofile-model-deletion'
        )

        models.signals.post_save.connect(
            signals.on_file_upload,
            sender=AudioFile,
            dispatch_uid='on-file-upload'
        )
