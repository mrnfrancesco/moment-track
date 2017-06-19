from __future__ import unicode_literals

from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from vatno_validator.validators import VATNoValidator
from phonenumber_field.formfields import PhoneNumberField

from dashboard.models import CompanyUser, PrivateUser, Company, EmployeeUser


class CompanySignupForm(SignupForm):
    """Form used to signup company user"""
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
