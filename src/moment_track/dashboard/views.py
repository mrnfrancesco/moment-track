# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from allauth.account.views import SignupView
from django.shortcuts import render

from dashboard.forms import CompanySignupForm, PrivateSignupForm


def privacy_policy(request):
    return render(request, 'dashboard/legal-notes/privacy-policy.html')


def terms_of_service(request):
    return render(request, 'dashboard/legal-notes/terms-of-service.html')


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


def index(request):
    return render(request, 'dashboard/index.html')
