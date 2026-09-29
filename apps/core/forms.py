from django import forms
from django.forms.models import ModelChoiceIterator
from django.utils.translation import gettext_lazy as _

from .models import ContactMessage, Plan, Service


class ServiceChoiceIterator(ModelChoiceIterator):
    """Agrupa servicios por área de práctica en el select."""

    def __iter__(self):
        if self.field.empty_label is not None:
            yield ("", self.field.empty_label)
        queryset = self.queryset.order_by("area__order", "area__name", "order", "pk")
        area_name = None
        bucket = []
        for obj in queryset:
            group = obj.area.name if obj.area_id else str(_("General"))
            if area_name is not None and group != area_name:
                yield area_name, bucket
                bucket = []
            area_name = group
            bucket.append(self.choice(obj))
        if bucket:
            yield area_name, bucket


class GroupedServiceChoiceField(forms.ModelChoiceField):
    iterator = ServiceChoiceIterator


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
        service_field = GroupedServiceChoiceField(
            queryset=Service.objects.filter(is_active=True).select_related("area"),
            required=False,
            empty_label=_("Seleccione un servicio (opcional)"),
            widget=forms.Select(attrs={"class": "form-select"}),
        )
        self.fields["service"] = service_field
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
