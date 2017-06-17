from __future__ import unicode_literals

from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django import forms
from django.utils.translation import ugettext_lazy as _
from vatno_validator.validators import VATNoValidator
from phonenumber_field.formfields import PhoneNumberField

from dashboard.models import CompanyUser, PrivateUser, Company


class CompanySignupForm(SignupForm):
    contact_person_first_name = forms.CharField(
        max_length=30, required=True, strip=True,
        label=_("First name"),
        widget=forms.TextInput(attrs={'placeholder': _("Contact person first name")})
    )

    contact_person_last_name = forms.CharField(
        max_length=30, required=True, strip=True,
        label=_("Last name"),
        widget=forms.TextInput(attrs={'placeholder': _("Contact person last name")})
    )

    contact_person_phone_number = PhoneNumberField(
        required=True, strip=True,
        label=_("Phone number"),
        widget=forms.TextInput(attrs={'placeholder': _("Contact person phone number")})
    )

    company_name = forms.CharField(
        max_length=50, required=True, strip=True,
        label=_("Company name"),
        widget=forms.TextInput(attrs={'placeholder': _("Company name")})
    )

    vat_no = forms.CharField(
        max_length=30,
        required=True,
        strip=True,
        validators=[VATNoValidator()],
        label=_("VAT Number"),
        widget=forms.TextInput(attrs={'placeholder': _("Company VAT number")})
    )

    def save(self, request):
        user = super(CompanySignupForm, self).save(request)

        user.user_type = user.COMPANY
        user.save()

        company = Company(
            company_name=self.cleaned_data.get('company_name'),
            vat_no=self.cleaned_data.get('vat_no')
        )
        company.save()

        company_user = CompanyUser(
            contact_person=user,
            phone_number=self.cleaned_data.get('contact_person_phone_number'),
            company=company
        )
        company_user.save()

        return user


class PrivateSignupForm(SignupForm):
    first_name = forms.CharField(
        max_length=30, required=True, strip=True,
        label=_("First name"),
        widget=forms.TextInput(attrs={'placeholder': _("First name")})
    )

    last_name = forms.CharField(
        max_length=30, required=True, strip=True,
        label=_("Last name"),
        widget=forms.TextInput(attrs={'placeholder': _("Last name")})
    )

    def save(self, request):
        user = super(PrivateSignupForm, self).save(request)

        user.user_type = user.PRIVATE
        user.save()

        private_user = PrivateUser(user=user)
        private_user.save()

        return user


class PrivateSocialSignupForm(SocialSignupForm):
    first_name = forms.CharField(
        max_length=30, required=True, strip=True,
        label=_("First name"),
        widget=forms.TextInput(attrs={'placeholder': _("First name")})
    )

    last_name = forms.CharField(
        max_length=30, required=True, strip=True,
        label=_("Last name"),
        widget=forms.TextInput(attrs={'placeholder': _("Last name")})
    )

    def save(self, request):
        user = super(PrivateSocialSignupForm, self).save(request)

        user.user_type = user.PRIVATE
        user.save()

        private_user = PrivateUser(user=user)
        private_user.save()

        return user
