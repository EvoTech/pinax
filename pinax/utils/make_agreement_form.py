from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _


def default_form_agreement_text():
    """Returns default agreement text for form."""
    text = _("I have read and agree to the <a href=\"%(terms_url)s\">Terms of Use</a> and <a href=\"%(privacy_url)s\">Privacy Policy</a>.") %\
        {'terms_url': reverse('terms'),
         'privacy_url': reverse('privacy'), }
    return text

FORM_AGREEMENT_TEXT = getattr(settings, 'FORM_AGREEMENT_TEXT',
                              default_form_agreement_text)


def make_agreement_form(Form, agreement_text=FORM_AGREEMENT_TEXT):
    """Returns form class with agree terms field"""

    class AgreeForm(Form):
        """Form class with agree terms field"""
        def __init__(self, *args, **kwargs):
            """Instance constructor."""
            r = super(AgreeForm, self).__init__(*args, **kwargs)
            if callable(agreement_text):
                text = agreement_text()
            else:
                text = agreement_text
            self.fields['terms_agree'].help_text = text
            #if hasattr(self, 'instance') and self.instance.pk:
            #    self.fields['terms_agree'].initial = True
            return r

        terms_agree = forms.BooleanField(
            label=_("I agree to the terms and conditions."),
            required=True,
            initial=False
        )

    return AgreeForm
