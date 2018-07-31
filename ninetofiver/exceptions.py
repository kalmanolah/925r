"""Exceptions."""
from django.core.exceptions import ValidationError
from rest_framework.views import exception_handler as base_exception_handler
from rest_framework import serializers
from rest_framework.utils.serializer_helpers import ReturnDict
import re


def error_message_to_key(msg):
    """Convert an error message to a translation key."""
    key = msg

    # Lowercase
    key = msg.lower()
    # Dashes + spaces -> underscores
    key = re.sub('[- ]', '_', key)
    # Remove all message placeholders
    key = re.sub('%\([a-z]+\)s', '', key)
    # Remove any non-alphebetical and non-underscore characters, leading/trailing underscores
    key = re.sub('[^a-z_]|(^_)|(_$)', '', key)
    # Deduplicate underscores
    key = re.sub('__', '_', key)

    # prefix = __name__
    prefix = 'ninetofiver.exceptions'

    key = '%s.%s' % (prefix, key)

    return key


def core_validation_error_to_dict(exc):
    """Convert a validation error to a dict."""
    if getattr(exc, 'error_dict', None):
        err_data = {}
        for field, err in exc.error_dict.items():
            err_data[field] = [core_validation_error_to_dict(x) for x in err]
        return err_data

    err_data = {
        'message': exc.message,
        'key': error_message_to_key(exc.message),
    }

    if exc.params:
        err_data['params'] = exc.params

    return err_data


def rest_validation_error_to_dict(exc):
    """Convert a validation error to a dict."""
    err_data = {}
    detail_type = type(exc.detail)

    if detail_type in [dict, ReturnDict]:
        for field, err in exc.detail.items():
            err_list = (err if type(err) in [tuple, list] else [err])
            err_data[field] = [{
                'message': x,
                'key': error_message_to_key(x),
            } for x in err_list]
    elif detail_type is list:
        err_data['error'] = [{'message': x, 'key': error_message_to_key(x)} for x in exc.detail]

    return err_data


def exception_handler(exc, context):
    """Handle an exception."""
    exc_type = type(exc)
    response = None

    if exc_type is ValidationError:
        if not getattr(exc, 'error_dict', None):
            exc = ValidationError({'error': exc})

        exc_data = core_validation_error_to_dict(exc)
        response = base_exception_handler(serializers.ValidationError(exc_data), context)
    elif exc_type is serializers.ValidationError:
        exc_data = rest_validation_error_to_dict(exc)
        response = base_exception_handler(serializers.ValidationError(exc_data), context)
    else:
        response = base_exception_handler(exc, context)

    return response
