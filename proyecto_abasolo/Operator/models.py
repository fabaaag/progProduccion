from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from django.conf import settings

from JobManagement.models import ItemRuta

class Operador(models.Model):
    """Representa un operador que puede trabajar en diferentes máquinas
        Mantiene información básica y sus habilitaciones.
    """
    nombre = models.CharField(max_length=100)
    rut = models.CharField(max_length=12, unique=True)
    activo = models.BooleanField(default=True)
    empresa = models.ForeignKey('JobManagement.EmpresaOT', on_delete=models.PROTECT)
    maquinas_habilitadas = models.ManyToManyField('JobManagement.Maquina', through='OperadorMaquina', related_name='operadores_habilitados')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} ({self.rut})"
    
    def puede_operar_maquina(self, maquina):
        """Verifica si el operador está habilitado para operar una máquina específica"""
        return self.maquinas_habilitadas.filter(id=maquina.id).exists()

class OperadorMaquina(models.Model):
    """Relaciona operadores con máquinas y mantiene un registro de habiliaciones.
    Incluye fecha de habilitacion y estado activo.
    """
    operador = models.ForeignKey(Operador, on_delete=models.CASCADE)
    maquina = models.ForeignKey('JobManagement.Maquina', on_delete=models.CASCADE)
    fecha_habilitacion = models.DateField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ['operador', 'maquina']
        verbose_name="Habilitación de máquina"
        verbose_name_plural = "Habilitaciónes de máquinas"

    def __str__(self):
        return f'{self.operador.nombre} - {self.maquina.codigo_maquina}'
    
