"""moment_track website URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.http import Http404
from django.views.defaults import page_not_found

from dashboard import views

app_name = 'dashboard'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^privacy-policy/$', views.privacy_policy, name='privacy-policy'),
    url(r'^terms-of-service/$', views.terms_of_service, name='terms-of-service'),

    url(r'^accounts/signup/company/$', views.company_signup, name='signup-company'),
    url(r'^accounts/signup/private/$', views.private_signup, name='signup-private'),
    url(r'^accounts/signup/employee/$', views.employee_signup, name='signup-employee'),

    # Prevent default django-allauth from using default (generic) signup form
    url(r'^accounts/signup/$', page_not_found, {'exception': Http404()}),

]
