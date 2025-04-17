from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from Utils.models import MeasurementUnit, MateriaPrima
    
class FamiliaProducto(models.Model):
    codigo_familia = models.CharField(max_length=2, unique=True)
    descripcion = models.CharField(max_length=50, blank=False, null=False)
    
    def __str__(self):
        return f'{self.descripcion}'
    
class SubfamiliaProducto(models.Model):
    codigo_subfamilia = models.CharField(max_length=5, unique=True)
    familia_producto = models.ForeignKey(FamiliaProducto, on_delete=models.CASCADE)
    descripcion = models.CharField(max_length=100, blank=False, null=False)

    def __str__(self):
        return f'{self.descripcion}'
    
class TipoProducto(models.Model):
    codigo = models.CharField(max_length=12, unique=True, null=False, blank=False)
    nombre = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'
        
class TerminacionFicha(models.Model):
    codigo = models.CharField(max_length=12, unique=True)
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'
    
class FichaTecnica(models.Model):
    tipo_producto = models.ForeignKey(TipoProducto, on_delete=models.CASCADE, blank=True)
    texto_largo_hilo = models.CharField(max_length=255)
    largo_hilo = models.DecimalField(max_digits=12, decimal_places=5)
    hilos_por_pulgada = models.IntegerField()
    peso_producto = models.DecimalField(max_digits=12, decimal_places=5)
    plano_ficha = models.FileField(upload_to='planos_fichas/', blank=True, null=True)
    plano_ficha_path = models.CharField(max_length=50, blank=True, null=True)
    calibra_ficha = models.CharField(max_length=50, blank=True, null=True)
    observacion_ficha = models.TextField(blank=True, null=True)
    terminacion_ficha = models.ForeignKey(TerminacionFicha, on_delete=models.CASCADE, blank=True, null=True)
    materia_prima = models.ForeignKey(MateriaPrima, on_delete=models.CASCADE, blank=True, null=True)
    largo_cortar = models.DecimalField(max_digits=12, decimal_places=5)
    observacion_mprima = models.TextField(blank=True, null=True)
    estandar_ficha = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        try:
            return f'FichaTecnica para {self.producto.descripcion} ID: self.id'
        except ObjectDoesNotExist:
            return f'FichaTecnica sin producto asociado ID: {self.id}'
        
class Producto(models.Model):
    codigo_producto = models.CharField(max_length=12, unique=True, null=False, blank=False)
    descripcion = models.CharField(max_length=100, null=False, blank=False)

    familia_producto = models.ForeignKey(FamiliaProducto, on_delete=models.SET_NULL, null=True, blank=True)
    subfamilia_producto = models.ForeignKey(SubfamiliaProducto, on_delete=models.SET_NULL, null=True, blank=True)

    peso_unitario = models.DecimalField(max_digits=15, decimal_places=5)
    und_medida = models.ForeignKey(MeasurementUnit, on_delete=models.PROTECT, null=True, blank=True)

    armado = models.BooleanField(default=False)

    ficha_tecnica = models.OneToOneField(FichaTecnica, on_delete=models.CASCADE, related_name='producto', null=True, blank=True)

    def __str__(self):
        return self.descripcion
    
    def save(self, *args, **kwargs):
        #Extrae los codgios familia y subfamilia del codigo de producto
        codigo_familia = self.codigo_producto[:2]
        codigo_subfamilia = self.codigo_producto[:5]

        familia_producto, created = FamiliaProducto.objects.get_or_create(codigo_familia=codigo_familia)
        self.familia_producto = familia_producto

        subfamilia_producto, created = SubfamiliaProducto.objects.get_or_create(codigo_subfamilia=codigo_subfamilia)
        self.subfamilia_producto = subfamilia_producto

        super(Producto, self).save(*args, **kwargs)

class Pieza(models.Model):
    codigo_pieza = models.CharField(max_length=12, unique=True, null=False, blank=False)
    descripcion = models.CharField(max_length=100, null=False, blank=False)

    familia_producto = models.ForeignKey(FamiliaProducto, on_delete=models.SET_NULL, null=True, blank=True)
    subfamilia_producto = models.ForeignKey(SubfamiliaProducto, on_delete=models.SET_NULL, null=True, blank=True)

    peso_unitario = models.DecimalField(max_digits=8, decimal_places=4, default=0.0000)
    und_medida = models.ForeignKey(MeasurementUnit, on_delete=models.PROTECT, null=True, blank=True)

    ficha_tecnica = models.OneToOneField(FichaTecnica, on_delete=models.CASCADE, related_name='pieza', null=True, blank=True)

    def __str__(self):
        return f'{self.descripcion}'

    def save(self, *args, **kwargs):
        codigo_familia = self.codigo_pieza[:2]
        codigo_subfamilia = self.codigo_pieza[:5]

        familia_producto, created = FamiliaProducto.objects.get_or_create(codigo_familia=codigo_familia)
        self.familia_producto = familia_producto

        subfamilia_producto, created = SubfamiliaProducto.objects.get_or_create(codigo_subfamilia=codigo_subfamilia, familia_producto=familia_producto)
        self.subfamilia_producto = subfamilia_producto

        super(Pieza, self).save(*args, **kwargs)