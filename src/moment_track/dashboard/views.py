# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import OrderedDict

from allauth.account.decorators import verified_email_required
from allauth.account.views import SignupView
from allauth.account.models import EmailAddress
from allauth.account import signals
from allauth.account.adapter import get_adapter
from django.contrib import messages

from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.forms import model_to_dict
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import ensure_csrf_cookie

from dashboard.accounts import user_displayable_name
from dashboard.forms import CompanySignupForm, PrivateSignupForm, EmployeeSignupForm, UserForm, CompanyForm, \
    CompanyUserForm, PayPalCreditsPacketPurchaseForm, UploadAudioFileForm, AudioFileForm
from dashboard.models import EmployeeUser, AudioFile, User
from dashboard.shortcuts import *
from dashboard.utils import get_actual_user, company_user_only, employee_user_only, private_user_only
from moment_track import settings


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
        try:
            employee = get_actual_user(request.user).company.employees.get(id=employee_id)
            user = employee.user
            user.is_active = not user.is_active
            user.save()

            status = 'active' if user.is_active else 'inactive'
            got_error = False
        except EmployeeUser.DoesNotExist:
            pass

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


@verified_email_required
def credits(request):
    # exclude employees from this view
    if not (request.user.is_private or request.user.is_company):
        redirect(reverse('dashboard:forbidden'))

    offers = get_unexpired_offers()

    for offer in offers:
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
        'total_available_credits': get_total_available_credits(request.user),
        'total_available_processing_minutes': get_total_available_processing_minutes(request.user),
        'credits_distribution': get_credits_distribution(request.user),
        'offers': offers
    }

    return render(
        request,
        'dashboard/user/{user_type}/credits.html'.format(
            user_type='private' if request.user.is_private else 'company'
        ),
        context
    )


@verified_email_required
def payment_cancelled(request):
    get_adapter(request).add_message(
        request,
        messages.WARNING,
        'dashboard/messages/payment_cancelled.txt'
    )
    return redirect(reverse('dashboard:credits'))


@verified_email_required
def payment_completed(request):
    get_adapter(request).add_message(
        request,
        messages.SUCCESS,
        'dashboard/messages/payment_completed.txt'
    )
    return redirect(reverse('dashboard:credits'))


@verified_email_required
def upload_file_error(request):
    errors = request.session.pop('errors', {_("Unknown field"): [_("Unknown error")]})
    return render(request, 'dashboard/upload_file_error.html', {'errors': errors})


@verified_email_required
def not_enough_credits(request):
    context = {
        'total_available_credits': get_total_available_credits(request.user),
        'total_available_processing_minutes': get_total_available_processing_minutes(request.user),
        'user': request.user
    }

    return render(request, 'dashboard/not_enough_credits.html', context)


@verified_email_required
def upload_file_success(request):
    get_adapter(request).add_message(
        request,
        messages.SUCCESS,
        'dashboard/messages/upload_file_succeed.txt'
    )
    return redirect(reverse('dashboard:index'))


@verified_email_required
def upload_file(request):
    if request.method == 'POST':
        form = UploadAudioFileForm(request.POST)

        if form.is_valid():
            file = request.FILES['file']

            # TODO: check audio duration and compare with user's available processing minutes

            audio = AudioFile(
                uploader=request.user,
                file=file,
                is_public=form.cleaned_data.get('is_public'),
                name=form.cleaned_data.get('name'),
                description=form.cleaned_data.get('description'),
                language_spoken=form.cleaned_data.get('language_spoken'),
                duration=form.cleaned_data.get('duration')  # FIXME: field vulnerable to data tampering
            )
            try:
                audio.full_clean()
                audio.save()
            except ValidationError as error:
                request.session['errors'] = error.message_dict
                return JsonResponse({'success': False, 'errors': error.messages})
            return JsonResponse({'success': True, 'errors': []})
        else:
            request.session['errors'] = form.errors
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        # If no credits left, just switch to credits page
        credits_left = get_total_available_credits(request.user)
        if not credits_left:
            if request.user.is_employee:
                return redirect(reverse('dashboard:not-enough-credits'))
            else:
                get_adapter(request).add_message(
                    request,
                    messages.ERROR,
                    'dashboard/messages/no_credits_available.txt'
                )
                return redirect(reverse('dashboard:credits'))
        else:
            context = {
                'total_available_credits': get_total_available_credits(request.user),
                'total_available_processing_minutes': get_total_available_processing_minutes(request.user),
                'form': UploadAudioFileForm(),
                'user': request.user
            }
            return render(request, 'dashboard/upload_file.html', context)


