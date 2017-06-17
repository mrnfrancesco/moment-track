from __future__ import print_function

from django.contrib.sites.models import Site

from allauth.socialaccount.providers.dropbox_oauth2.provider import DropboxOAuth2Provider
from allauth.socialaccount.models import SocialApp


# Create site domain
print("Creating site domain...", end='')
site, _ = Site.objects.get_or_create(pk=1)
site.domain = '127.0.0.1:9000'
site.name = 'Moment Track'
site.save()
print("OK")

# Register Dropbox OAuth2 social app
print("Registering Dropbox OAuth2 social app...", end='')
social_app, _ = SocialApp.objects.get_or_create(pk=1)
social_app.provider = DropboxOAuth2Provider.id
social_app.name = 'Dropbox OAuth2'
social_app.client_id = 'zq6xbpqx3zh2i00'
social_app.secret = 'pkyu37aqhmgw9fs'
social_app.save()
social_app.sites.add(site)
social_app.save()
print("OK")

print("Done")
