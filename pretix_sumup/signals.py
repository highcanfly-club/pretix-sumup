# Register your receivers here
from django.dispatch import receiver
from django.http import HttpRequest, HttpResponse
from django.urls import resolve
from pretix.base.middleware import _merge_csp, _parse_csp, _render_csp
from pretix.base.signals import register_payment_providers
from pretix.presale.signals import process_response

from .payment import getNonce


@receiver(register_payment_providers, dispatch_uid="payment_sumup")
def register_payment_provider(sender, **kwargs):
    from .payment import SumupPayment

    return SumupPayment


@receiver(signal=process_response, dispatch_uid="payment_sumup_middleware_resp")
def signal_process_response(
    sender, request: HttpRequest, response: HttpResponse, **kwargs
):
    url = resolve(request.path_info)
    if url.url_name == "event.checkout":
        if "Content-Security-Policy" in response:
            h = _parse_csp(response["Content-Security-Policy"])
        else:
            h = {}
            csps = {
                "script-src": [
                    "https://gateway.sumup.com",
                    "https://net-tracker.notolytix.com",
                    "'nonce-{}'".format(getNonce(request)),
                    "'unsafe-eval'",
                ],
                "frame-src": [
                    "https://gateway.sumup.com/",
                    "'nonce-{}'".format(getNonce(request)),
                ],
                "connect-src": [
                    "https://gateway.sumup.com",
                    "https://api.sumup.com",
                    "https://api.notolytix.com",
                    "https://cdn.optimizely.com",
                    "'nonce-{}'".format(getNonce(request)),
                ],
                "img-src": [
                    "https://static.sumup.com",
                    "'nonce-{}'".format(getNonce(request)),
                ],
                "style-src": ["'unsafe-inline'"],
            }

        _merge_csp(h, csps)
        if h:
            response["Content-Security-Policy"] = _render_csp(h)

    return response
