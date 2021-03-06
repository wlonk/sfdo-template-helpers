from ipaddress import IPv4Address

from django.conf import settings
from django.core.exceptions import SuspiciousOperation


def get_remote_ip(request):
    """Get the IP address of the host that connected to Heroku

    (This may be a proxy, so don't assume it's the client's actual IP address.)
    """
    value = request.META.get("HTTP_X_FORWARDED_FOR") or request.META.get("REMOTE_ADDR")
    # X-Forwarded-For may be a list of multiple IP addresses.
    # The last one was added by Heroku so should be trustworthy.
    return value.split(",")[-1].strip()


class AdminRestrictMiddleware:
    """
    A middleware that restricts all access to the admin prefix to allowed IPs.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.ip_ranges = settings.ADMIN_API_ALLOWED_SUBNETS

    def __call__(self, request):
        if request.path.startswith(f"/{settings.ADMIN_AREA_PREFIX}"):
            self._validate_ip(request)

        return self.get_response(request)

    def _validate_ip(self, request):
        ip_str = get_remote_ip(request)
        ip_addr = IPv4Address(ip_str)

        if not any(ip_addr in subnet for subnet in self.ip_ranges):
            raise SuspiciousOperation(f"Disallowed IP address: {ip_addr}")
