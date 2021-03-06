from datetime import date

import math
from django.db import transaction
from django.db.models import F, Sum

from dashboard.models import CreditsPacketPurchase, CreditsPacketOffer
from dashboard.utils import get_actual_user


def get_unexpired_credits(user):
    """Return a QuerySet representing the unexpired non-empty credits
    available for the specified user.
    """
    # if employee look at the company's contact person credits
    if user.is_employee:
        user = get_actual_user(user).company.contact_person.user

    return CreditsPacketPurchase.objects.filter(
        customer=user,
        expiration_date__gte=date.today(),
        credits_remaining__gt=0
    )


def get_total_available_processing_minutes(user):
    """Return the total available processing minutes for the specified user
    as results of the available credits.
    """
    return get_unexpired_credits(user).annotate(
        minutes_left=F('offer__minutes_per_credit') * F('credits_remaining')
    ).aggregate(
        minutes_left_sum=Sum('minutes_left')
    ).get('minutes_left_sum') or 0


def get_total_available_credits(user):
    """Return the total available credits for the specified user."""
    return get_unexpired_credits(user).aggregate(
        credits_remaining=Sum('credits_remaining')
    ).get('credits_remaining') or 0


def get_credits_distribution(user):
    """Return a QuerySet representing the available credits for the specified user."""
    today = date.today()

    credits_distribution = get_unexpired_credits(user).values(
        'offer__minutes_per_credit',
        'credits_purchased',
        'credits_remaining',
        'expiration_date'
    )
    # Change expiration date into days left before expiration
    for t in credits_distribution:
        t['days_before_expiration'] = (t['expiration_date'] - today).days
        del t['expiration_date']

    return credits_distribution


def get_unexpired_offers():
    """Return a dictionary representing the available non-expired offers
    for credits purchasing.
    """
    today = date.today()

    offers = CreditsPacketOffer.objects.exclude(
        date_end__lte=today
    ).values(
        'id',
        'date_end',
        'minutes_per_credit',
        'cost_per_credit'
    )

    for offer in offers:
        # Change offer expiration date into days left before expiration
        if offer['date_end']:
            offer['days_left'] = (offer['date_end'] - today).days
        else:
            offer['days_left'] = None
        del offer['date_end']

    return offers


@transaction.atomic
def calculate_credits_usage(audio):
    """Calculate the best usage possible of credits to process the specified audio
    and update the database accordingly.
    """
    duration = math.ceil(audio.duration.total_seconds() / 60.0)

    with transaction.atomic():
        while duration > 0:
            unexpired_credits = get_unexpired_credits(audio.uploader)\
                .select_related('offer')\
                .order_by('offer__minutes_per_credit')

            # take the biggest credit with minutes-per-credit <= duration
            result = unexpired_credits.filter(offer__minutes_per_credit__lte=duration).last()
            if result is not None:
                CreditsPacketPurchase.objects.filter(pk=result.pk).update(credits_remaining=F('credits_remaining') - 1)
                duration -= result.offer.minutes_per_credit
            else:
                # take the smallest credit with minute-per-credit > duration
                result = unexpired_credits.filter(offer__minutes_per_credit__gt=duration).first()
                if result is not None:
                    CreditsPacketPurchase.objects.filter(pk=result.pk).update(credits_remaining=F('credits_remaining') - 1)
                    duration -= result.offer.minutes_per_credit
                else:
                    raise ValueError('Not enough credits left')
