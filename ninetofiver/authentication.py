""""Authentication."""
from django.utils.translation import ugettext_lazy as _
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication as BaseTokenAuthentication


class ApiKeyAuthentication(BaseTokenAuthentication):
    """API key authentication."""

    def authenticate(self, request):
        """Authenticate the request."""
        token = request.GET.get('api_key', None)

        if not token:
            msg = _('Invalid token. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)

        res = self.authenticate_credentials(token)

        # Only allow GETs using API keys
        if request.method != 'GET':
            msg = _('The token provided is only valid for read-only requests.')
            raise exceptions.AuthenticationFailed(msg)

        return res

    def authenticate_header(self, request):
        return None
