import os
from allauth.account.models import EmailAddress
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from paypal.standard.models import ST_PP_COMPLETED

from dashboard.tasks import process_audio_file
from dashboard.models import CreditsPacketOffer, CreditsPacketPurchase
from moment_track import settings


def user_bought_credits_packet(sender, **kwargs):
    # Get the Instant Payment Notification object
    ipn = sender

    if ipn.payment_status == ST_PP_COMPLETED:
        # WARNING !
        # Check that the receiver email is the same we previously
        # set on the business field request. (The user could tamper
        # with those fields on payment form before send it to PayPal)
        if ipn.receiver_email != settings.PAYPAL_BUSINESS_EMAIL_ADDRESS:
            # Not a valid payment
            return

        # Retrieve custom user data
        if ipn.custom:
            try:
                # Retrieve the user using the email address used during the payment
                user = EmailAddress.objects.select_related('user').get(email__iexact=ipn.custom['buyer_email']).user
                offer = CreditsPacketOffer.objects.get(id=ipn.custom['offer_id'])
            except (ObjectDoesNotExist, IndexError):
                # If we reach this point it means that data has been tampered
                return

            # Check that the amount received is the expected one
            if (offer.cost_per_credit * ipn.quantity) == (ipn.mc_gross - ipn.mc_fee):
                purchase = CreditsPacketPurchase(
                    customer=user,
                    offer=offer,
                    credits_purchased=ipn.quantity
                )
                try:
                    purchase.full_clean()
                    purchase.save()
                except ValidationError:
                    return


def delete_file_on_model_deletion(sender, instance, **kwargs):
    """Deletes file from filesystem when corresponding sender model object is deleted."""
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)


def on_file_upload(sender, instance, created, **kwargs):
    """Run processing on file upload"""

    # Run the processing just on file creation, avoiding to repeat the
    # processing procedure on every model update
    if created:
        process_audio_file(instance.id)
