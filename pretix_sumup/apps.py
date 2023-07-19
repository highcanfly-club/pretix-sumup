from django.utils.translation import gettext_lazy as _

from . import __version__

try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2.7 or above to run this plugin!")


class PluginApp(PluginConfig):
    default = True
    name = "pretix_sumup"
    verbose_name = "Sumup for Pretix"

    class PretixPluginMeta:
        name = _("Sumup for Pretix")
        author = "Ronan Le Meillat"
        picture = "pretix_sumup/sumup-logo-black.svg"
        description = _(
            "Sumup plugin is a payment plugin for enabling online payment via Sumup."
            "Note that you will need to register an OAuth application and require to the Sumup team to add the 'payment' scope"
        )
        visible = True
        version = __version__
        category = "PAYMENT"
        compatibility = "pretix>=2.7.0"

    def ready(self):
        from . import signals  # NOQA
