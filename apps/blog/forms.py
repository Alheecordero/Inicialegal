from django import forms

from .models import Comment


class CommentForm(forms.ModelForm):
    # Honeypot anti-spam
    website = forms.CharField(
        required=False,
        label="",
        # Campo de texto real (los bots lo rellenan), fuera de la vista y del foco para las personas.
        widget=forms.TextInput(attrs={
            "autocomplete": "off",
            "tabindex": "-1",
            "aria-hidden": "true",
            "style": "position:absolute;left:-10000px;width:1px;height:1px;overflow:hidden;",
        }),
    )

    class Meta:
        model = Comment
        fields = ["name", "email", "body"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Tu nombre"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Tu correo (no se publica)"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Escribe tu comentario"}),
        }

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Solicitud inválida.")
        return ""
