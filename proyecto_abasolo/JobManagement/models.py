from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from Client.models import Cliente
from Product.models import Producto, Pieza, MateriaPrima, MeasurementUnit
from datetime import datetime, time, timedelta
import uuid
from django.conf import settings

# Create your models here.


class Maquina(models.Model):
    codigo_maquina = models.CharField(max_length=10, null=False, blank=False, unique=False)
    descripcion = models.CharField(max_length=100, null=False, blank=False)
    sigla = models.CharField(max_length=10, null=False, blank=False, default='')
    carga = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    golpes = models.IntegerField(default=0)
    empresa = models.ForeignKey('EmpresaOT', on_delete=models.CASCADE, null=True)

    class Meta:
        unique_together = ('empresa', 'codigo_maquina')

    def __str__(self):
        return f'{self.codigo_maquina} - {self.descripcion}'
    
class Proceso(models.Model):
    codigo_proceso = models.CharField(max_length=10, null=False, blank=False, unique=False)
    sigla = models.CharField(max_length=10, null=True, blank=True)
    descripcion = models.CharField(max_length=100, null=False, blank=False)
    carga = models.DecimalField(max_digits=10, decimal_places=4, default=0.0000)
    empresa = models.ForeignKey('EmpresaOT', on_delete=models.CASCADE, null=True, blank=True)
    # Añadir esta relación
    tipos_maquina_compatibles = models.ManyToManyField('Machine.TipoMaquina', related_name='procesos_compatibles')

    class Meta:
        unique_together = ('empresa', 'codigo_proceso')

    def __str__(self):
        return f'{self.codigo_proceso} - {self.descripcion}'

    def get_maquinas_compatibles(self):
        """Obtiene todas las máquinas compatibles con este proceso"""
        from Machine.models import EstadoMaquina
        return Maquina.objects.filter(
            estado__tipos_maquina__in=self.tipos_maquina_compatibles.all(),
            estado__disponible=True
        ).distinct()
    
class Ruta(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='rutas')
    nro_etapa = models.PositiveIntegerField()
    proceso = models.ForeignKey(Proceso, on_delete=models.CASCADE)
    maquina = models.ForeignKey(Maquina, on_delete=models.CASCADE)
    estandar = models.IntegerField(default=0)

    class Meta:
        unique_together = ('producto', 'nro_etapa', 'proceso', 'maquina')

    def __str__(self):
        return f'{self.producto.codigo_producto} - Etapa {self.nro_etapa} - {self.proceso.codigo_proceso}'
    
class RutaPieza(models.Model):
    pieza = models.ForeignKey(Pieza, on_delete=models.CASCADE, related_name='rutas')
    nro_etapa = models.PositiveIntegerField()
    proceso = models.ForeignKey(Proceso, on_delete=models.CASCADE)
    maquina = models.ForeignKey(Maquina, on_delete=models.CASCADE)
    estandar = models.IntegerField(default=0)

    class Meta:
        unique_together = ('pieza', 'nro_etapa', 'proceso', 'maquina')

    def __str__(self):
        return f'{self.pieza.codigo_pieza} - Etapa {self.nro_etapa} - {self.proceso.codigo_proceso}'
    
class TipoOT(models.Model):
    codigo_tipo_ot = models.CharField(max_length=2, unique=True)
    descripcion = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f'{self.codigo_tipo_ot}: {self.descripcion}' or 'Unnamed'
    
class SituacionOT(models.Model):
    codigo_situacion_ot = models.CharField(max_length=2, unique=True)
    descripcion = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f'{self.codigo_situacion_ot}: {self.descripcion}' or 'Unnamed'
    
class EmpresaOT(models.Model):
    nombre = models.CharField(max_length=50, blank=False, null=False)
    apodo = models.CharField(max_length=50, blank=False, null=False, unique=True)
    codigo_empresa = models.CharField(max_length=50, blank=False, null=False, unique=True)

    def __str__(self):
        return f'{self.apodo} - {self.codigo_empresa}'
    
