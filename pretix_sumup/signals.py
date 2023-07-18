# Register your receivers here
from pretix.base.signals import register_payment_providers
from django.http import HttpRequest, HttpResponse
from django.dispatch import receiver
from django.urls import resolve
from pretix.base.settings import settings_hierarkey
from django.utils.translation import gettext_lazy as _, gettext_noop
from i18nfield.strings import LazyI18nString
from pretix.base.middleware import _merge_csp, _parse_csp, _render_csp
from django.utils.crypto import get_random_string
from pretix.presale.signals import html_head, process_response
import sys


@receiver(register_payment_providers, dispatch_uid="payment_sumup")
def register_payment_provider(sender, **kwargs):
    from .payment import SumupPayment
    return SumupPayment


@receiver(signal=process_response, dispatch_uid="payment_sumup_middleware_resp")
def signal_process_response(sender, request: HttpRequest, response: HttpResponse, **kwargs):
    url = resolve(request.path_info)
    if url.url_name == "event.checkout":
        if 'Content-Security-Policy' in response:
            h = _parse_csp(response['Content-Security-Policy'])
        else:
            h = {}
            csps = {
                'script-src': ['https://gateway.sumup.com', 'https://net-tracker.notolytix.com', "'nonce-{}'".format(request.session["_sumup_nonce"]), "'unsafe-eval'"],
                'frame-src': ['https://gateway.sumup.com/', "'nonce-{}'".format(request.session["_sumup_nonce"])],
                'connect-src': ['https://gateway.sumup.com', 'https://api.sumup.com', 'https://api.notolytix.com','https://cdn.optimizely.com', "'nonce-{}'".format(request.session["_sumup_nonce"])],
                'img-src': ['https://static.sumup.com', "'nonce-{}'".format(request.session["_sumup_nonce"])],
                'style-src': ["'unsafe-inline'"]
            }

        _merge_csp(h, csps)
        if h:
            response['Content-Security-Policy'] = _render_csp(h)

    return response

