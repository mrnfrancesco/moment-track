# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible


from django.db import models
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField
from vatno_validator.validators import VATNoValidator


@python_2_unicode_compatible
class PrivateUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.email


@python_2_unicode_compatible
class CompanyUser(models.Model):
    contact_person = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=50, null=False, blank=False)
    vat_no = models.CharField(
        max_length=30,
        validators=[VATNoValidator()],
        unique=True,
        null=False,
        blank=False
    )
    phone_number = PhoneNumberField(null=False, blank=False)

    def __str__(self):
        return self.company_name


