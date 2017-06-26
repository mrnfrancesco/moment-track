from allauth.account.models import EmailAddress
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from paypal.standard.models import ST_PP_COMPLETED

from dashboard.models import CreditsPacketOffer, CreditsPacketPurchase
from moment_track import settings


def private_user_bought_credits_packet(sender, **kwargs):
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
