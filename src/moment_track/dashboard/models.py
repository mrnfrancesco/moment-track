# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
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
class AbstractUserModel(models.Model):
    """Abstract user model to make custom user models
    interchangeable with User"""

    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError as error:
            # search attribute in user model's django fields
            if name in [field.name for field in get_user_model()._meta.fields]:
                return getattr(self.user, name)
            # search attribute in user model's python properties
            elif name in [prop_name
                          for prop_name, prop in vars(get_user_model()).iteritems()
                          if type(prop) == property
                          ]:
                return getattr(self.user, name)
            else:
                raise error

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def __str__(self):
        return user_displayable_name(self.user)

    class Meta:
        abstract = True


class PrivateUser(AbstractUserModel):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='private_user')


@python_2_unicode_compatible
class Company(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False)
    vat_no = models.CharField(
        max_length=30,
        validators=[VATNoValidator()],
        unique=True,
        null=False,
        blank=False
    )

    def __str__(self):
        return self.name


class CompanyUser(AbstractUserModel):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='company_user')
    phone_number = PhoneNumberField(null=False, blank=False)
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='contact_person')


@python_2_unicode_compatible
class EmployeeUser(AbstractUserModel):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='employee_user')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employees')

    def __str__(self):
        return '{user} @ {company}'.format(
            user=user_displayable_name(self.user),
            company=str(self.company)
        )
