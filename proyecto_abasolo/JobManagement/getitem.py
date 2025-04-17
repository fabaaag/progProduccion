import os
import sys
import django

# Agregar el directorio del proyecto al path de Python
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_path)

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto_abasolo.settings')
django.setup()

# Ahora podemos importar los modelos
from JobManagement.models import Proceso, Ruta, RutaPieza

def get_rutas_fabricacion():
    codigo_proceso = '9999'
    try:
# Obtener el proceso de fabricación
        proceso_fabricacion = Proceso.objects.get(codigo_proceso=codigo_proceso)
        print(f"Proceso encontrado: {proceso_fabricacion.descripcion}, {proceso_fabricacion.codigo_proceso}")

        # Conjunto para almacenar máquinas únicas (usamos set para evitar duplicados)
        maquinas_unicas = set()

        # Obtener todas las rutas de productos que usan este proceso
        rutas_productos = Ruta.objects.filter(
            proceso=proceso_fabricacion
        ).select_related('producto', 'maquina')

        # Obtener todas las rutas de piezas que usan este proceso
        rutas_piezas = RutaPieza.objects.filter(
    proceso=proceso_fabricacion
        ).select_related('pieza', 'maquina')

         # Recolectar máquinas únicas
        print("\n=== RECOLECTANDO MÁQUINAS ÚNICAS ===")
        for ruta in rutas_productos:
            if ruta.maquina.codigo_maquina not in maquinas_unicas:
                maquinas_unicas.add(ruta.maquina.codigo_maquina)
                print(f"Nueva máquina encontrada en productos: {ruta.maquina.codigo_maquina} - {ruta.maquina.descripcion}")

        for ruta in rutas_piezas:
            if ruta.maquina.codigo_maquina not in maquinas_unicas:
                maquinas_unicas.add(ruta.maquina.codigo_maquina)
                print(f"Nueva máquina encontrada en piezas: {ruta.maquina.codigo_maquina} - {ruta.maquina.descripcion}")

        print(f"\nTotal de máquinas únicas encontradas: {len(maquinas_unicas)}")
        print("\nLista de códigos de máquinas únicas:")
        for codigo in sorted(maquinas_unicas):
            print(f"- {codigo}")

    except Proceso.DoesNotExist:
        print(f"No se encontró el proceso con código {codigo_proceso}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    maquinas = get_rutas_fabricacion()
    print("\nPuedes usar la lista de máquinas así:", maquinas)