def list_files(request):
    requested_user_id = request.GET.get('uploader')
    user = request.user
    actual_user = get_actual_user(user)
    try:
        requested_user = User.objects.get(id=requested_user_id)
    except User.DoesNotExist:
        requested_user = None

    # user is guest
    if user.is_anonymous:

        # no specific user requested, show all public files
        if requested_user is None:
            title = _("Public files")
            files = AudioFile.objects.filter(is_public=True)

        # specific user requested, show its own public files only
        else:
            # requested user exists
            if requested_user is not None:
                title = _("%s's public files" % user_displayable_name(requested_user))
                files = AudioFile.objects.filter(uploader=requested_user, is_public=True)

            # requested user does not exist
            else:
                title = _("Requested user does not exist")
                files = AudioFile.objects.none()

    # user is authenticated
    else:

        # if no specific user requested
        if requested_user_id is None:
            # company user will see all the company's files
            if user.is_company:
                title = _("%s's files" % actual_user.company.name)
                company_staff = [employee_id for employee_id in actual_user.company.employees.values_list('user__id', flat=True)]
                company_staff.append(user.id)
                files = AudioFile.objects.filter(uploader__in=company_staff)
            # private and employees will see their own files
            else:
                title = _("Your files")
                files = AudioFile.objects.filter(uploader=user)

        # specific user requested
        else:

            # user asks for its own files, show them
            if user.id == requested_user.id:
                title = _("Your files")
                files = AudioFile.objects.filter(uploader=user)

            # user is company and asks for employee's files, show them
            elif user.is_company and actual_user.company.employees.filter(user__id=requested_user.id).exists():
                title = _("Employee %s's files" % user_displayable_name(requested_user))
                files = AudioFile.objects.filter(uploader=requested_user)

            # user asks for other user files, show the public ones only
            else:
                title = _("%s's public files" % user_displayable_name(requested_user))
                files = AudioFile.objects.filter(uploader=requested_user, is_public=True)

    context = {
        'files': files.order_by('-upload_datetime'),
        'title': title,
        'user': user
    }
    return render(request, 'dashboard/list_files.html', context)


@verified_email_required
def edit_file(request):
    file_id = request.GET.get('file')
    try:
        audio = AudioFile.objects.get(id=file_id)
    except AudioFile.DoesNotExist:
        audio = None

    # audio file does not exist
    if audio is None:
        get_adapter(request).add_message(
            request,
            messages.ERROR,
            'dashboard/messages/file_does_not_exist.txt'
        )
        return redirect(reverse('dashboard:list-files'))

    # user is not allowed to edit the specified file
    if audio.uploader.id != request.user.id:
        return redirect(reverse('dashboard:forbidden'))

    # user is allowed to see and edit the specified file
    if request.method == 'POST':
        form = AudioFileForm(request.POST, instance=audio)

        if form.is_valid():
            form.save()
            get_adapter(request).add_message(
                request,
                messages.SUCCESS,
                'dashboard/messages/file_update_succeed.txt'
            )
            return redirect(reverse('dashboard:list-files'))
    else:
        form = AudioFileForm(instance=audio)

    return render(request, 'dashboard/edit_file.html', {'form': form, 'audio': audio, 'user': request.user})


@verified_email_required
def delete_file(request):
    if request.method == 'POST':
        file_id = request.POST.get('file')
        try:
            audio = AudioFile.objects.get(id=file_id)
        except AudioFile.DoesNotExist:
            audio = None

        # audio file does not exist
        if audio is None:
            get_adapter(request).add_message(
                request,
                messages.ERROR,
                'dashboard/messages/file_does_not_exist.txt'
            )
            return redirect(reverse('dashboard:list-files'))

        # user is not allowed to delete the specified file
        elif audio.uploader.id != request.user.id:
            return redirect(reverse('dashboard:forbidden'))

        # user is allowed to delete the specified file
        else:
            audio.delete()
            get_adapter(request).add_message(
                request,
                messages.SUCCESS,
                'dashboard/messages/file_delete_succeed.txt'
            )
            return redirect(reverse('dashboard:list-files'))
    else:
        return HttpResponseNotAllowed(['POST'])


def search_in_file(request):
    user = request.user

    # check audio file existence
    try:
        audio = AudioFile.objects.get(id=request.GET.get('file'))
    except AudioFile.DoesNotExist:
        get_adapter(request).add_message(
            request,
            messages.ERROR,
            'dashboard/messages/file_does_not_exist.txt'
        )
        return redirect(reverse('dashboard:list-files'))

    # if audio is public no check is required
    if not audio.is_public:
        # guest users cannot do nothing with non-public files
        if user.is_anonymous:
            return redirect(reverse('dashboard:forbidden'))
        # user is not the uploader
        elif user != audio.uploader:
            # private and employee users are not allowed to view other users' non-public files
            if user.is_private or user.is_employee:
                return redirect(reverse('dashboard:forbidden'))
            # company user can use its own files and the employees' ones
            elif user.is_company and not get_actual_user(user).company.employees.filter(user=audio.uploader).exists():
                return redirect(reverse('dashboard:forbidden'))

    # user is performing a search
    if request.method == 'POST':
        query_string = request.POST.get('querystring')

        transcriptions = audio.transcriptions\
            .filter(text__icontains=query_string)\
            .order_by('offset', 'confidence')\
            .values_list('offset', 'confidence')

        results = [
            {
                'start_time': offset,
                'end_time': offset + settings.MOMENTTRACK_AUDIO_FRAGMENT_DURATION,
                'confidence': confidence
            }
            for offset, confidence in OrderedDict(transcriptions).items()
        ]

    # user is requesting the page without any query string
    else:
        query_string = ''
        results = []

    context = {'audio': audio, 'query_string': query_string, 'results': results}
    return render(request, 'dashboard/search.html', context)
