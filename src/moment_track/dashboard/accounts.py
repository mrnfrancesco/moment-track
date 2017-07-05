def user_displayable_name(user):
    """
    Use some basic information to build a string representing the given user.
    :param user: the user you want a displayable name
    :type user: settings.AUTH_USER_MODEL | PrivateUser | CompanyUser | EmployeeUser
    :return: the user displayable name
    :rtype: str
    """
    if user.first_name or user.last_name:
        displayable_name = ' '.join((user.first_name, user.last_name))
    else:
        displayable_name = user.email[:user.email.find('@')]

    return displayable_name
