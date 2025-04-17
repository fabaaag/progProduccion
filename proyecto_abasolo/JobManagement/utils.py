def calcular_progreso_acumulado(fragmento):
    """
    Calcula el progreso acumulado de una tarea fragmentada y todas sus continuaciones.
    
    Args:
        fragmento: Instancia de TareaFragmentada
        
    Returns:
        float: Porcentaje de progreso acumulado (0-100)
    """
    # Cantidad total completada en este fragmento y sus continuaciones
    total_completado = fragmento.cantidad_completada
    
    # Función recursiva auxiliar para sumar cantidades completadas
    def sumar_completado_recursivamente(frag):
        suma = 0
        # Obtener todas las continuaciones directas
        continuaciones = frag.continuaciones.all()
        for cont in continuaciones:
            suma += cont.cantidad_completada
            # Sumar recursivamente las continuaciones de las continuaciones
            suma += sumar_completado_recursivamente(cont)
        return suma
    
    # Añadir cantidades completadas de todas las continuaciones
    total_completado += sumar_completado_recursivamente(fragmento)
    
    # Obtener cantidad total asignada originalmente a la tarea raíz
    tarea_original = fragmento
    while tarea_original.tarea_padre:
        tarea_original = tarea_original.tarea_padre
    
    # La cantidad original es la asignada a la primera tarea de la cadena
    cantidad_original = tarea_original.cantidad_asignada
    
    # Calcular porcentaje
    if cantidad_original > 0:
        porcentaje = (total_completado / cantidad_original) * 100
        return min(100, round(porcentaje, 2))  # Limitamos a 100% máximo
    return 0