# -*- coding: utf-8 -*-
"""
models/__init__.py - Inicialización del paquete de modelos

Este archivo:
1. Crea la instancia de SQLAlchemy (db)
2. Importa todos los modelos para que estén disponibles

Para usar en otros archivos:
    from models import db, Cliente, Oferta, OfertaPartida, ParteTrabajo, Factura, Numerador
"""

from flask_sqlalchemy import SQLAlchemy

# ==============================================================================
# INSTANCIA DE SQLALCHEMY
# ==============================================================================

# Esta instancia se usará en toda la aplicación para interactuar con la BD
# Se inicializa con la app de Flask en app.py usando db.init_app(app)
db = SQLAlchemy()

# ==============================================================================
# IMPORTACIÓN DE MODELOS
# ==============================================================================

# Importamos todos los modelos después de crear db para evitar importaciones circulares
from models.cliente import Cliente
from models.numerador import Numerador
from models.oferta import Oferta, OfertaPartida
from models.parte import ParteTrabajo, PartePartida
from models.factura import Factura, FacturaPartida

# Lista de todos los modelos disponibles (útil para operaciones masivas)
__all__ = ['db', 'Cliente', 'Numerador', 'Oferta', 'OfertaPartida', 'ParteTrabajo', 'PartePartida', 'Factura', 'FacturaPartida']

