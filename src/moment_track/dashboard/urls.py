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
from django.http import Http404, HttpResponseForbidden
from django.views.defaults import page_not_found, permission_denied
from django.views.generic import TemplateView, RedirectView

from dashboard import views

app_name = 'dashboard'
urlpatterns = [
    url(r'^forbidden/$', permission_denied, {'exception': HttpResponseForbidden()}, name='forbidden'),

    # file listing, editing, deleting and content searching
    url(r'^$', RedirectView.as_view(url='files/list/', permanent=True), name='index'),
    url(r'^files/list/$', views.list_files, name='list-files'),
    url(r'^files/edit/$', views.edit_file, name='edit-file'),
    url(r'^files/delete/$', views.delete_file, name='delete-file'),
    url(r'^files/search/$', views.search_in_file, name='search-in-file'),

    url(
        r'^privacy-policy/$',
        TemplateView.as_view(template_name='dashboard/legal-notes/privacy-policy.html'),
        name='privacy-policy'
    ),
    url(
        r'^terms-of-service/$',
        TemplateView.as_view(template_name='dashboard/legal-notes/terms-of-service.html'),
        name='terms-of-service'
    ),

    # Account signup
    url(r'^accounts/signup/company/$', views.company_signup, name='signup-company'),
    url(r'^accounts/signup/private/$', views.private_signup, name='signup-private'),

    # Prevent default django-allauth from using default (generic) signup form
    url(r'^accounts/signup/$', page_not_found, {'exception': Http404()}),

    # Users' profile management pages
    url(r'^profile/private/$', views.private_user_profile, name='private-user-profile'),
    url(r'^profile/company/$', views.company_user_profile, name='company-user-profile'),
    url(r'^profile/employee/$', views.employee_user_profile, name='employee-user-profile'),
    url(r'^profile/employee/company/$', views.employee_company_details, name='employee-company-details'),

    # Company user management pages
    url(r'^company/details/$', views.company_details, name='company-details'),
    url(r'^company/employees/$', views.company_employees, name='company-employees'),
    url(  # used for using reverse url function without employee_id parameter
        r'^company/employees/invert-active-status/$',
        page_not_found, {'exception': Http404()},
        name='invert-employee-account-active-status'
    ),
    url(
        r'^company/employees/invert-active-status/(?P<employee_id>[0-9]+)$',
        views.invert_employee_account_active_status,
        name='invert-employee-account-active-status'
    ),

    # payment management
    url(r'^payment-cancelled/$', views.payment_cancelled, name='payment-cancelled'),
    url(r'^payment-completed/$', views.payment_completed, name='payment-completed'),

    # private and company user credits management
    url(r'^credits/$', views.credits, name='credits'),

    # File upload
    url(r'^upload-file/$', views.upload_file, name='upload-file'),
    url(r'^upload-file/error/$', views.upload_file_error, name='upload-file-error'),
    url(r'^upload-file/success/$', views.upload_file_success, name='upload-file-success'),
    url(r'^upload-file/not-enough-credits/$', views.not_enough_credits, name='not-enough-credits'),
]
