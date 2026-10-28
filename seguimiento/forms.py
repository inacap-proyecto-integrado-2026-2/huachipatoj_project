from django import forms
from .models import Jugador

class JugadorForm(forms.ModelForm):
    class Meta:
        model = Jugador
        fields = ['rut', 'nombre_completo', 'categoria', 'fecha_nacimiento', 'contacto_emergencia', 'observaciones']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'observaciones': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Escribe una observación inicial para el deportista...'}),
        }