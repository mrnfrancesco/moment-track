"""moment_track URL Configuration

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
from django.conf.urls import url, include

from rest_framework import routers
from rest_framework_swagger.views import get_swagger_view

from dashboard.api import views as api_views


router = routers.DefaultRouter()
router.register(r'files', api_views.AudioFileViewSet)

urlpatterns = [
    url(r'', include('dashboard.urls')),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^paypal/', include('paypal.standard.ipn.urls')),

    url(r'^api/v1/$', get_swagger_view(), name='api-doc'),
    url(r'^api/v1/', include(router.urls, namespace='v1')),
    url(r'^api/v1/statistics/$', api_views.Statistics.as_view(), name='api-statistics'),
    url(
        r'^api/v1/files/(?P<id>[0-9]+)/search/(?P<query>.+)/$',
        api_views.SearchInFile.as_view(),
        name='api-search-in-file'
    ),
]
