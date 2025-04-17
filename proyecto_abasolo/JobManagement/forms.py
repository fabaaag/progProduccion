from django import forms
from django.core.exceptions import ValidationError

from .models import OrdenTrabajo, RutaOT
from .models import ProgramaOrdenTrabajo, OrdenTrabajo, SituacionOT

class OrdenTrabajoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ruta_ot'] = forms.ModelChoiceField(queryset=RutaOT.objects.all(), required=False)

    class Meta:
        model = OrdenTrabajo
        fields = '__all__'

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data['ruta_ot']:
            ruta_ot_instance = self.cleaned_data['ruta_ot']
            ruta_ot_instance.orden_trabajo = instance
            ruta_ot_instance.save()
        if commit:
            instance.save()
        return instance

class ProgramaOrdenTrabajoAdminForm(forms.ModelForm):
    class Meta:
        model = ProgramaOrdenTrabajo
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ProgramaOrdenTrabajoAdminForm, self).__init__(*args, **kwargs)
        # Filter the orden_trabajo queryset
        situacion_ot_ids = SituacionOT.objects.filter(codigo_situacion_ot__in=['P', 'S']).values_list('id', flat=True)
        self.fields['orden_trabajo'].queryset = OrdenTrabajo.objects.filter(situacion_ot_id__in=situacion_ot_ids)