# -*- coding: utf-8 -*-
"""
routes/__init__.py - Inicialización del paquete de rutas

Este archivo importa todos los Blueprints de la aplicación
para que puedan ser registrados en app.py.

Blueprint = módulo de rutas en Flask
Cada blueprint agrupa las rutas relacionadas con una funcionalidad.
"""

# Importamos cada Blueprint desde su archivo correspondiente
from routes.principal import principal_bp
from routes.clientes import clientes_bp
from routes.ofertas import ofertas_bp
from routes.partes import partes_bp
from routes.facturas import facturas_bp

# Lista de todos los Blueprints disponibles
# Se usa en app.py para registrarlos automáticamente
blueprints = [
    principal_bp,
    clientes_bp,
    ofertas_bp,
    partes_bp,
    facturas_bp
]


