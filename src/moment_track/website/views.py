# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.


def home(request):
    return render(request, 'website/home.html')


def privacy_policy(request):
    return render(request, 'website/privacy-policy.html')


def terms_of_service(request):
    return render(request, 'website/terms-of-service.html')
