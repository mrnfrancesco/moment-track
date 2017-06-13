from __future__ import unicode_literals

from allauth.account.forms import SignupForm
from django import forms
from django.utils.translation import ugettext_lazy as _
from vatno_validator.validators import VATNoValidator
from phonenumber_field.formfields import PhoneNumberField

from website.models import CompanyUser, PrivateUser


class CompanySignupForm(SignupForm):
    contact_person_first_name = forms.CharField(max_length=30, required=True, strip=True)
    contact_person_last_name = forms.CharField(max_length=30, required=True, strip=True)
    company_name = forms.CharField(max_length=50, required=True, strip=True)
    vat_no = forms.CharField(
        max_length=30,
        required=True,
        strip=True,
        validators=[VATNoValidator()],
        label=_("VAT Number")
    )
    phone_number = PhoneNumberField(required=True, strip=True)

    def save(self, request):
        user = super(CompanySignupForm, self).save(request)
        user.first_name = self.cleaned_data.get('contact_person_first_name')
        user.last_name = self.cleaned_data.get('contact_person_last_name')
        user.save()

        company_user = CompanyUser(
            contact_person=user,
            company_name=self.cleaned_data.get('company_name'),
            vat_no=self.cleaned_data.get('vat_no'),
            phone_number=self.cleaned_data.get('phone_number')
        )
        company_user.save()

        return company_user.contact_person


class PrivateSignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, required=True, strip=True)
    last_name = forms.CharField(max_length=30, required=True, strip=True)

    def save(self, request):
        user = super(PrivateSignupForm, self).save(request)
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.save()

        private_user = PrivateUser(user=user)
        private_user.save()

        return user