class ItemRuta(models.Model):
    item = models.PositiveIntegerField()
    maquina = models.ForeignKey(Maquina, on_delete=models.CASCADE)
    proceso = models.ForeignKey(Proceso, on_delete=models.CASCADE)
    estandar = models.IntegerField(default=0)
    cantidad_pedido = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    cantidad_terminado_proceso = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    cantidad_perdida_proceso = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    terminado_sin_actualizar = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    ruta = models.ForeignKey('RutaOT', on_delete=models.CASCADE, related_name='items')

    class Meta:
        unique_together = ('ruta', 'item', 'maquina', 'proceso')

    def __str__(self):
        return f'Item {self.item} de Ruta de Orden: {self.ruta.orden_trabajo}'
    
class RutaOT(models.Model):
    
    orden_trabajo = models.OneToOneField('OrdenTrabajo', on_delete=models.CASCADE, related_name='ruta_ot', null=True, blank=True)

    def __str__(self):
        if hasattr(self, 'orden_trabajo') and self.orden_trabajo:
            return f'Ruta asociada a la Orden de Trabajo: {self.orden_trabajo.codigo_ot}'
        return 'Ruta sin Orden de Trabajo asociada'
    
class OrdenTrabajo(models.Model):

    codigo_ot = models.IntegerField(unique=True)
    tipo_ot = models.ForeignKey(TipoOT, on_delete=models.PROTECT)
    situacion_ot = models.ForeignKey(SituacionOT, on_delete=models.PROTECT)
    fecha_emision = models.DateField(null=True, blank=True)
    fecha_proc = models.DateField(null=True, blank=True)
    fecha_termino = models.DateField(null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, null=True, blank=True)
    nro_nota_venta_ot = models.CharField(max_length=12, null=True, blank=True)
    item_nota_venta = models.IntegerField()
    referencia_nota_venta = models.IntegerField(null=True, blank=True)
    codigo_producto_inicial = models.CharField(max_length=12, null=True, blank=True)
    codigo_producto_salida = models.CharField(max_length=12, null=True, blank=True)
    descripcion_producto_ot = models.CharField(max_length=255, null=True, blank=True)
    cantidad = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    unidad_medida = models.ForeignKey(MeasurementUnit, on_delete=models.PROTECT, null=True, blank=True)
    cantidad_avance = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    peso_unitario = models.DecimalField(max_digits=19, decimal_places=5, default=0.00000)
    materia_prima = models.ForeignKey(MateriaPrima, on_delete=models.PROTECT, null=True, blank=True)
    cantidad_mprima = models.DecimalField(max_digits=14, decimal_places=2, default=0.00000)
    unidad_medida_mprima = models.ForeignKey(MeasurementUnit, related_name='unidad_of_medida_materia_prima', on_delete=models.PROTECT, null=True, blank=True) #column 19
    observacion_ot = models.CharField(max_length=150, null=True, blank=True)
    empresa = models.ForeignKey(EmpresaOT, on_delete=models.PROTECT, null=True, blank=True)
    multa = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.codigo_ot}'

    def update_item_rutas(self, items_data):
        print("Items data:", items_data)
        # Si recibes el listado de máquinas en el frontend, sería ideal cargar estas previamente
        maquinas_dict = {maquina.id: maquina for maquina in Maquina.objects.all()}
        
        for item_data in items_data:
            try:
                # Intenta obtener el ítem de la ruta correspondiente
                item = self.ruta_ot.items.get(item=item_data['item'])
                print("Item instance:", item)

                # Validar y actualizar la máquina si se proporciona
                if 'maquina' in item_data:
                    maquina = maquinas_dict.get(item_data['maquina'])
                    if maquina:
                        item.maquina = maquina
                    else:
                        print(f"Máquina con ID {item_data['maquina']} no encontrada.")
                
                # Actualizar el estándar de producción si se proporciona
                if 'estandar' in item_data:
                    item.estandar = item_data['estandar']
                
                item.save()  # Guardar los cambios en el ítem

            except ItemRuta.DoesNotExist:
                print(f"Ítem con el número {item_data['item']} no encontrado en la ruta.")
            except Exception as e:
                print(f"Error al actualizar ItemRuta: {e}")

