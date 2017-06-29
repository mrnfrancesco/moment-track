from datetime import date

from django.db.models import F, Sum

from dashboard.models import CreditsPacketPurchase, CreditsPacketOffer
from dashboard.utils import get_actual_user


def get_unexpired_credits(user):
    # if employee look at the company's contact person credits
    if user.is_employee:
        user = get_actual_user(user).company.contact_person.user

    return CreditsPacketPurchase.objects.filter(
        customer=user,
        expiration_date__gte=date.today(),
        credits_remaining__gt=0
    )


def get_total_available_processing_minutes(user):
    return get_unexpired_credits(user).annotate(
        minutes_left=F('offer__minutes_per_credit') * F('credits_remaining')
    ).aggregate(
        minutes_left_sum=Sum('minutes_left')
    ).get('minutes_left_sum') or 0


def get_total_available_credits(user):
    return get_unexpired_credits(user).aggregate(
        credits_remaining=Sum('credits_remaining')
    ).get('credits_remaining') or 0


def get_credits_distribution(user):
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
