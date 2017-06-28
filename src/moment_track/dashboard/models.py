# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.encoding import python_2_unicode_compatible

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from vatno_validator.validators import VATNoValidator

from dashboard.accounts import user_displayable_name


@python_2_unicode_compatible
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
        editable=False, null=True,
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

    def __str__(self):
        return '{displayable_name} ({email})'.format(
            displayable_name=user_displayable_name(self),
            email=self.email
        )


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
        return str(self.user)

    class Meta:
        abstract = True


@python_2_unicode_compatible
class PrivateUser(AbstractUserModel):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='private_user')

    def __str__(self):
        return super(PrivateUser, self).__str__()


@python_2_unicode_compatible
class Company(models.Model):
    name = models.CharField(max_length=50)
    vat_no = models.CharField(max_length=30, validators=[VATNoValidator()], unique=True)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class CompanyUser(AbstractUserModel):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='company_user')
    phone_number = PhoneNumberField()
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='contact_person')

    def __str__(self):
        return '{user} contact person for {company}'.format(
            user=str(self.user),
            company=str(self.company)
        )


@python_2_unicode_compatible
class EmployeeUser(AbstractUserModel):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='employee_user')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employees')

    def __str__(self):
        return '{user} employee @ {company}'.format(
            user=str(self.user),
            company=str(self.company)
        )


@python_2_unicode_compatible
class CreditsPacketOffer(models.Model):
    MIN_MINUTES_PER_CREDIT = 5
    MAX_MINUTES_PER_CREDIT = 60

    date_start = models.DateField(default=date.today)
    date_end = models.DateField(null=True, blank=True)
    minutes_per_credit = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                MIN_MINUTES_PER_CREDIT,
                _("Cannot set minutes per credit value less than %d" % MIN_MINUTES_PER_CREDIT)
            ),
            MaxValueValidator(
                MAX_MINUTES_PER_CREDIT,
                _("Cannot set minutes per credit value greater than %d" % MAX_MINUTES_PER_CREDIT)
            )
        ]
    )
    cost_per_credit = models.FloatField()

    def __str__(self):
        return '{cost} USD/min (from {date_start} to {date_end})'.format(
            cost=(float(self.cost_per_credit)/float(self.minutes_per_credit)),
            date_start=self.date_start,
            date_end=self.date_end if self.date_end else '?'
        )


@python_2_unicode_compatible
class CreditsPacketPurchase(models.Model):
    MIN_CREDITS_PURCHASED = 1

    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='purchases')
    offer = models.ForeignKey(CreditsPacketOffer, related_name='purchases', on_delete=models.PROTECT)
    datetime = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateField()
    credits_purchased = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                MIN_CREDITS_PURCHASED,
                _("You cannot buy less than %d credit" % MIN_CREDITS_PURCHASED)
            )
        ]
    )
    credits_remaining = models.PositiveSmallIntegerField()

    def __init__(self, *args, **kwargs):
        super(CreditsPacketPurchase, self).__init__(*args, **kwargs)
        if not self.expiration_date:
            self.expiration_date = (self.datetime.date() + timedelta(days=30))
        self.credits_remaining = self.credits_purchased

    def __str__(self):
        return '[{datetime}] {user_name} purchased {purchased} credits ({remaining} remaining)'.format(
            datetime=self.datetime,
            user_name=user_displayable_name(self.customer),
            purchased=self.credits_purchased,
            remaining=self.credits_remaining
        )


@python_2_unicode_compatible
class AudioFile(models.Model):
    from django.conf import global_settings
    LANGUAGE_SPOKEN_CHOICES = global_settings.LANGUAGES

    ALLOWED_MIME_TYPES = (
        'audio/flac',
        'audio/x-flac'
    )

    class Status(object):
        STORING = 1
        PROCESSING = 2
        DONE = 3

        @classmethod
        def choices(cls):
            return (
                (cls.STORING, _("Storing")),
                (cls.PROCESSING, _("Processing")),
                (cls.DONE, _("Done")),
            )

    uploader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    file_status = models.PositiveSmallIntegerField(choices=Status.choices())
    is_public = models.BooleanField(default=False)
    name = models.CharField(max_length=256)
    description = models.CharField(max_length=500)
    language_spoken = models.CharField(max_length=5, choices=LANGUAGE_SPOKEN_CHOICES)
    duration = models.DurationField()

    def __str__(self):
        return '{name} @ "{path}"'.format(name=self.name, path=self.file.path)


@python_2_unicode_compatible
class CreditsUsage(models.Model):
    MIN_CREDITS_USED = 1

    file = models.OneToOneField(
        AudioFile,
        on_delete=models.CASCADE,
        related_name='credits_usage'
    )
    credits_packet_purchase = models.OneToOneField(
        CreditsPacketPurchase,
        on_delete=models.CASCADE,
        related_name='credits_usage'
    )
    credits_used = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                MIN_CREDITS_USED,
                _("You cannot use less than %d credit(s)" % MIN_CREDITS_USED)
            )
        ]
    )
    datetime = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '[{datetime}] {user_name} used {used} credit(s) for file "{file_name}"'.format(
            datetime=self.datetime,
            user_name=user_displayable_name(self.file.uploader),
            used=self.credits_used,
            file_name=self.file.name
        )


@python_2_unicode_compatible
class Transcription(models.Model):
    file = models.ForeignKey(AudioFile, on_delete=models.CASCADE, related_name='transcriptions')
    time_start = models.TimeField()
    duration = models.DurationField()
    confidence = models.FloatField()
    text = models.TextField(blank=True)

    def __str__(self):
        return 'Transcription for "{file_name}" starting at {time_start} ({duration} sec)'.format(
            file_name=file.name,
            time_start=self.time_start,
            duration=self.duration
        )
