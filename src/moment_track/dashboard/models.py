# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import date, timedelta

import magic
import uuid
import math

from django.conf import global_settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.encoding import python_2_unicode_compatible

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from vatno_validator.validators import VATNoValidator

from moment_track import settings
from dashboard.accounts import user_displayable_name


@python_2_unicode_compatible
class User(AbstractUser):
    """A fully featured user base model with an extra field
    to differentiate between user types"""
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
        """Return True if the current user is a private user, False otherwise."""
        return self.user_type == User.PRIVATE

    @property
    def is_company(self):
        """Return True if the current user is a company user, False otherwise."""
        return self.user_type == User.COMPANY

    @property
    def is_employee(self):
        """Return True if the current user is an employee user, False otherwise."""
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
        """Return always True"""
        return True

    @property
    def is_anonymous(self):
        """Return always False"""
        return False

    def __str__(self):
        return str(self.user)

    class Meta:
        abstract = True


@python_2_unicode_compatible
class PrivateUser(AbstractUserModel):
    """Model to represent a private user"""
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='private_user')

    def __str__(self):
        return super(PrivateUser, self).__str__()


@python_2_unicode_compatible
class Company(models.Model):
    """Model to represent a company"""
    name = models.CharField(max_length=50)
    vat_no = models.CharField(max_length=30, validators=[VATNoValidator()], unique=True)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class CompanyUser(AbstractUserModel):
    """Model to represent a company user"""
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
    """Model to represent an employee user"""
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='employee_user')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employees')

    def __str__(self):
        return '{user} employee @ {company}'.format(
            user=str(self.user),
            company=str(self.company)
        )


@python_2_unicode_compatible
class CreditsPacketOffer(models.Model):
    """Model to represent a credits packet offer"""
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
    """Model to represent the purchase of credits chosen
    from the available credits packet offers
    """
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


def _get_relative_file_path(instance, filename):
    """Return a relative path based on actual date
    with unique file name as uuid.
    """
    # Give file a unique name
    return '{date}/{filename}.flac'.format(
        date=date.today().strftime('%Y/%m/%d'),
        filename=str(uuid.uuid4())
    )


@python_2_unicode_compatible
class AudioFile(models.Model):
    """Model to represent a flac audio file."""
    LANGUAGE_SPOKEN_CHOICES = global_settings.LANGUAGES

    ALLOWED_MIME_TYPES = (
        'audio/flac',
        'audio/x-flac'
    )

    uploader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='files', editable=False)
    upload_datetime = models.DateTimeField(auto_now_add=True, editable=False)
    file = models.FileField(upload_to=_get_relative_file_path, editable=False)
    is_public = models.BooleanField(default=False)
    name = models.CharField(max_length=256)
    description = models.CharField(max_length=500, blank=True)
    language_spoken = models.CharField(max_length=5, choices=LANGUAGE_SPOKEN_CHOICES, editable=False)
    duration = models.DurationField(editable=False)

    def clean_file(self):
        """Check if the uploaded file is really a flac file"""
        # Get first 1024 Bytes file chunk
        chunk = next(chunk for chunk in self.file.chunks(1024))
        # Retrieve the mime type of the file
        mime = magic.from_buffer(chunk, mime=True)

        if mime not in AudioFile.ALLOWED_MIME_TYPES:
            raise ValidationError(
                'Unsupported file type {actual_type}. Allowed type(s) are: {allowed_types}'.format(
                    actual_type=mime,
                    allowed_types=(', '.join(AudioFile.ALLOWED_MIME_TYPES))
                ),
                code='invalid'
            )

    @property
    def total_fragments(self):
        """Returns the total number of fragments to use to process file"""
        return int(
            math.ceil(
                self.duration.total_seconds() / settings.MOMENTTRACK_AUDIO_FRAGMENT_DURATION.total_seconds()
            )
        )

    @property
    def available_fragments(self):
        """Returns the actual number of fragments available after processing"""
        return self.transcriptions.values_list('offset').distinct().count()

    @property
    def transcription_coverage(self):
        """Return the percentage of transcription coverage as
        available fragments on total fragments ratio.
        """
        return float(self.available_fragments) / float(self.total_fragments)

    def __str__(self):
        return '{name} @ "{path}"'.format(name=self.name, path=self.file.name)


@python_2_unicode_compatible
class Transcription(models.Model):
    """Model to represent a file fragment transcription"""
    file = models.ForeignKey(AudioFile, on_delete=models.CASCADE, related_name='transcriptions')
    offset = models.DurationField()
    confidence = models.FloatField()
    text = models.TextField(blank=True)

    def __str__(self):
        audio = self.file

        hours, remainder = divmod(self.offset.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        return 'Transcription for "{file_name}" starting at {hh}:{mm}:{ss}'.format(
            file_name=audio.file.name,
            hh=str(hours).zfill(2), mm=str(minutes).zfill(2), ss=str(seconds).zfill(2)
        )
