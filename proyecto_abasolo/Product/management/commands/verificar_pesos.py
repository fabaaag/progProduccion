from django.core.management.base import BaseCommand
from django.db.models import Q
from JobManagement.models import OrdenTrabajo
from Product.models import Producto, Pieza
from decimal import Decimal

class Command(BaseCommand):
    help='Verifica y compara los pesos entre Ots y sus productos y/o piezas correspondientes'

    def handle(self, *args, **kwargs):
        discrepancias =[]
        ots_sin_producto = []
        productos_no_encontrados = []
        total_ots = 0
        ots_con_discrepancia = 0

        self.stdout.write('Iniciando verificación de pesos...')

        #Obener todas las Ots
        ordenes_trabajo = OrdenTrabajo.objects.all()
        total_ots = ordenes_trabajo.count()

        for ot in ordenes_trabajo:
            try:
                #Buscar producto salida
                producto_salida = None
                try:
                    #Primero buscar en Productos
                    producto_salida = Producto.objects.filter(
                        codigo_producto=ot.codigo_producto_salida
                    ).first()
                    
                    #Si no se encuentra en Productos, buscar en Piezas
                    if not producto_salida:
                        producto_salida = Pieza.objects.filter(
                            codigo_pieza=ot.codigo_producto_salida
                        ).first()
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Error al buscar producto {ot.codigo_producto_salida} : {str(e)}')
                    )
                    
                #Si no se encontró el producto
                if not producto_salida:
                    productos_no_encontrados.append({
                        'ot': ot.codigo_ot,
                        'codigo_salida': ot.codigo_producto.salida
                    })
                    continue

                #Verificar discrepancia
                peso_ot = Decimal(str(ot.peso_unitario))
                peso_producto = Decimal(str(producto_salida.peso_unitario))

                #Solo registrar si hay diferencia significativa
                if abs(peso_producto - peso_ot) > Decimal('0.00001'):
                    discrepancias.append({
                        'ot': ot.codigo_ot,
                        'codigo_producto': ot.codigo_producto_salida,
                        'descripcion_producto': producto_salida.descripcion,
                        'peso_ot': float(peso_ot),
                        'peso_producto': float(peso_producto),
                        'diferencia': float(peso_producto- peso_ot)
                    })
                    ots_con_discrepancia += 1
                    
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error procesando OT {ot.codigo_ot}: {str(e)}')
                )

        #Mostrar resumen
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(f'RESUMEN DE VERIFICACIÓN'))
        self.stdout.write("="*50)
        self.stdout.write(f'Total de OTs revisadas: {total_ots}')
        self.stdout.write(f'OTs con discrepancias: {ots_con_discrepancia}')
        self.stdout.write(f'Productos no encontrados: {len(productos_no_encontrados)}')

        #Mostrar discrepancias encontradas
        if discrepancias:
            self.stdout.write("\n" + "="*50)
            self.stdout.write(self.style.WARNING("DISCREPANCIAS ENCONTRADAS"))
            self.stdout.write("="*50)
            for d in discrepancias:
                self.stdout.write(
                    f"OT: {d['ot']}\n"
                    f"Producto: {d['codigo_producto']} - {d['descripcion_producto']}\n"
                    f"  Peso OT: {d['peso_ot']:.5f} kg\n"
                    f"  Peso Producto: {d['peso_producto']:.5f} kg\n"
                    f"  Diferencia: {d['diferencia']:.5f} kg\n"
                )

        #Mostrar productos no encontrados
        if productos_no_encontrados:
            self.stdout.write("\n" + "="*50)
            self.stdout.write(self.style.WARNING("PRODUCTOS NO ENCONTRADOS"))
            self.stdout.write("="*50)
            for p in productos_no_encontrados:
                self.stdoutt.write(
                    f"OT: {p['ot']}\n"
                    f"  Código producto: {p['codigo_salida']}\n"
                )

        


        #Mostrar mensaje de finalización
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("VERIFICACIÓN COMPLETADA"))
        
        