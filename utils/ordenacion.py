# -*- coding: utf-8 -*-
"""
utils/ordenacion.py - Utilidad reutilizable para ordenación dinámica de tablas

Este archivo contiene la función de ordenación que se usa en TODAS las vistas
de listado (Clientes, Ofertas, Partes, Facturas).

La función valida el campo de ordenación contra una lista blanca (whitelist)
para evitar inyección de SQL, y aplica el order_by correspondiente.

Para usar en cualquier vista:
    from utils.ordenacion import aplicar_ordenacion
    query = aplicar_ordenacion(query, sort_key, order, CAMPOS_PERMITIDOS)
"""


def aplicar_ordenacion(query, sort_key, order, campos_permitidos):
    """
    Aplica ordenación dinámica a una consulta SQLAlchemy.
    
    Valida que el campo solicitado esté en la lista blanca antes de
    aplicar el order_by. Si no está, devuelve la consulta sin modificar
    (se mantiene el orden por defecto de la vista).
    
    Parámetros:
        query: Consulta SQLAlchemy a la que aplicar ordenación
        sort_key (str): Clave del campo por el que ordenar (ej: 'nombre', 'dni')
        order (str): Dirección de la ordenación ('asc' o 'desc')
        campos_permitidos (dict): Diccionario que mapea claves GET a columnas
                                  del modelo SQLAlchemy.
                                  Ej: {'nombre': Cliente.apellido, 'dni': Cliente.dni}
    
    Retorna:
        Query: La consulta con order_by aplicado, o sin modificar si la clave no es válida
    """
    # Buscamos la columna en la lista blanca
    columna = campos_permitidos.get(sort_key)
    
    # Si la clave no está en la lista blanca, devolvemos la consulta sin cambios
    if columna is None:
        return query
    
    # Aplicamos la ordenación según la dirección solicitada
    if order == 'desc':
        return query.order_by(columna.desc())
    else:
        # Por defecto, orden ascendente
        return query.order_by(columna.asc())
