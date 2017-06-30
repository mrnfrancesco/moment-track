from __future__ import unicode_literals

from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.db import transaction
from django.forms import NumberInput
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from paypal.standard.forms import PayPalPaymentsForm
from paypal.standard.widgets import ValueHiddenInput
from vatno_validator.validators import VATNoValidator
from phonenumber_field.formfields import PhoneNumberField

from dashboard.models import CompanyUser, PrivateUser, Company, EmployeeUser, AudioFile
from moment_track import settings


class CompanySignupForm(SignupForm):
    """Form used to signup company user"""
    contact_person_first_name = forms.CharField(
        max_length=30,
        label=_("First name"),
        widget=forms.TextInput(attrs={'placeholder': _("Contact person first name")})
    )

    contact_person_last_name = forms.CharField(
        max_length=30,
        label=_("Last name"),
        widget=forms.TextInput(attrs={'placeholder': _("Contact person last name")})
    )

    contact_person_phone_number = PhoneNumberField(
        label=_("Phone number"),
        widget=forms.TextInput(attrs={'placeholder': _("Contact person phone number")})
    )

    company_name = forms.CharField(
        max_length=50,
        label=_("Company name"),
        widget=forms.TextInput(attrs={'placeholder': _("Company name")})
    )

    vat_no = forms.CharField(
        max_length=30,
        validators=[VATNoValidator()],
        label=_("VAT Number"),
        widget=forms.TextInput(attrs={'placeholder': _("Company VAT number")})
    )

    def save(self, request):
        with transaction.atomic():
            user = super(CompanySignupForm, self).save(request)

            user.user_type = user.COMPANY
            user.save()

            company = Company(
                name=self.cleaned_data.get('company_name'),
                vat_no=self.cleaned_data.get('vat_no')
            )
            company.save()

            company_user = CompanyUser(
                user=user,
                phone_number=self.cleaned_data.get('contact_person_phone_number'),
                company=company
            )
            company_user.save()

        return user


class PrivateSignupForm(SignupForm):
    """Form used to signup private user who are performing manual registration"""
    first_name = forms.CharField(
        max_length=30,
        label=_("First name"),
        widget=forms.TextInput(attrs={'placeholder': _("First name")})
    )

    last_name = forms.CharField(
        max_length=30,
        label=_("Last name"),
        widget=forms.TextInput(attrs={'placeholder': _("Last name")})
    )

    def save(self, request):
        with transaction.atomic():
            user = super(PrivateSignupForm, self).save(request)

            user.user_type = user.PRIVATE
            user.save()

            private_user = PrivateUser(user=user)
            private_user.save()

        return user


class PrivateSocialSignupForm(SocialSignupForm):
    """Form used to complete signup of private users using social login"""
    first_name = forms.CharField(
        max_length=30,
        label=_("First name"),
        widget=forms.TextInput(attrs={'placeholder': _("First name")})
    )

    last_name = forms.CharField(
        max_length=30,
        label=_("Last name"),
        widget=forms.TextInput(attrs={'placeholder': _("Last name")})
    )

    def save(self, request):
        with transaction.atomic():
            user = super(PrivateSocialSignupForm, self).save(request)

            user.user_type = user.PRIVATE
            user.save()

            private_user = PrivateUser(user=user)
            private_user.save()

        return user


class EmployeeSignupForm(SignupForm):
    """Form used to signup company's employee"""

    def __init__(self, *args, **kwargs):
        super(EmployeeSignupForm, self).__init__(*args, **kwargs)
        # remove the ask for password
        del self.fields['password1']
        if self.fields.get('password2'):
            del self.fields['password2']

    def save(self, request):
        with transaction.atomic():
            user = super(EmployeeSignupForm, self).save(request)

            user.user_type = user.EMPLOYEE
            user.save()

            company = request.user.company_user.company
            employee = EmployeeUser(user=user, company=company)
            employee.save()

        return user


class UserForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        for field_name in ('date_joined', 'last_login', 'email'):
            if field_name in self.fields:
                self.fields[field_name].disabled = True
                self.fields[field_name].required = False

    def clean(self):
        cleaned_data = super(UserForm, self).clean()

        required_fields = {
            field_name
            for field_name in self._meta.fields
            if not self.fields[field_name].disabled
        }
        unwanted_fields = set(cleaned_data) - required_fields
        for field_name in unwanted_fields:
            del cleaned_data[field_name]

        return cleaned_data

    class Meta:
        model = get_user_model()
        fields = (
            'date_joined', 'last_login',
            'email', 'first_name', 'last_name',
        )


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ('name', 'vat_no')


class CompanyUserForm(forms.ModelForm):
    class Meta:
        model = CompanyUser
        fields = ('phone_number',)


class PayPalCreditsPacketPurchaseForm(PayPalPaymentsForm):
    def __init__(self, *args, **kwargs):
        super(PayPalCreditsPacketPurchaseForm, self).__init__(*args, **kwargs)

        # Automatically set business email address to the correct value
        self.fields['business'] = forms.CharField(
            widget=ValueHiddenInput(),
            initial=settings.PAYPAL_BUSINESS_EMAIL_ADDRESS
        )

        # Let the user choose the quantity
        self.fields['quantity'] = forms.IntegerField(
            label=_('Quantity'),
            widget=NumberInput(attrs={'min': 1}),
            initial=1
        )

        current_domain = Site.objects.get_current().domain
        self.fields['notify_url'] = forms.URLField(
            widget=ValueHiddenInput(),
            initial=(current_domain + reverse('paypal-ipn'))
        )
        self.fields['return_url'] = forms.URLField(
            widget=ValueHiddenInput(),
            initial=(current_domain + reverse('dashboard:private-user-payment-completed'))
        )
        self.fields['cancel_return'] = forms.URLField(
            widget=ValueHiddenInput(),
            initial=(current_domain + reverse('dashboard:private-user-payment-cancelled'))
        )

    @property
    def endpoint(self):
        return self.get_endpoint()


class UploadAudioFileForm(forms.Form):
    language_spoken = forms.CharField(
        widget=forms.Select(choices=AudioFile.LANGUAGE_SPOKEN_CHOICES),
        initial='it'
    )
    name = forms.CharField(max_length=256)
    description = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={'maxlength': 500})
    )
    is_public = forms.BooleanField(initial=False)
    duration = forms.DurationField(widget=forms.HiddenInput())
