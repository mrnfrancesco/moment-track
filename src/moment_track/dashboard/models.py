# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible


from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from vatno_validator.validators import VATNoValidator

from dashboard.accounts import user_displayable_name


class User(AbstractUser):
    PRIVATE = 1
    COMPANY = 2
    EMPLOYEE = 3

    USER_TYPE_CHOICES = (
        (PRIVATE, _('Private User')),
        (COMPANY, _('Company User')),
        (EMPLOYEE, _('Employee User')),
    )
    user_type = models.PositiveSmallIntegerField(
        editable=False, null=True, blank=False,
        choices=USER_TYPE_CHOICES
    )

    @property
    def is_private(self):
        return self.user_type == User.PRIVATE

    @property
    def is_company(self):
        return self.user_type == User.COMPANY

    @property
    def is_employee(self):
        return self.user_type == User.EMPLOYEE


@python_2_unicode_compatible
class PrivateUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return user_displayable_name(self.user)


@python_2_unicode_compatible
class Company(models.Model):
    company_name = models.CharField(max_length=50, null=False, blank=False)
    vat_no = models.CharField(
        max_length=30,
        validators=[VATNoValidator()],
        unique=True,
        null=False,
        blank=False
    )

    def __str__(self):
        return self.company_name


@python_2_unicode_compatible
class CompanyUser(models.Model):
    contact_person = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = PhoneNumberField(null=False, blank=False)
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='contact_person')

    def __str__(self):
        return user_displayable_name(self.contact_person)

