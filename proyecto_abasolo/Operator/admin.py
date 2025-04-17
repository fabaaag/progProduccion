from django.contrib import admin
from .models import Operador, OperadorMaquina, AsignacionOperador

@admin.register(Operador)
class OperadorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'activo', 'empresa', 'created_at')
    list_filter = ('activo', 'empresa')
    search_fields = ('nombre', 'rut')
    date_hierarchy = 'created_at'

@admin.register(OperadorMaquina)
class OperadorMaquinaAdmin(admin.ModelAdmin):
    list_display = ('operador', 'maquina', 'fecha_habilitacion', 'activo')
    list_filter = ('activo', 'fecha_habilitacion')
    search_fields = ('operador__nombre', 'maquina__codigo_maquina')

@admin.register(AsignacionOperador)
class AsignacionOperadorAdmin(admin.ModelAdmin):
    list_display = ('operador', 'item_ruta', 'programa', 'fecha_inicio', 'fecha_fin')
    list_filter = ('programa', 'fecha_inicio')
    search_fields = ('operador__nombre', 'programa__nombre')
    date_hierarchy = 'fecha_inicio'