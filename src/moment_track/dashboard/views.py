# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import date

from allauth.account.decorators import verified_email_required
from allauth.account.views import SignupView
from allauth.account.models import EmailAddress
from allauth.account import signals
from allauth.account.adapter import get_adapter
from django.contrib import messages

from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.db import transaction
from django.db.models import Sum, F
from django.forms import model_to_dict
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie

from dashboard.forms import CompanySignupForm, PrivateSignupForm, EmployeeSignupForm, UserForm, CompanyForm, \
    CompanyUserForm, PayPalCreditsPacketPurchaseForm
from dashboard.models import EmployeeUser, CreditsPacketPurchase, CreditsPacketOffer
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


@verified_email_required
@company_user_only
@ensure_csrf_cookie
def invert_employee_account_active_status(request, employee_id):
    status = 'unknown'
    got_error = True

    if request.method == 'POST':
        if EmployeeUser.objects.filter(id=employee_id).exists():
            employee = EmployeeUser.objects.get(id=employee_id)
            user = employee.user
            user.is_active = not user.is_active
            user.save()

            status = 'active' if user.is_active else 'inactive'
            got_error = False

    return JsonResponse({'error': got_error, 'status': status})


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


@verified_email_required
@private_user_only
def private_user_credits(request):
    today = date.today()

    # Get all the credits purchases bought by the user that are not
    # expired and have at least 1 credit left
    qs_unexpired_not_empty_purchase = CreditsPacketPurchase.objects.filter(
        customer=request.user,
        expiration_date__gte=today,
        credits_remaining__gt=0
    )

    # Get the sum of all the available credits (no matter the type)
    total_available_credits = qs_unexpired_not_empty_purchase.aggregate(
        credits_remaining=Sum('credits_remaining')
    ).get('credits_remaining') or 0

    # Get the total available minutes of processing as the sum of all the
    # credits left x minutes per credit
    total_available_processing_minutes = qs_unexpired_not_empty_purchase.annotate(
        minutes_left=F('offer__minutes_per_credit') * F('credits_remaining')
    ).aggregate(
        minutes_left_sum=Sum('minutes_left')
    ).get('minutes_left_sum') or 0

    # Get all the info about every credits packet purchased
    credits_distribution = qs_unexpired_not_empty_purchase.values(
        'offer__minutes_per_credit',
        'credits_purchased',
        'credits_remaining',
        'expiration_date'
    )

    # Change expiration date into days left before expiration
    for t in credits_distribution:
        t['days_before_expiration'] = (t['expiration_date'] - today).days
        del t['expiration_date']

    # Get all the not expired credits packets offers
    offers = CreditsPacketOffer.objects.exclude(
        date_end__lt=today
    ).values(
        'id',
        'date_end',
        'minutes_per_credit',
        'cost_per_credit'
    )

    for offer in offers:
        # Change offer expiration date into days left before expiration
        if offer['date_end']:
            offer['days_left'] = (offer['date_end'] - today).days
        else:
            offer['days_left'] = None
        del offer['date_end']

        # Paypal dictionary for receiving payments
        offer['paypal_form'] = PayPalCreditsPacketPurchaseForm(initial={
            'amount': offer['cost_per_credit'],
            'item_name': 'Moment Track Credit Packet ({mpc} min/credit, {cpc} $/credit)'.format(
                mpc=offer['minutes_per_credit'],
                cpc=offer['cost_per_credit'],
                custom={
                    'buyer_email': request.user.email,
                    'offer_id': offer['id']
                }
            ),
        })

    context = {
        'total_available_credits': total_available_credits,
        'total_available_processing_minutes': total_available_processing_minutes,
        'credits_distribution': credits_distribution,
        'offers': offers
    }

    return render(request, 'dashboard/user/private/credits.html', context)


@verified_email_required
@private_user_only
def private_user_payment_cancelled(request):
    account_adapter = get_adapter(request)
    account_adapter.add_message(
        request,
        messages.ERROR,
        'dashboard/messages/payment_cancelled.txt'
    )
    return redirect(reverse('dashboard:private-user-credits'))


@verified_email_required
@private_user_only
def private_user_payment_completed(request):
    account_adapter = get_adapter(request)
    account_adapter.add_message(
        request,
        messages.SUCCESS,
        'dashboard/messages/payment_completed.txt'
    )
    return redirect(reverse('dashboard:private-user-credits'))
