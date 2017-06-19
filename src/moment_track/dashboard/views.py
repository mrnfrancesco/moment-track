# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from allauth.account.decorators import verified_email_required
from allauth.account.views import SignupView
from allauth.account.models import EmailAddress
from allauth.account import signals
from allauth.account.adapter import get_adapter
from django.contrib import messages

from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.db import transaction
from django.forms import model_to_dict
from django.shortcuts import render

from dashboard.forms import CompanySignupForm, PrivateSignupForm, EmployeeSignupForm, UserForm, CompanyForm, \
    CompanyUserForm
from dashboard.models import EmployeeUser
from dashboard.utils import get_actual_user, company_user_only, employee_user_only, private_user_only


class CompanyUserSignupView(SignupView):
    template_name = 'account/signup_company.html'
    form_class = CompanySignupForm
    view_name = 'dashboard:company_signup'

company_signup = CompanyUserSignupView.as_view()


class PrivateUserSignupView(SignupView):
    template_name = 'account/signup_private.html'
    form_class = PrivateSignupForm
    view_name = 'dashboard:private_signup'

private_signup = PrivateUserSignupView.as_view()


@verified_email_required
@company_user_only
def company_employees(request):
    # if this is a POST request we need to process the form data
    # otherwise we just create a blank employee signup form
    if request.method == 'POST':
        employee_signup_form = EmployeeSignupForm(request.POST)

        if employee_signup_form.is_valid():
            with transaction.atomic():
                user = employee_signup_form.save(request)

                signals.user_signed_up.send(sender=user.__class__, user=user)

                # Automatically verify email
                email = EmailAddress.objects.get_primary(user=user)
                email.verified = True
                email.save()

                signals.email_confirmed.send(sender=user.__class__, email_address=user.email)

                # we need the account adapter to send email using allauth workflow
                account_adapter = get_adapter()

                # create a random password for the user
                # N.B: user already has a password, but it is not accessible
                # anymore because of crypt, so we create a new one and
                # send it to the user email
                random_password = get_user_model().objects.make_random_password()
                user.set_password(raw_password=random_password)
                user.save()

                signals.password_changed.send(sender=user.__class__, request=request, user=user)

                employee = get_actual_user(user)

                current_site = get_current_site(request)
                company = employee.company

                account_adapter.send_mail(
                    'account/email/employee_password',
                    employee.email,
                    {
                        'current_site': current_site,
                        'company': company,
                        'password': random_password
                    }
                )

                account_adapter.send_mail(
                    'account/email/employee_added',
                    company.contact_person.email,
                    {
                        'current_site': current_site,
                        'company': company,
                        'employee': employee
                    }
                )

                # send a notification as another confirmation message
                account_adapter.add_message(
                    request,
                    messages.SUCCESS,
                    'account/messages/employee_added.txt',
                    {
                        'company': company,
                        'employee': employee
                    }
                )
    # If this is a GET (or any other methods) request, create a blank form
    else:
        employee_signup_form = EmployeeSignupForm()

    company_user = get_actual_user(request.user)
    company = company_user.company
    employees = EmployeeUser.objects.filter(company=company)

    context = {
        'employee_signup_form': employee_signup_form,
        'employees': employees,
    }

    return render(request, 'dashboard/user/company/employees.html', context)


def _user_profile(request):
    user = request.user
    # in case the user is trying to modify data
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)

        account_adapter = get_adapter(request)

        if user_form.is_valid():
            user_form.save()

            account_adapter.add_message(
                request,
                messages.SUCCESS,
                'dashboard/messages/profile_update_success.txt'
            )
    else:
        user_form = UserForm(instance=user)

    context = {
        'user_has_usable_password': user.has_usable_password(),
        'user_form': user_form
    }

    return context


@verified_email_required
@private_user_only
def private_user_profile(request):
    context = _user_profile(request)
    return render(request, 'dashboard/user/private/profile.html', context)


@verified_email_required
@employee_user_only
def employee_user_profile(request):
    context = _user_profile(request)
    return render(request, 'dashboard/user/employee/profile.html', context)


@verified_email_required
@company_user_only
def company_user_profile(request):
    user = request.user
    company_user = get_actual_user(request.user)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        company_user_form = CompanyUserForm(request.POST, instance=company_user)

        account_adapter = get_adapter(request)

        if user_form.is_valid() and company_user_form.is_valid():
            with transaction.atomic():
                user_form.save()
                company_user_form.save()

            account_adapter.add_message(
                request,
                messages.SUCCESS,
                'dashboard/messages/profile_update_success.txt'
            )
    else:
        user_form = UserForm(instance=user)
        company_user_form = CompanyUserForm(instance=company_user)

    context = {
        'user_has_usable_password': user.has_usable_password(),
        'user_form': user_form,
        'company_user_form': company_user_form,
    }

    return render(request, 'dashboard/user/company/profile.html', context)


@verified_email_required
@company_user_only
def company_details(request):
    company_user = get_actual_user(request.user)
    company = company_user.company

    if request.method == 'POST':
        company_form = CompanyForm(request.POST, instance=company)

        if company_form.is_valid():
            company_form.save()
    else:
        company_form = CompanyForm(instance=company)

    context = {'company_form': company_form}
    return render(request, 'dashboard/user/company/company_details.html', context)


@verified_email_required
@employee_user_only
def employee_company_details(request):
    employee_user = get_actual_user(request.user)
    company = employee_user.company
    company_user = company.contact_person

    context = {
        'company': CompanyForm(model_to_dict(company)),
        'contact_person_user': UserForm(model_to_dict(company_user.user)),
        'company_contact_person': CompanyUserForm(model_to_dict(company_user)),
    }

    return render(request, 'dashboard/user/employee/company.html', context)


def index(request):
    return render(request, 'dashboard/index.html')
