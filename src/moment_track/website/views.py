# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from allauth.account.views import SignupView
from django.shortcuts import render

from website.forms import CompanySignupForm


def home(request):
    return render(request, 'website/home.html')


def privacy_policy(request):
    return render(request, 'website/privacy-policy.html')


def terms_of_service(request):
    return render(request, 'website/terms-of-service.html')


class CompanyUserSignupView(SignupView):
    template_name = 'account/signup_company.html'
    form_class = CompanySignupForm
    view_name = 'website:company_signup'

company_signup = CompanyUserSignupView.as_view()
