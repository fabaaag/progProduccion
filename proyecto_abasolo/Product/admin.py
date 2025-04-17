from django.contrib import admin
from .models import *
from .forms import ProductoForm

# Register your models here.


class FamiliaProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo_familia', 'descripcion')
    search_fields = ('codigo_familia', 'descripcion')

class SubfamiliaProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo_subfamilia', 'familia_producto', 'descripcion')
    list_filter = ('familia_producto',)
    search_fields = ('codigo_subfamilia', ' familia_producto__codigo_familia', 'familia_producto__codigo_familia', 'familia_producto__descripcion')

class ProductoAdmin(admin.ModelAdmin):
    form = ProductoForm
    list_display = ('codigo_producto', 'descripcion', 'familia_producto', 'subfamilia_producto', 'peso_unitario', 'armado', 'ficha_tecnica')    
    list_filter = ('familia_producto', 'subfamilia_producto')
    search_fields = ('codigo_producto', 'descripcion', 'familia_producto__codigo_familia', 'familia_producto__descripcion', 'subfamilia_producto__codigo_subfamilia', 'subfamilia_producto__familia_producto__codigo_familia', 'subfamilia_producto__familia_producto__descripcion', 'peso_unitario', 'armado')

class PiezaAdmin(admin.ModelAdmin):
    list_display = ('codigo_pieza', 'descripcion', 'familia_producto', 'subfamilia_producto', 'peso_unitario')
    list_filter = ('familia_producto', 'subfamilia_producto')
    search_fields = ('codigo_pieza', 'descripcion', 'familia_producto__codigo_familia', 'familia_producto__descripcion', 'subfamilia_producto__codigo_subfamilia', 'subfamilia_producto__familia_producto__codigo_familia', 'subfamilia_producto__familia_producto__descripcion', 'peso_unitario')

@admin.register(TerminacionFicha)
class TerminacionFichaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre')
    search_fields = ('codigo', 'nombre')

class FichaTecnicaAdmin(admin.ModelAdmin):
    list_display = (
        'producto',
        'pieza',
        'tipo_producto',
        'texto_largo_hilo',
        'largo_hilo',
        'hilos_por_pulgada',
        'peso_producto',
        'plano_ficha_path',
        'calibra_ficha',
        'observacion_ficha',
        'terminacion_ficha',
        'largo_cortar',
        'materia_prima_info',
        'observacion_mprima',
        'estandar_ficha',
    )
    list_filter = ('tipo_producto', 'materia_prima',) #Enable filtering by FK fields
    search_fields = (
        'tipo_producto__nombre',
        'texto_largo_hilo',
        'largo_hilo',
        'hilos_por_pulgada',
        'peso_producto',
        'producto__codigo_producto',
        'producto__descripcion',
        'codigo_materia_prima__nombre',
        'largo_cortar',
        'estandar_ficha'
    )
    def materia_prima_info(self, obj):
        if obj.materia_prima:
            return f"{obj.materia_prima.codigo} - {obj.materia_prima.nombre}"
        
    materia_prima_info.short_description = "Materia Prima"

admin.site.register(FamiliaProducto, FamiliaProductoAdmin)
admin.site.register(SubfamiliaProducto, SubfamiliaProductoAdmin)
admin.site.register(Producto, ProductoAdmin)
admin.site.register(Pieza, PiezaAdmin)
admin.site.register(TipoProducto)
admin.site.register(FichaTecnica, FichaTecnicaAdmin)