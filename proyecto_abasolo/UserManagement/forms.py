from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    rut = forms.CharField(
        max_length=12,
        help_text="Formato: XX.XXX.XXX-X",
        widget=forms.TextInput(attrs={'placeholder': '12.345.678-9'})
    )

    telefono = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '+56912345678'})
    )

    cargo = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ej: Operador Prensa'})
    )

    class Meta:
        model = CustomUser
        fields = [
            'username',
            'rut',
            'first_name',
            'last_name',
            'email',
            'telefono',
            'cargo',
            'password1',
            'password2'
        ]

    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        if CustomUser.objects.filter(rut=rut).exists():
            raise ValidationError("Este RUT ya está registrado en el sistema.")
        return rut
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user

class CustomUserChangeForm(UserChangeForm):
    password = None

    class Meta:
        model = CustomUser
        fields = [
            'first_name',
            'last_name',
            'email',
            'telefono',
            'cargo'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #Hacer que el RUT sea de solo lectura en la edición
        if 'rut' in self.fields:
            self.fields['rut'].widget.attrs['readonly'] = True


class SupervisorCreationForm(CustomUserCreationForm):
    class Meta(CustomUserCreationForm.Meta):
        model = CustomUser
        fields = CustomUserCreationForm.Meta.fields + ['rol']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #Limitar las opciones de rol solo a Supervisor
        self.fields['rol'].choices = [('SUPERVISOR', 'Supervisor')]
        self.fields['rol'].initial = 'SUPERVISOR'
        self.fields['rol'].widget.attrs['readonly'] = True

class OperadorCreationForm(CustomUserCreationForm):
    class Meta(CustomUserCreationForm.Meta):
        model = CustomUser
        fields = CustomUserCreationForm.Meta.fields

    def save(self, commit=True):
        user = super().save(commit=False)
        user.rol = 'OPERADOR'
        if commit:
            user.save()                
        return user
    
class AdminUserChangeForm(UserChangeForm):
    """Formulario especial para administradores que permite modificar todos los campos"""
    password = None

    class Meta:
        model = CustomUser
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'telefono',
            'cargo',
            'rol',
            'activo'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #Permitir cambiar el rol solo si el usuario es administrador
        if not self.instance.is_admin:
            self.fields['rol'].widget.attrs['disabled'] = True