class ProgramaProduccion(models.Model):
    nombre = models.CharField(max_length=100, unique=True, blank=True)
    #Fecha de inicio será determinada por la fecha de la ot en primera posición, y la fecha de fin se determinará por el cálculo de cuando termine el último proceso de la ultima ot
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = "Programa Producción"
        verbose_name_plural = "Programas Producción"

    def __str__(self):
        return self.nombre
    
    def save(self, *args, **kwargs):
        if not self.nombre:
            timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
            random_string = uuid.uuid4().hex[:6]
            self.nombre = f"Programa_{timestamp}_{random_string}"

        #Si es un programa nuevo y no tiene fecha_fin, usamos fecha_inicio + 30 dias como valor predeterminado
        if not self.pk and not self.fecha_fin:
            self.fecha_fin = self.fecha_inicio + timezone.timedelta(days=30)

        #Guardamos el objecto con los valores iniciales
        super().save(*args, **kwargs)

        #Si ya tiene OTs asociadas, calculamos la fecha_fin (para actualizaciones)
        if self.pk and ProgramaOrdenTrabajo.objects.filter(programa=self).exists():
            self.actualizar_fecha_fin()

    def actualizar_fecha_fin(self):
        """Método legacy manenido para compatibilidad"""
        pass
            
    @property
    def dias_programa(self):
        return (self.fecha_fin - self.fecha_inicio).days + 1

    #Crear métodos para disponibilidad de operadores y maquinas
    #Disponibilidad horaria más adelante

class ProgramaOrdenTrabajo(models.Model):
    programa =  models.ForeignKey(ProgramaProduccion, on_delete=models.CASCADE)
    orden_trabajo = models.ForeignKey(OrdenTrabajo, on_delete=models.CASCADE)
    prioridad = models.PositiveIntegerField()

    class Meta:
        unique_together = ('programa', 'orden_trabajo')

    def save(self, *args, **kwargs):
        if not self.id:
            if self.orden_trabajo.situacion_ot.codigo_situacion_ot not in ['P', 'S']:
                raise ValidationError("La OT debe estar en situación 'Pendiente' o 'Sin imprimir'")
        super(ProgramaOrdenTrabajo, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.programa.nombre} - {self.orden_trabajo.codigo_ot} - Prioridad: {self.prioridad}'

class IntervaloDisponibilidad(models.Model):
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    

    TIPO_CHOICES = [
        ('MAQUINA', 'Maquina'),
        ('OPERADOR', 'Operador')
    ]
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)

    class Meta:
        abstract = True

    def clean(self):
        if self.fecha_inicio > self.fecha_fin:
            raise ValidationError("La fecha de inicio debe ser anterior a la fecha de fin")

        # Validar que esté dentro del horario (7:45 - 17:45)
        hora_laboral_inicio = time(7, 45)
        hora_laboral_fin = time(17, 45)

        #Verificar cada día del intervalo
        fecha_actual = self.fecha_inicio
        while fecha_actual <= self.fecha_fin:
            #Solo verificar días laborales(L-V)
            if fecha_actual.weekyday() < 5: #0-4 son Lunes a Viernes
                hora_inicio = fecha_actual.time()
                hora_fin = min(fecha_actual.replace(hour=17, minute=45).time(), self.fecha_fin.time() if fecha_actual.date() == self.fecha_fin.date() else hora_laboral_fin)

                if hora_inicio < hora_laboral_inicio or hora_fin > hora_laboral_fin:
                    raise ValidationError(f"El intervalo del día {fecha_actual.date()} debe estar dentro del horario laboral (7:45 - 17:45)")
                
            fecha_actual += timedelta(days=1)

    def tiene_conflicto(self, fecha_inicio, fecha_fin):
        """Verfifica si hay conflicto con otro intervalo de tiempo"""
        return not(fecha_fin <= self.fecha_inicio or fecha_inicio >= self.fecha_fin)
    
