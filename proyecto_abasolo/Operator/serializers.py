from rest_framework import serializers
from .models import Operador, OperadorMaquina, AsignacionOperador
from JobManagement.serializers import MaquinaSerializer, ItemRutaSerializer, ProgramaProduccionSerializer, EmpresaOTSerializer
from JobManagement.models import ItemRuta, ProgramaProduccion

class OperadorMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperadorMaquina
        fields = ['id', 'operador', 'maquina', 'fecha_habilitacion', 'activo']

class OperadorSerializer(serializers.ModelSerializer):
    empresa = EmpresaOTSerializer(read_only=True)
    maquinas_habilitadas = MaquinaSerializer(many=True, read_only=True)

    class Meta:
        model = Operador
        fields = ['id', 'nombre', 'rut', 'activo', 'empresa', 'maquinas_habilitadas', 'created_at', 'updated_at']

    def create(self, validated_data):
        empresa_id = self.initial_data.get('empresa')
        maquinas_ids = self.initial_data.get('maquinas_habilitadas', [])

        operador = Operador.objects.create(
            nombre=validated_data.get('nombre'),
            rut=validated_data.get('rut'),
            empresa_id=empresa_id,
            activo=validated_data.get('activo', True)
        )

        #Asignar máquinas si se proporcionaron
        if maquinas_ids:
            #Convertir a enteros si vienen como strins
            maquinas_ids = [int(id) for id in maquinas_ids]

            #Crear las habilitaciones de máquinas
            for maquina_id in maquinas_ids:
                OperadorMaquina.objects.create(
                    operador=operador,
                    maquina_id=maquina_id
                )
            
            #Log para depuración
            print(f'Operador nuevo {operador.id}: Máquinas asignadas: {maquinas_ids}')
        
        return operador

    def update(self, instance, validated_data):
        empresa_id = self.initial_data.get('empresa')
        maquinas_ids = self.initial_data.get('maquinas_habilitadas')

        instance.nombre = validated_data.get('nombre', instance.nombre)
        instance.rut = validated_data.get('rut', instance.rut)
        instance.activo = validated_data.get('activo', instance.activo)

        if empresa_id:
            instance.empresa_id = empresa_id
        
        instance.save()

        if maquinas_ids is not None:
            #Convertir a enteros si vienen como strings
            maquinas_ids = [int(id) for id in maquinas_ids]

            #Actualizar habilitaciones de maquinas
            actual_maquinas = set(instance.maquinas_habilitadas.values_list('id', flat=True))
            nueva_maquinas = set(maquinas_ids)

            #Maquinas a agregar (están en la nueva lista pero no en la actual)
            maquinas_a_agregar = nueva_maquinas - actual_maquinas

            #Maquinas a eliminar (están en la actual pero no en la nueva)
            maquinas_a_eliminar = actual_maquinas - nueva_maquinas

            #Eliminar relaciones que ya no existen
            OperadorMaquina.objects.filter(
                operador=instance,
                maquina_id__in=maquinas_a_eliminar
            ).delete()


            #Agregar nuevas relaciones
            for maquina_id in nueva_maquinas - actual_maquinas:
                OperadorMaquina.objects.create(
                    operador=instance,
                    maquina_id=maquina_id
                )

            # Log para depuración
            print(f"Operador {instance.id}: Máquinas actuales: {actual_maquinas}")
            print(f"Operador {instance.id}: Máquinas nuevas: {nueva_maquinas}")
            print(f"Operador {instance.id}: Máquinas a agregar: {maquinas_a_agregar}")
            print(f"Operador {instance.id}: Máquinas a eliminar: {maquinas_a_eliminar}")    
        
        return instance
    
class AsignacionOperadorSerializer(serializers.ModelSerializer):
    operador = OperadorSerializer(read_only=True)
    item_ruta = ItemRutaSerializer(read_only=True)
    programa = ProgramaProduccionSerializer(read_only=True)
    asignado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = AsignacionOperador
        fields = [
            'id', 'operador', 'item_ruta', 'programa', 
            'fecha_inicio', 'fecha_fin', 'created_at',
            'asignado_por', 'asignado_por_nombre', 'fecha_asignacion'
        ]

    def get_asignado_por_nombre(self, obj):
        if obj.asignado_por:
            return f'{obj.asignado_por.first_name} {obj.asignado_por.last_name}'.strip() or obj.asignado_por.username
    def validate(self, data):
        """Validaciones adicionales para la asignación"""
        operador = self.context['request'].data.get('operador')
        item_ruta =self.context['request'].data.get('item_ruta')
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')

        if not all([operador, item_ruta, fecha_inicio, fecha_fin]):
            raise serializers.ValidationError('Faltan campos requeridos')
        
        #Validar que el operador puede operar la máquina
        if not Operador.objects.get(id=operador).puede_operar_maquina(ItemRuta.objects.get(id=item_ruta).maquina):
            raise serializers.ValidationError('El operador no está habilitado para esta máquina')
        
        #Validar superposicion de horarios
        if AsignacionOperador.objects.filter(
            operador_id=operador,
            fecha_inicio__lt=fecha_fin,
            fecha_fin__gt=fecha_inicio
        ).exists():
            raise serializers.ValidationError('El operador ya tiene una asignación en este horario')
        
        return data