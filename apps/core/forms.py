from django import forms
from django.utils.translation import gettext_lazy as _

from .models import ContactMessage, Plan, Service


class ContactForm(forms.ModelForm):
    # Honeypot anti-spam
    website = forms.CharField(required=False, widget=forms.HiddenInput)
    accept = forms.BooleanField(
        label=_("He leído y acepto la Política de Privacidad."),
        required=True,
        error_messages={"required": _("Debe aceptar la Política de Privacidad para enviar su solicitud.")},
    )

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "phone", "company", "plan", "service", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": _("Nombre y apellido")}),
            "email": forms.EmailInput(attrs={"placeholder": "nombre@empresa.cl"}),
            "phone": forms.TextInput(attrs={"placeholder": "+56 9 1234 5678"}),
            "company": forms.TextInput(attrs={"placeholder": _("Nombre de su empresa (opcional)")}),
            "subject": forms.TextInput(attrs={"placeholder": _("¿En qué podemos ayudarle?")}),
            "message": forms.Textarea(attrs={"rows": 5, "placeholder": _("Describa brevemente su situación o consulta.")}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["plan"].queryset = Plan.objects.filter(is_active=True)
        self.fields["plan"].empty_label = _("Seleccione un plan (opcional)")
        self.fields["service"].queryset = Service.objects.filter(is_active=True).select_related("area").order_by(
            "area__order", "order", "pk"
        )
        self.fields["service"].empty_label = _("Seleccione un servicio (opcional)")
        for name, field in self.fields.items():
            if name == "accept":
                field.widget.attrs["class"] = "form-check-input"
            elif name != "website":
                css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
                field.widget.attrs["class"] = css

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Solicitud inválida.")
        return ""


class NewsletterForm(forms.Form):
    # Formulario simple (no ModelForm) para que un correo ya suscrito no sea rechazado por `unique`.
    email = forms.EmailField(
        label=_("Correo electrónico"),
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": _("Su correo electrónico"), "aria-label": _("Correo electrónico")}),
    )
    accept = forms.BooleanField(
        required=True,
        error_messages={"required": _("Debe aceptar el tratamiento de su correo para suscribirse.")},
    )

    def clean_email(self):
        return self.cleaned_data["email"].lower().strip()