class IntervaloMaquina(IntervaloDisponibilidad):
    maquina = models.ForeignKey('Maquina', on_delete=models.CASCADE)
    motivo = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Intervalo {self.maquina.codigo_maquina} - {self.fecha_inicio.strftime('%Y-%m-%d %H:%M')} a {self.fecha_fin.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['maquina', 'fecha_inicio'],
                name='unique_maquina_intervalo'
            )
        ]

    @classmethod
    def validar_disponibilidad(cls, maquina, fecha_inicio, fecha_fin):
        """
        Verifica si una máquina está disponible en un intervalo de tiempo específico
        Retorna bool, str : (está_disponible, mensaje)
        """
        intervalos = cls.objects.filter(
            maquina=maquina,
            fecha_fin__gte=fecha_inicio,
            fecha_inicio__lte=fecha_fin
        )

        for intervalo in intervalos:
            if intervalo.tiene_conflicto(fecha_inicio, fecha_fin):
                return False, f"Maquina no disponible del {intervalo.fecha_inicio.strf.time('%Y-%m-%d %H:%M')} al {intervalo.fecha_fin.strftime('%Y-%m-%d H:%M')}"
            
        return True, "Disponible"
    

class IntervaloOperador(IntervaloDisponibilidad):
    operador = models.ForeignKey('Operator.Operador', on_delete=models.CASCADE)
    motivo = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Intervalo {self.operador.nombre} - ({self.fecha_inicio.strftime('%Y-%m-%d %H:%M')} a {self.hora_fin.strftime('%Y-%m-%d %H:%M')})"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['operador', 'fecha_inicio'],
                name='unique_operador_intervalo'
            )
        ]

    @classmethod
    def validar_disponibilidad(cls, operador, fecha, fecha_inicio, fecha_fin):
        """
        Verifica si un operador está disponible en un intervalo de tiempo específico
        Retorna (bool, str): (está_disponible, mensaje)
        """
        intervalos = cls.objects.filter(
            operador=operador,
            fecha_fin__gte=fecha_inicio,
            fecha_inicio__lte=fecha_fin
        )

        for intervalo in intervalos:
            if intervalo.tiene_conflicto(fecha, fecha_inicio, fecha_fin):
                return False, f"Operador no disponible de {intervalo.fecha_inicio.strftime('%Y-%m-%d %H:%M')} a {intervalo.fecha_fin.strftime('%Y-%m-%d %H:%M')}"
            
        return True, "Disponible"

    @classmethod
    def encontrar_siguiente_disponibilidad(cls, operador, fecha_inicio, duracion_horas):
        """
        Encuentra el siguiente intervalo disponible para un operador
        """

        #Obtener todos los intervalos futuros del operador
        intervalos = cls.objects.filter(
            operador=operador,
            fecha_fin__gte=fecha_inicio
        ).order_by('fecha_inicio')

        fecha_propuesta = fecha_inicio
        duracion = timedelta(hours=duracion_horas)

        for intervalo in intervalos:
            fecha_fin_propuesta = fecha_propuesta + duracion

            #Si no hay conflicto, hemos encontrado un espacio
            if not intervalo.tiene_conflicto(fecha_propuesta, fecha_fin_propuesta):
                return fecha_propuesta

            #Si hay conflicto, intentar después del intervalo actual
            fecha_propuesta = intervalo.fecha_fin

        #Si no encontramos conflictos o no hay más intervalos, usar la última fecha propuesta
        return fecha_propuesta

