from rest_framework import serializers
from .models import TipoMaquina, EstadoOperatividad, EstadoMaquina

class TipoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoMaquina
        fields = ['id', 'codigo', 'descripcion']

class EstadoOperatividadSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadoOperatividad
        fields =['id', 'estado', 'descripcion']

class EstadoMaquinaSerializer(serializers.ModelSerializer):
    tipos_maquina = TipoMaquinaSerializer(many=True, read_only=True)
    estado_operatividad = EstadoOperatividadSerializer(read_only=True)

    class Meta:
        model = EstadoMaquina
        fields = [
            'id',
            'tipos_maquina',
            'estado_operatividad',
            'motivo_estado',
            'fecha_ultimo_cambio',
            'disponible',
            'capacidad_maxima',
            'observaciones'
        ]
