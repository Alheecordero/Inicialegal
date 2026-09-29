from django import forms

from .models import Comment


class CommentForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput)  # honeypot

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