class ReporteDiario(models.Model):
    programa = models.ForeignKey(ProgramaProduccion, on_delete=models.CASCADE)
    item_ruta = models.ForeignKey(ItemRuta, on_delete=models.CASCADE)
    fecha = models.DateField()
    estado = models.CharField(max_length=20, choices=[
        ('Pendiente', 'Pendiente'),
        ('En Proceso', 'En Proceso'),
        ('Terminado', 'Terminado'),
        ('Detenido', 'Detenido')
    ])
    kilos_fabricados = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unidades_fabricadas = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    observaciones = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    fragmento_tarea = models.ForeignKey('TareaFragmentada', on_delete=models.SET_NULL, null=True, blank=True, related_name='reportes')

    class Meta:
        unique_together = ['programa', 'item_ruta', 'fecha']

class TareaFragmentada(models.Model):
    tarea_original = models.ForeignKey('ItemRuta', on_delete=models.CASCADE, related_name='fragmentos')
    tarea_padre = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='continuaciones')
    fecha = models.DateField()
    porcentaje_completado= models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cantidad_asignada = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad_completada = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    es_continuacion = models.BooleanField(default=False)
    nivel_fragmentacion = models.IntegerField(default=0)  #0 para tarea original, 1 para continuaciones
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['fecha', 'nivel_fragmentacion']

    def __str__(self):
        return f"Fragmento {self.nivel_fragmentacion} de {self.tarea_original} - {self.fecha}"
    


class ReporteSupervisor(models.Model):
    """Modelo para gestionar el reporte global de un supervisor para un programa"""
    programa = models.OneToOneField(
        ProgramaProduccion,
        on_delete=models.CASCADE,
        related_name='reporte_supervisor'
    )
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='programas_supervisados'
    )
    estado = models.CharField(
        max_length=20,
        choices=[
            ('ACTIVO', 'Activo'),
            ('FINALIZADO', 'Finalizado'),
            ('PAUSADO', 'Pausado')
        ],
        default='ACTIVO'
    )
    notas = models.TextField(blank=True, null=True)
    porcentaje_completado = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    #Campos para el bloqueo de edición
    editor_actual = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reportes_editando'
    )
    bloqueo_hasta = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Reporte de Supervisor'
        verbose_name_plural = 'Reportes de Supervisor'

    def __str__(self):
        return f'Reporte Supervisor: {self.programa.nombre}'
    
    def calcular_porcentaje_completado(self):
        """Calcular porcentaje de tareas completadas"""
        reportes = ReporteDiario.objects.filter(programa=self.programa)
        if not reportes.exists():
            return 0
        
        total_tareas = reportes.count()
        tareas_completadas = reportes.filter(estado='Terminado').count()

        porcentaje = (tareas_completadas / total_tareas) * 100 if total_tareas > 0 else 0
        self.porcentaje_completado = round(porcentaje, 2)
        self.save(update_fields=['porcentaje_completado'])
        return self.porcentaje_completado
    

    #Métodos para gestonar el bloqueo
    def esta_bloqueado(self):
        return (self.editor_actual is not None and
                self.bloqueo_hasta is not None and
                self.bloqueo_hasta > timezone.now())
    
    def puede_editar(self, usuario):
        if not self.esta_bloqueado():
            return True
        return self.editor_actual == usuario
    
    def adquirir_bloqueo(self, usuario, duracion_minutos=30):
        if self.esta_bloqueado() and self.editor_actual != usuario:
            return False
        self.editor_actual = usuario
        self.bloqueo_hasta = timezone.now() + timedelta(minutes=duracion_minutos)
        self.save(update_fields=['editor_actual', 'bloqueo_hasta'])
        return True
    
    def liberar_bloqueo(self, usuario):
        if self.editor_actual == usuario:
            self.editor_actual = None
            self.bloqueo_hasta = None
            self.save(update_fields=['editor_actual', 'bloqueo_hasta'])
            return True
        return False