from rest_framework import serializers
from .models import MateriaPrima, MeasurementUnit


class MeasurementUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementUnit
        fields = '__all__'

class MateriaPrimaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MateriaPrima
        fields = '__all__'