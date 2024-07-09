"""Django context processors."""

import environ
from django.conf import settings
from users.models import CustomUser

env = environ.FileAwareEnv()


def export_vars(request) -> dict:
    """Export environment variables to Django templates.

    https://stackoverflow.com/questions/43207563/how-can-i-access-environment-variables-directly-in-a-django-template/43211490#43211490?newreg=9f02cb1a210c4f618f41fb1759bd9fb3

    Useage
    ------

    An example of how to access the environment variable in the template using
    just the data dict key to pass the CSS file location to the template.


    <link rel="stylesheet" href="{{ CSS }}">


    """

    data: dict = {}

    data["PROJECT_NAME"] = "Example"

    return data
