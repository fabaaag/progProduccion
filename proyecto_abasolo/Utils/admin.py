from django.contrib import admin
from .models import *

# Register your models here.
@admin.register(MeasurementUnit)
class MeasurementUnitAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo_und_medida']
    search_fields = ['nombre', 'codigo_und_medida']
    list_per_page = 20

@admin.register(MateriaPrima)
class MateriaPrimaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre']
    search_fields = ['codigo', 'nombre']
    
