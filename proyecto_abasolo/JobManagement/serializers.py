from importlib import import_module

from django.apps import apps
from django.utils import timezone
from rest_framework import serializers

from .models import *
from Client.serializers import ClienteSerializer
from Utils.serializers import MateriaPrimaSerializer, MeasurementUnitSerializer
from .utils import calcular_progreso_acumulado

class EmpresaOTSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpresaOT
        fields = '__all__'


class MaquinaSerializer(serializers.ModelSerializer):
    empresa = EmpresaOTSerializer()
    
    class Meta:
        model = Maquina
        fields = ['id', 'codigo_maquina', 'descripcion', 'empresa']

class ProcesoSerializer(serializers.ModelSerializer):
    empresa = EmpresaOTSerializer()

    class Meta:
        model = Proceso
        fields = '__all__'

class RutaSimpleSerializer(serializers.ModelSerializer):
    proceso = ProcesoSerializer(read_only=True)
    maquina = MaquinaSerializer(read_only=True)

    class Meta:
        model = Ruta
        fields = ['nro_etapa', 'proceso', 'maquina', 'estandar']

class RutaPiezaSimpleSerializer(serializers.ModelSerializer):
    proceso = ProcesoSerializer(read_only=True)
    maquina = MaquinaSerializer(read_only=True)

    class Meta:
        model = RutaPieza
        fields = ['nro_etapa', 'proceso', 'maquina', 'estandar']

class RutaSerializer(serializers.ModelSerializer):
    producto = serializers.PrimaryKeyRelatedField(read_only=True)
    proceso = ProcesoSerializer()
    maquina = MaquinaSerializer()

    class Meta:
        model = Ruta
        fields = ['producto', 'nro_etapa', 'proceso', 'maquina', 'estandar']

class RutaPiezaSerializer(serializers.ModelSerializer):
    pieza = serializers.PrimaryKeyRelatedField(read_only=True)
    proceso = ProcesoSerializer()
    maquina = MaquinaSerializer()

    class Meta:
        model = RutaPieza
        fields = ['pieza', 'nro_etapa', 'proceso', 'maquina', 'estandar']

class TipoOTSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoOT
        fields = '__all__'

class SituacionOTSerializer(serializers.ModelSerializer):
    class Meta:
        model = SituacionOT
        fields = '__all__'

class ItemRutaSerializer(serializers.ModelSerializer):
    maquina = MaquinaSerializer()
    proceso = ProcesoSerializer()

    class Meta:
        model = ItemRuta
        fields = ['id', 'item', 'maquina', 'proceso', 'estandar', 'cantidad_pedido', 'cantidad_terminado_proceso', 'cantidad_perdida_proceso', 'terminado_sin_actualizar']

    def update(self, instance, validated_data):
        instance.estandar = validated_data.get('estandar', instance.estandar)
        instance.maquina = validated_data.get('maquina', instance.maquina)
        instance.save()
        return instance
    
class RutaOTSerializer(serializers.ModelSerializer):
    items = ItemRutaSerializer(many=True)
    class Meta:
        model = RutaOT
        fields = ['items']

        def update(self, instance, validated_data):
            items_data = validated_data.get('items')
            for item_data in items_data:
                item_id = item_data.get(0)  
                item_instance = ItemRuta.objects.get(id=item_id, ruta=instance)
                item_serializer = ItemRutaSerializer(item_instance, data=item_data)
            
                if item_serializer.is_valid():
                    item_serializer.save()
            return instance
        
