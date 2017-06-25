from __future__ import print_function

from django.contrib.sites.models import Site

from allauth.socialaccount.providers.dropbox_oauth2.provider import DropboxOAuth2Provider
from allauth.socialaccount.models import SocialApp

from dashboard.models import User, CreditsPacketOffer

for ModelCls in (User, Site, SocialApp, CreditsPacketOffer):
    print("Deleting %s..." % ModelCls.__name__, end='')
    ModelCls.objects.all().delete()
    print("OK")

print("Creating site domain...", end='')
site = Site(
    pk=1,
    domain='127.0.0.1:9000',
    name='Moment Track'
)
site.full_clean()
site.save()
print("OK")

print("Registering Dropbox OAuth2 social app...", end='')
social_app = SocialApp(
    provider=DropboxOAuth2Provider.id,
    name='Dropbox OAuth2',
    client_id='zq6xbpqx3zh2i00',
    secret='pkyu37aqhmgw9fs'
)
social_app.full_clean()
social_app.save()
social_app.sites.add(site)
social_app.save()
print("OK")

print("Done")
