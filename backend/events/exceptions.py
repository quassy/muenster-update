from django.http import Http404
from rest_framework import exceptions
from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    # Rest Framework >= 3.15 passes on the untranslated message of Django's
    # Http404, keep responding with its own (translated) not found message
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    return drf_exception_handler(exc, context)
