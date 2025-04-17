from django.contrib import admin
from .models import Cliente
# Register your models here.

class ClienteAdmin(admin.ModelAdmin):
   search_fields = (
      'codigo_cliente',
      'nombre',
      'vip',
      'apodo'
   )
   list_filter = (
      'vip',
      'apodo'
   )
admin.site.register(Cliente, ClienteAdmin)