class AsignacionOperador(models.Model):
    """Registra la asignacion de un operador a un ItemRuta específico dentro de un programa
    Incluye validaciones de tiempo y permisos
    """
    operador = models.ForeignKey(Operador, on_delete=models.CASCADE, related_name='asignaciones')
    item_ruta = models.ForeignKey('JobManagement.ItemRuta', on_delete=models.CASCADE)
    programa = models.ForeignKey('JobManagement.ProgramaProduccion', on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()

    #Nuevos campos para rastrear quién realizó la asignación
    asignado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='asignaciones_realizadas')
    fecha_asignacion = models.DateTimeField(default=timezone.now)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(fecha_fin__gt=models.F('fecha_inicio')),
                name='check_fecha_fin_mayor_inicio'
            )
        ]
    
    def clean(self):
        if not hasattr(self, 'operador_id') or not hasattr(self, 'item_ruta_id'):
            return
        try:
            # Validar que las fechas sean válidas
            if self.fecha_inicio >= self.fecha_fin:
                raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio')
            
            # Validar que el operador esté habilitado para la máquina
            if not self.operador.puede_operar_maquina(self.item_ruta.maquina):
                raise ValidationError('El operador no está habilitado para esta máquina')
                
            # Buscar superposiciones y ajustar fechas si es necesario
            self.ajustar_fechas_por_conflictos()

        except ValidationError as e:
            raise e
        except Exception as e:
            raise ValidationError(f'Error de validación: {str(e)}')

    def ajustar_fechas_por_conflictos(self):
        """Ajusta las fechas de la asignación en caso de conflictos"""
        duracion = self.fecha_fin - self.fecha_inicio
        fecha_inicio_propuesta = self.fecha_inicio
        fecha_fin_propuesta = self.fecha_fin
        
        while True:
            # Verificar superposición con otras asignaciones del operador
            superposicion_operador = AsignacionOperador.objects.filter(
                operador=self.operador,
                fecha_inicio__lt=fecha_fin_propuesta,
                fecha_fin__gt=fecha_inicio_propuesta
            ).exclude(id=self.id).order_by('fecha_inicio')

            # Verificar superposición con otras asignaciones de la máquina
            superposicion_maquina = AsignacionOperador.objects.filter(
                item_ruta__maquina=self.item_ruta.maquina,
                fecha_inicio__lt=fecha_fin_propuesta,
                fecha_fin__gt=fecha_inicio_propuesta
            ).exclude(id=self.id).order_by('fecha_inicio')

            if not superposicion_operador.exists() and not superposicion_maquina.exists():
                # No hay conflictos, usar estas fechas
                self.fecha_inicio = fecha_inicio_propuesta
                self.fecha_fin = fecha_fin_propuesta
                break

            # Encontrar la última fecha de fin entre todas las superposiciones
            ultima_fecha_fin = None
            if superposicion_operador.exists():
                ultima_fecha_fin = superposicion_operador.last().fecha_fin

            if superposicion_maquina.exists():
                fecha_fin_maquina = superposicion_maquina.last().fecha_fin
                if ultima_fecha_fin is None or fecha_fin_maquina > ultima_fecha_fin:
                    ultima_fecha_fin = fecha_fin_maquina

            # Ajustar las fechas para el siguiente intervalo disponible
            fecha_inicio_propuesta = ultima_fecha_fin
            fecha_fin_propuesta = fecha_inicio_propuesta + duracion

            # Ajustar por horario laboral (8:00 - 18:00)
            hora_inicio = fecha_inicio_propuesta.hour
            if hora_inicio < 8:
                fecha_inicio_propuesta = fecha_inicio_propuesta.replace(hour=8, minute=0)
                fecha_fin_propuesta = fecha_inicio_propuesta + duracion
            elif hora_inicio >= 18:
                # Mover al siguiente día laboral
                fecha_inicio_propuesta = (fecha_inicio_propuesta + timedelta(days=1)).replace(hour=8, minute=0)
                fecha_fin_propuesta = fecha_inicio_propuesta + duracion

            # Si la fecha propuesta es después de la hora de almuerzo (13:00-14:00)
            if 13 <= fecha_inicio_propuesta.hour < 14:
                fecha_inicio_propuesta = fecha_inicio_propuesta.replace(hour=14, minute=0)
                fecha_fin_propuesta = fecha_inicio_propuesta + duracion

    @staticmethod
    def encontrar_siguiente_horario_disponible(operador, maquina, fecha_inicio, duracion_horas):
        """Encuentra el siguiente horario disponible para una asignación"""
        fecha_propuesta = fecha_inicio
        duracion = timedelta(hours=duracion_horas)
        
        while True:
            fecha_fin_propuesta = fecha_propuesta + duracion
            
            # Verificar disponibilidad del operador y la máquina
            superposicion = AsignacionOperador.objects.filter(
            Q(operador=operador, fecha_inicio__lt=fecha_fin_propuesta, fecha_fin__gt=fecha_propuesta) |
            Q(item_ruta__maquina=maquina, fecha_inicio__lt=fecha_fin_propuesta, fecha_fin__gt=fecha_propuesta)
            ).order_by('fecha_fin')

            if not superposicion.exists():
                # Ajustar por horario laboral
                hora = fecha_propuesta.hour
                if hora < 8:
                    fecha_propuesta = fecha_propuesta.replace(hour=8, minute=0)
                elif hora >= 18:
                    fecha_propuesta = (fecha_propuesta + timedelta(days=1)).replace(hour=8, minute=0)
                elif 13 <= hora < 14:
                    fecha_propuesta = fecha_propuesta.replace(hour=14, minute=0)
                else:
                    return fecha_propuesta
            else:
                fecha_propuesta = superposicion.last().fecha_fin

            # Verificar si la nueva fecha propuesta respeta el horario laboral
            if fecha_propuesta.hour >= 18:
                fecha_propuesta = (fecha_propuesta + timedelta(days=1)).replace(hour=8, minute=0)

    def recalcular_asignaciones_posteriores(self):
        """Recalcula las fechas de las asignaciones posteriores cuando se modifica una asignacion"""
        # Obtener todas las asignaciones posteriores del mismo operador, ordenadas por prioridad de OT
        asignaciones_posteriores = AsignacionOperador.objects.filter(
            operador=self.operador,
            fecha_inicio__gt=self.fecha_inicio
        ).select_related(
            'item_ruta__orden_trabajo',
            'programa'
        ).order_by(
            'item_ruta__orden_trabajo__prioridad',
            'item_ruta__item'
        )

        fecha_anterior = self.fecha_fin
        for asignacion in asignaciones_posteriores:
            # Calcular la duración original de la asignacion
            duracion = asignacion.fecha_fin - asignacion.fecha_inicio
            
            # Encontrar el siguiente horario disponible
            nueva_fecha_inicio = self.encontrar_siguiente_horario_disponible(
                asignacion.operador,
                asignacion.item_ruta.maquina,
                fecha_anterior,
                duracion.total_seconds() / 3600
            )

            # Actualizar las fechas
            asignacion.fecha_inicio = nueva_fecha_inicio
            asignacion.fecha_fin = nueva_fecha_inicio + duracion
            asignacion.save()

            # Recalcular los procesos subsiguientes de la misma OT
            self.recalcular_procesos_subsiguientes(asignacion)

            fecha_anterior = asignacion.fecha_fin

    def recalcular_procesos_subsiguientes(self, asignacion):
        """Recalcula las fechas de los procesos que siguen después del proceso actual en la misma OT"""
        procesos_siguientes = ItemRuta.objects.filter(
            orden_trabajo=asignacion.item_ruta.orden_trabajo,
            item__gt=asignacion.item_ruta.item
        ).order_by('item')

        fecha_inicio = asignacion.fecha_fin
        for proceso in procesos_siguientes:
            # Buscar si el proceso tiene una asignación
            try:
                asig_proceso = AsignacionOperador.objects.get(
                    item_ruta=proceso,
                    programa=asignacion.programa
                )
                # Actualizar las fechas de la asignación
                asig_proceso.fecha_inicio = fecha_inicio
                asig_proceso.fecha_fin = fecha_inicio + (asig_proceso.fecha_fin - asig_proceso.fecha_inicio)
                asig_proceso.save()
                fecha_inicio = asig_proceso.fecha_fin
            except AsignacionOperador.DoesNotExist:
                continue

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        self.clean()
        super().save(*args, **kwargs)

        #Solo recalcular si es una nueva asignacion o si las fechas cambiaron
        if is_new or self.has_changed:
            self.recalcular_asignaciones_posteriores()

    def __str__(self):
        return f"{self.operador.nombre} - {self.item_ruta} ({self.fecha_inicio})"