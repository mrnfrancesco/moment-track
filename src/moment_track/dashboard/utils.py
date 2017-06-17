from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test

from dashboard.models import PrivateUser, CompanyUser, EmployeeUser


def get_actual_user(user):
    """
    Get the actual user type

    :param user: the user you want to know the actual type
    :type user: dashboard.models.User | django.contrib.auth.models.AnonymousUser
    :return: the actual user instance of the specified user or None if guest
    :rtype: PrivateUser | CompanyUser | EmployeeUser | None
    :raise ValueError: if user instance has an unknown user_type field value
    """
    if user.is_authenticated and user.user_type:
        if user.is_private:
            actual_user = user.private_user
        elif user.is_company:
            actual_user = user.company_user
        elif user.is_employee:
            actual_user = user.employee_user
        else:
            raise ValueError('User instance has an unknown user_type (%ud)' % (user.user_type,))
    else:
        actual_user = None

    return actual_user


def company_user_only(view_function):
    """Decorator for views that limits visibility to specified type of user(s)."""
    actual_decorator = user_passes_test(
        lambda user: user.is_company,
        login_url='/forbidden/',
        redirect_field_name=''  # no redirect field accepted
    )

    return actual_decorator(view_function)

