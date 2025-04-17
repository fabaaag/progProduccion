import uuid
from django.contrib import admin
from django.utils import timezone
from django import forms

from .models import Maquina, Proceso, Ruta, RutaPieza, TipoOT, SituacionOT, OrdenTrabajo, EmpresaOT, RutaOT, ItemRuta, ProgramaOrdenTrabajo, ProgramaProduccion

from .forms import ProgramaOrdenTrabajoAdminForm
# Register your models here.

class MaquinaAdmin(admin.ModelAdmin):
    list_display = ('codigo_maquina', 'descripcion', 'sigla', 'carga', 'golpes', 'empresa')
    list_filter = ('empresa', 'sigla')
    search_fields = ('codigo_maquina', 'descripcion', 'sigla')

@admin.register(Proceso)
class ProcesoAdmin(admin.ModelAdmin):
    list_display = ('codigo_proceso', 'descripcion', 'carga', 'sigla', 'empresa')
    list_filter = ('empresa', 'sigla')
    search_fields = ('descripcion', 'sigla')

@admin.register(Ruta)
class RutaAdmin(admin.ModelAdmin):
    search_fields = ('producto__codigo_producto', 'proceso__codigo_proceso', 'maquina__codigo_maquina')
    list_display = ('producto', 'nro_etapa', 'proceso', 'maquina', 'estandar')
    list_filter = ('producto', 'nro_etapa', 'proceso', 'maquina')

@admin.register(RutaPieza)
class RutaPiezaAdmin(admin.ModelAdmin):
    list_display = ('pieza', 'nro_etapa', 'proceso', 'maquina', 'estandar')
    list_filter = ('pieza', 'nro_etapa', 'proceso', 'maquina')
    search_fields = ('pieza__codigo_pieza', 'proceso__codigo_proceso', 'maquina__codigo_maquina')

@admin.register(TipoOT)
class TipoOTAdmin(admin.ModelAdmin):
    list_display = ('codigo_tipo_ot', 'descripcion')
    search_fields = ('codigo_tipo_ot', 'descripcion')

@admin.register(SituacionOT)
class SituacionOTAdmin(admin.ModelAdmin):
    list_display = ('codigo_situacion_ot', 'descripcion')
    search_fields = ('codigo_situacion_ot', 'descripcion')

class RutaOTFormset(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class ItemRutaInline(admin.TabularInline):
    model = ItemRuta
    fields = ('item', 'maquina', 'proceso', 'estandar', 'cantidad_pedido', 'cantidad_terminado_proceso', 'cantidad_perdida_proceso', 'terminado_sin_actualizar')
    extra = 1

class OrdenTrabajoCodigoOTFilter(admin.SimpleListFilter):
    title = 'by codigo_ot'
    parameter_name = 'by codigo_ot'

    def lookups(self, request, model_admin):
        codigos = OrdenTrabajo.objects.order_by('codigo_ot').distinct('codigo_ot')
        return [(codigo.codigo_ot, codigo.codigo_ot) for codigo in codigos]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(ruta__orden_trabajo__codigo_ot=self.value())
        return queryset
    
class ItemRutaAdmin(admin.ModelAdmin):
    list_display = ('item', 'maquina', 'proceso', 'estandar', 'ruta')
    list_filter = (OrdenTrabajoCodigoOTFilter, )
    search_fields = ['ruta__orden_trabajo__codigo_ot']


    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('ruta__orden_trabajo').prefetch_related('ruta__orden_trabajo__codigo_ot')
    
class RutaOTAdmin(admin.ModelAdmin):
    inlines = [ItemRutaInline]
    list_display = ['orden_trabajo']
    search_fields = ['orden_trabajo__codigo_ot', 'orden_trabajo__descripcion_producto_ot']

    def __str__(self):
        return 'RutaOT Admin'
    
class RutaOTInline(admin.StackedInline):
    model = RutaOT
    fields = ('orden_trabajo', )
    readonly_fields = ('orden_trabajo', )
    can_delete = False
    max_num = 1
    min_num = 1
    inlines = [ItemRutaInline]

class OrdenTrabajoAdmin(admin.ModelAdmin):
    list_display = (
        'codigo_ot', 'tipo_ot', 'situacion_ot', 'fecha_emision', 'fecha_proc', 'fecha_termino', 'cliente', 'nro_nota_venta_ot', 'item_nota_venta', 'referencia_nota_venta', 'codigo_producto_inicial', 'codigo_producto_salida', 'descripcion_producto_ot', 'cantidad', 'unidad_medida', 'cantidad_avance', 'peso_unitario', 'materia_prima', 'cantidad_mprima', 'unidad_medida_mprima', 'observacion_ot', 'empresa', 'multa'
    )
    search_fields = (
        'codigo_ot', 'descripcion_producto_ot', 'cliente__nombre', 'ruta_ot__items__maquina__codigo_maquina', 'ruta_ot__items__proceso__codigo_proceso'
    )
    list_filter = (
        'tipo_ot', 'situacion_ot', 'fecha_emision', 'empresa', 'multa'
    )
    date_hierarchy = 'fecha_emision'
    ordering = ('-fecha_termino',)
    inlines = [RutaOTInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

class ProgramaOrdenTrabajoInline(admin.TabularInline):
    model = ProgramaOrdenTrabajo
    form = ProgramaOrdenTrabajoAdminForm
    extra = 1

class ProgramaProduccionAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'fecha_inicio', 'fecha_fin']
    inlines = [ProgramaOrdenTrabajoInline]

    def save_model(self, request, obj, form, change):
        if not obj.nombre:
            obj.nombre = f"Programa_{timezone.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
        super().save_model(request, obj, form, change)


@admin.register(EmpresaOT)
class EmpresaOTAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apodo', 'codigo_empresa')
    search_fields = ('nombre', 'nombre_fantasia', 'codigo_empresa')


admin.site.register(Maquina, MaquinaAdmin)
admin.site.register(RutaOT, RutaOTAdmin)
admin.site.register(ItemRuta)
admin.site.register(ProgramaProduccion, ProgramaProduccionAdmin)
admin.site.register(OrdenTrabajo, OrdenTrabajoAdmin)
