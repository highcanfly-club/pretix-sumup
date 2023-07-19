import json
import requests
import sys
import uuid
from collections import OrderedDict
from django import forms
from django.http import HttpRequest
from django.template.loader import get_template
from django.utils.crypto import get_random_string
from django.utils.translation import get_language, gettext_lazy as _, to_locale
from i18nfield.strings import LazyI18nString
from pretix.base.models import OrderPayment
from pretix.base.payment import BasePaymentProvider


def getNonce(request):
    if "_sumup_nonce" not in request.session:
        request.session["_sumup_nonce"] = get_random_string(32)
    return request.session["_sumup_nonce"]


class SumupPayment(BasePaymentProvider):
    identifier = "sumuppayment"
    verbose_name = _("Sumup Payment")
    abort_pending_allowed = True

    @property
    def test_mode_message(self):
        return _(
            "In test mode, you can just manually mark this order as paid in the backend after it has been "
            "created."
        )

    @property
    def settings_form_fields(self):
        fields = [
            (
                "client_id",
                forms.CharField(
                    label=_("Sumup Oauth App Client ID"),
                    max_length=40,
                    min_length=40,
                    help_text=_("Find it in the developer application view"),
                ),
            ),
            (
                "secret",
                forms.CharField(
                    label=_("Sumup Secret"),
                    max_length=64,
                    min_length=64,
                    help_text=_("This is Sumup OAuth app Client Secret"),
                ),
            ),
            (
                "sumupid",
                forms.CharField(
                    label=_("Sumup ID"),
                    max_length=12,
                    min_length=8,
                    help_text=_(
                        "This is Sumup Client ID (under your name on the top right of the main Sumup screen)"
                    ),
                ),
            ),
        ]
        return OrderedDict(fields + list(super().settings_form_fields.items()))

    def sumup_get_token(self, _clientId, _clientSecret) -> str | bool:
        url = "https://api.sumup.com/token"
        data = {
            "client_id": _clientId,
            "client_secret": _clientSecret,
            "grant_type": "client_credentials",
            "scope": "user.payout-settings user.app-settings transactions.history user.profile_readonly payments",
        }
        payload = json.dumps(data)
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        response = requests.request("POST", url, headers=headers, data=payload)
        jsonResponse = response.json()
        print(jsonResponse, file=sys.stderr)
        if "payments" in jsonResponse["scope"]:
            return jsonResponse["access_token"]
        else:
            return False

    def sumup_create_checkout(
        self, merchantToken, sumupId, amount, email, firstName, lastName
    ):
        url = "https://api.sumup.com/v0.1/checkouts"
        data = {
            "checkout_reference": str(uuid.uuid4()),
            "amount": amount,
            "currency": self.event.currency,
            "merchant_code": sumupId,
            "personal_details": {
                "email": email,
                "first_name": firstName,
                "last_name": lastName,
            },
        }
        payload = json.dumps(data)
        print(payload, file=sys.stderr)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Bearer " + merchantToken,
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        return response

    def check_sumup_payment_done(self, sumupToken, sumupCheckout):
        print("SumupPayment.check_sumup_payment_done", file=sys.stderr)
        url = "https://api.sumup.com/v0.1/checkouts/" + sumupCheckout["id"]
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Bearer " + sumupToken,
        }
        response = requests.request("GET", url, headers=headers)
        sumupResponse = json.loads(response.content)
        print(
            "Sumup checkout:{} status: {}".format(
                sumupCheckout["id"], sumupResponse["status"]
            ),
            file=sys.stderr,
        )
        if sumupResponse["status"] == "PAID":
            return True
        else:
            return False

    def payment_form_render(self, request) -> str:
        print("SumupPayment.payment_form_render", file=sys.stderr)
        ctx = {}
        template = get_template("pretix_sumup/prepare.html")
        return template.render(ctx)

    def checkout_prepare(self, request, cart):
        print("SumupPayment.checkout_prepare", file=sys.stderr)
        client_id = self.settings.get("client_id")
        secret = self.settings.get("secret")
        sumupid = self.settings.get("sumupid")
        sumupToken = self.sumup_get_token(client_id, secret)
        if isinstance(sumupToken, str):
            sumupCheckoutResponse = self.sumup_create_checkout(
                sumupToken,
                sumupid,
                str(cart["total"]),
                "none@example.com",
                "none",
                "example",
            )
            if sumupCheckoutResponse.status_code == 201:
                print(
                    "SumupPayment.checkout_prepare OK: "
                    + str(sumupCheckoutResponse.content),
                    file=sys.stderr,
                )
                request.session["sumupCheckout"] = json.loads(
                    sumupCheckoutResponse.content
                )
                request.session["sumupToken"] = sumupToken
                return True
            else:
                request.session["sumupCheckout"] = ""
                request.session["sumupToken"] = ""
                return False
        request.session["sumupCheckout"] = ""
        request.session["sumupToken"] = ""
        return False

    def payment_prepare(
        self, request: HttpRequest, payment: OrderPayment
    ) -> bool | str:
        print("SumupPayment.payment_prepare", file=sys.stderr)
        return True

    def payment_is_valid_session(self, request):
        print("SumupPayment.payment_is_valid_session", file=sys.stderr)
        return True

    def execute_payment(self, request: HttpRequest, payment: OrderPayment):
        print("SumupPayment.execute_payment", file=sys.stderr)
        if ("sumupCheckout" in request.session) and ("sumupToken" in request.session):
            if self.check_sumup_payment_done(
                request.session["sumupToken"], request.session["sumupCheckout"]
            ):
                payment.confirm()

    def get_sumup_locale(self, request):
        languageDjango = get_language()
        localeDjango = to_locale(languageDjango)
        baseLocale = localeDjango[0:2]
        subLocale = localeDjango[3:5].upper()
        if subLocale == "":
            subLocale = baseLocale.upper()
        locale = "{}-{}".format(baseLocale, subLocale)
        return locale

    def checkout_confirm_render(self, request):
        print("SumupPayment.checkout_confirm_render", file=sys.stderr)
        ctx = {
            "request": request,
            "event": self.event,
            "sumupCheckout": request.session["sumupCheckout"],
            "nonce": getNonce(request),
            "locale": self.get_sumup_locale(request),
            "btn_text": _("Payment OK, get your ticket"),
        }
        template = get_template("pretix_sumup/checkout_payment_form.html")
        return template.render(ctx)

    def order_pending_mail_render(self, order) -> str:
        print("SumupPayment.order_pending_mail_render", file=sys.stderr)
        template = get_template("pretix_sumup/email/order_pending.txt")
        ctx = {
            "event": self.event,
            "order": order,
            "information_text": self.settings.get(
                "information_text", as_type=LazyI18nString
            ),
        }
        return template.render(ctx)

    def payment_pending_render(self, request: HttpRequest, payment: OrderPayment):
        print("SumupPayment.payment_pending_render", file=sys.stderr)
        template = get_template("pretix_sumup/pending.html")
        ctx = {
            "event": self.event,
            "order": payment.order,
            "information_text": self.settings.get(
                "information_text", as_type=LazyI18nString
            ),
        }
        return template.render(ctx)

    def payment_control_render(self, request: HttpRequest, payment: OrderPayment):
        print("SumupPayment.payment_control_render", file=sys.stderr)
        template = get_template("pretix_sumup/control.html")
        ctx = {
            "request": request,
            "event": self.event,
            "payment_info": payment.info_data,
            "order": payment.order,
        }
        return template.render(ctx)
