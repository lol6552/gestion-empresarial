# -*- coding: utf-8 -*-
"""
config.py - Configuración centralizada del Sistema de Gestión Empresarial

Este archivo contiene TODA la configuración de la aplicación:
- Rutas de base de datos
- Datos del autónomo
- Constantes de negocio (IVA, formas de pago)
- Configuración de Flask

IMPORTANTE: Modificar este archivo para cambiar cualquier configuración.
"""

import os

# ==============================================================================
# RUTAS BASE
# ==============================================================================

# Ruta base del proyecto
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Carpeta instance para datos persistentes (BD y PDFs)
# os.makedirs con exist_ok=True crea la carpeta si no existe,
# y no da error si ya existe. Esto es CLAVE para que funcione
# en Docker/EasyPanel donde el contenedor arranca desde cero.
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
os.makedirs(INSTANCE_DIR, exist_ok=True)

# ==============================================================================
# CONFIGURACIÓN DE FLASK
# ==============================================================================

class Config:
    """
    Clase de configuración para Flask.
    
    Contiene todas las variables de configuración necesarias
    para el funcionamiento de la aplicación.
    """
    
    # Clave secreta para sesiones y seguridad
    # En producción (EasyPanel), esta clave se configura vía variable de entorno SECRET_KEY
    # En desarrollo, usa la clave por defecto (solo para pruebas locales)
    SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-secreta-desarrollo-cambiar-en-produccion')
    
    # Ruta de la base de datos
    # Si existe la variable de entorno DATABASE_URL, la usa (permite PostgreSQL en el futuro).
    # Si no existe, usa SQLite en instance/database.db (desarrollo local).
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(INSTANCE_DIR, "database.db")}'
    )
    
    # Desactivar el seguimiento de modificaciones (mejora rendimiento)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Carpeta para almacenar PDFs generados
    PDF_FOLDER = os.path.join(INSTANCE_DIR, 'pdfs')

# ==============================================================================
# DATOS DEL AUTÓNOMO
# ==============================================================================

# Información del autónomo que aparece en todos los documentos
AUTONOMO = {
    'nombre': 'Javier Aranguren Meneses',
    'dni': '73487357B',
    'direccion': 'C/ Foz de Lumbier 10,Bajo A. Sarriguren',
    'cuenta_bancaria': 'ES95 0182 5297 23 0201854500',
    'profesion': 'Electricista- Mantenimiento General',
    'telefono': '+34) 634 42 66 24',
    'email': 'aransk27.1@gmail.com',
    'web': '---'
}

# ==============================================================================
# CONSTANTES DE NEGOCIO
# ==============================================================================

# Porcentaje de IVA aplicable (21% es el tipo general en España)
IVA_PORCENTAJE = 21

# Formas de pago disponibles
FORMAS_PAGO = [
    ('transferencia', 'Transferencia bancaria'),
    ('bizum', 'Bizum'),
    ('efectivo', 'Efectivo')
]

# Estados posibles para ofertas
ESTADOS_OFERTA = [
    ('pendiente', 'Pendiente'),
    ('aceptada', 'Aceptada'),
    ('rechazada', 'Rechazada')
]

# ==============================================================================
# CONFIGURACIÓN DEL SERVIDOR
# ==============================================================================

# Host: 0.0.0.0 permite acceso desde red local
# Puede ser sobrescrito por variable de entorno SERVER_HOST
SERVER_HOST = os.environ.get('SERVER_HOST', '0.0.0.0')

# Puerto por defecto (puede ser sobrescrito por variable de entorno SERVER_PORT)
SERVER_PORT = int(os.environ.get('SERVER_PORT', 5000))

# Modo debug: habilitado en desarrollo, deshabilitado en producción
# Se determina automáticamente según la variable FLASK_ENV
DEBUG_MODE = os.environ.get('FLASK_ENV', 'development') == 'development'
