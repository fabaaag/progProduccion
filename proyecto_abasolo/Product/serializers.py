from rest_framework import serializers

from .models import *
from JobManagement.models import Ruta, RutaPieza
from JobManagement.serializers import RutaSimpleSerializer, RutaPiezaSimpleSerializer
from Utils.serializers import *


class FamiliaProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamiliaProducto
        fields = ['codigo_familia', 'descripcion', 'id']

class SubfamiliaProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubfamiliaProducto
        fields = ['codigo_subfamilia', 'descripcion', 'id']

class TipoProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoProducto
        fields = '__all__'

class MateriaPrimaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MateriaPrima
        fields = '__all__'

class TerminacionFichaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TerminacionFicha
        fields = '__all__'

class FichaTecnicaSerializer(serializers.ModelSerializer):
    tipo_producto = TipoProductoSerializer()
    materia_prima = MateriaPrimaSerializer()
    terminacion_ficha = TerminacionFichaSerializer()

    class Meta:
        model = FichaTecnica
        fields = '__all__'

class ProductoSerializer(serializers.ModelSerializer):
    familia_producto = FamiliaProductoSerializer()
    subfamilia_producto = SubfamiliaProductoSerializer()
    ficha_tecnica = FichaTecnicaSerializer()
    rutas = RutaSimpleSerializer(many=True, read_only=True) 
    und_medida = MeasurementUnitSerializer()

    class Meta:
        model = Producto
        fields = ['codigo_producto', 'descripcion', 'familia_producto', 'subfamilia_producto', 'peso_unitario', 'und_medida', 'armado', 'ficha_tecnica', 'rutas']

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.order_by('codigo_producto')
        return queryset

    def create(self, validated_data):
        familia_producto_data = validated_data.pop('familia_producto')
        familia_producto = FamiliaProducto.objects.get(**familia_producto_data)
        producto = Producto.objects.create(familia_producto=familia_producto, **validated_data)
        return producto
    
class PiezaSerializer(serializers.ModelSerializer):
    familia_producto = FamiliaProductoSerializer()
    subfamilia_producto = SubfamiliaProductoSerializer()
    ficha_tecnica = FichaTecnicaSerializer()
    rutas = RutaPiezaSimpleSerializer(many=True, read_only=True)
    und_medida = MeasurementUnitSerializer()

    class Meta:
        model = Pieza
        fields = ['codigo_pieza', 'descripcion', 'familia_producto', 'subfamilia_producto', 'peso_unitario', 'und_medida', 'ficha_tecnica', 'rutas']

    def create(self, validated_data):
        familia_producto_data = validated_data.pop('familia_producto')
        subfamilia_producto_data = validated_data.pop('subfamilia_producto')

        familia_producto, created = FamiliaProducto.objects.get_or_create(**familia_producto_data)
        subfamilia_producto, created = SubfamiliaProducto.objects.get_or_create(**subfamilia_producto_data, familia_producto = familia_producto)

        pieza = Pieza.objects.create(familia_producto=familia_producto, subfamilia_producto=subfamilia_producto, **validated_data)
        return pieza
    
    def update(self, instance, validated_data):
        familia_producto_data = validated_data.pop('familia_producto', None)
        subfamilia_producto_data = validated_data.pop('subfamilia_producto', None)

        if familia_producto_data:
            familia_producto, created = FamiliaProducto.objects.get_or_create(**familia_producto_data)
            instance.familia_producto = familia_producto

        if subfamilia_producto_data:
            subfamilia_producto, created = SubfamiliaProducto.objects.get_or_create(**subfamilia_producto_data)
            instance.subfamilia_producto = subfamilia_producto

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
    
    def get_ruta_pieza(self, obj):
        rutas_pieza = RutaPieza.objects.filter(pieza=obj).order_by('-nro_etapa')
        return RutaPiezaSimpleSerializer(rutas_pieza, many=True).data
 