class OrdenTrabajoSerializer(serializers.ModelSerializer):

    tipo_ot = TipoOTSerializer()
    situacion_ot = SituacionOTSerializer()
    cliente = ClienteSerializer()
    unidad_medida = MeasurementUnitSerializer()
    materia_prima = MateriaPrimaSerializer()
    unidad_medida_mprima = MeasurementUnitSerializer()
    empresa = EmpresaOTSerializer()
    descripcion_producto_ot_instance = serializers.SerializerMethodField()
    ruta_ot = RutaOTSerializer()
    dias_atrasos = serializers.SerializerMethodField()
    fecha_emision_formated = serializers.SerializerMethodField()
    fecha_proc_formated = serializers.SerializerMethodField()
    fecha_termino_formated = serializers.SerializerMethodField()

    def to_representation(self, instance):
        if isinstance(instance, ProgramaOrdenTrabajo):
            instance = instance.orden_trabajo
        return super().to_representation(instance)
    
    class Meta:
        model = OrdenTrabajo
        fields = [
            'id', 'codigo_ot', 'tipo_ot', 'situacion_ot', 'fecha_emision', 'fecha_proc', 'fecha_termino', 'fecha_emision_formated', 'fecha_proc_formated', 'fecha_termino_formated', 'cliente', 'nro_nota_venta_ot', 'item_nota_venta', 'referencia_nota_venta', 'codigo_producto_inicial', 'codigo_producto_salida', 'descripcion_producto_ot', 'descripcion_producto_ot_instance', 'cantidad', 'unidad_medida', 'cantidad_avance', 'peso_unitario', 'materia_prima', 'cantidad_mprima', 'unidad_medida_mprima', 'observacion_ot', 'empresa', 'multa', 'ruta_ot', 'dias_atrasos'
        ]

    def get_dias_atrasos(self, obj):
        now = timezone.now().date()
        if obj.fecha_termino:
            lateness = (now - obj.fecha_termino).days
            return lateness
        return None
    
    def get_descripcion_producto_ot_instance(self, obj):
        try:
            Producto = apps.get_model('Product', 'Producto')
            Pieza = apps.get_model('Product', 'Pieza')

            products_serializers = import_module('Product.serializers')
            ProductoSerializer = getattr(products_serializers, 'ProductoSerializer', None)
            PiezaSerializer = getattr(products_serializers, 'PiezaSerializer', None)

            codigo_producto_salida = obj.codigo_producto_salida

            if ProductoSerializer:
                try:
                    producto = Producto.objects.get(codigo_producto=codigo_producto_salida)
                    return ProductoSerializer(producto).data
                except Producto.DoesNotExist:
                    pass

            if PiezaSerializer:
                try:
                    pieza = Pieza.objects.get(codigo_pieza=codigo_producto_salida)
                    return PiezaSerializer(pieza).data
                except Pieza.DoesNotExist:
                    pass
        
        except Exception as e:
            print(f"Error in get_descripcion_ot_instance: {str(e)}")
            return None
        
        return None
    
    def get_fecha_emision_formated(self, obj):
        if obj.fecha_emision:
            return obj.fecha_emision.strftime('%d-%m-%Y')
        return None
    
    def get_fecha_proc_formated(self, obj):
        if obj.fecha_proc:
            return obj.fecha_proc.strftime('%d-%m-%Y')
        return None
    
    def get_fecha_termino_formated(self, obj):
        if obj.fecha_termino:
            return obj.fecha_termino.strftime('%d-%m-%Y')
        return None
    
    def update(self, instance, validated_data):
        ruta_ot_data = validated_data.pop('ruta_ot')
        ruta_ot_serializer = self.fields['ruta_ot']
        ruta_ot_instance = instance.ruta_ot

        if ruta_ot_serializer and ruta_ot_instance:
            ruta_ot_serializer.update(ruta_ot_instance, ruta_ot_data)

        instance.save()
        return instance
    
class ProgramaOrdenTrabajoSerializer(serializers.ModelSerializer):
    orden_trabajo_codigo_ot = serializers.CharField(source='orden_trabajo.codigo_ot')
    orden_trabajo_descripcion_producto_ot = serializers.CharField(source='orden_trabajo.descripcion_producto_ot')

    class Meta:
        model = ProgramaOrdenTrabajo
        fields = ['id', 'programa', 'orden_trabajo', 'prioridad', 'orden_trabajo_codigo_ot', 'orden_trabajo_descripcion_producto_ot']

class ProgramaProduccionSerializer(serializers.ModelSerializer):
    ordenes_trabajo = serializers.SerializerMethodField()

    class Meta:
        model = ProgramaProduccion
        fields = ['id', 'nombre', 'fecha_inicio', 'fecha_fin', 'created_at', 'updated_at', 'ordenes_trabajo']

    def get_ordenes_trabajo(self, obj):
        ordenes_trabajo = ProgramaOrdenTrabajo.objects.filter(programa=obj).select_related('orden_trabajo').order_by('prioridad')
        
        return ProgramaOrdenTrabajoSerializer(ordenes_trabajo, many=True).data
    

# Agregar después de ProgramaProduccionSerializer

class TareaFragmentadaSerializer(serializers.ModelSerializer):
    tarea_original = ItemRutaSerializer(read_only=True)
    operador_id = serializers.IntegerField(source='operador.id', read_only=True)
    orden_trabajo = serializers.SerializerMethodField()

    class Meta:
        model = TareaFragmentada
        fields = [
            'id', 'programa', 'fecha', 'tarea_original', 'operador_id',
            'cantidad_asignada', 'cantidad_pendiente_anterior',
            'cantidad_total_dia', 'cantidad_completada', 'cantidad_pendiente',
            'kilos_fabricados', 'estado', 'porcentaje_cumplimiento',
            'es_continuacion', 'tarea_padre', 'observaciones',
            'created_at', 'updated_at', 'orden_trabajo',
            'fecha_planificada_inicio', 'fecha_planificada_fin'
        ]

    def get_orden_trabajo(self, obj):
        """Obtiene la información de la orden de trabajo asociada a esta tarea"""
        try:
            if obj.tarea_original and obj.tarea_original.ruta and obj.tarea_original.ruta.orden_trabajo:
                ot = obj.tarea_original.ruta.orden_trabajo
                return {
                    'id': ot.id,
                    'codigo': ot.codigo_ot,
                    'descripcion': ot.descripcion_producto_ot
                }
        except AttributeError:
            #Maneja las excepciones si algún objeto en la cadena es None
            pass
        return None

class EjecucionTareaSerializer(serializers.ModelSerializer):
    operador_id = serializers.IntegerField(source='operador.id', read_only=True)
    
    class Meta:
        model = EjecucionTarea
        fields = [
            'id', 'tarea', 'fecha_hora_inicio', 'fecha_hora_fin',
            'cantidad_producida', 'operador_id', 'estado', 'observaciones',
            'created_at', 'updated_at'
        ]