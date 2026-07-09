

# -*- coding: utf-8 -*-
"""
app.py - Punto de entrada del Sistema de Gestión Empresarial

Este archivo contiene SOLO:
- Inicialización de Flask
- Configuración de la base de datos
- Registro de Blueprints
- Creación de directorios necesarios

La lógica de negocio está en routes/
Los modelos están en models/
La configuración está en config.py
"""

import os
from flask import Flask

# Importamos la configuración
from config import Config, INSTANCE_DIR

# Importamos la base de datos y los modelos
from models import db

# Importamos los Blueprints
from routes import blueprints





def crear_app():
    """
    Función fábrica para crear la aplicación Flask.
    
    Esta función:
    1. Crea la instancia de Flask
    2. Aplica la configuración
    3. Inicializa la base de
    4. Registra los Blueprints
    5. Crea las tablas si no existen
    
    Retorna:
        Flask: Aplicación Flask configurada y lista para usar
    """
    # ==============================================================================
    # CREAR APLICACIÓN FLASK
    # ==============================================================================
    
    app = Flask(__name__)
    
    # Aplicamos la configuración desde config.py
    app.config.from_object(Config)
    
    ######chatyyyy###
    from version import APP_VERSION, APP_DATE, APP_CHANGE

    @app.route("/version")
    def version():
        return {
            "version": APP_VERSION,
            "date": APP_DATE,
            "change": APP_CHANGE
        }
    # ==============================================================================
    # CREAR DIRECTORIOS NECESARIOS
    # ==============================================================================
    
    # Creamos la carpeta instance si no existe
    if not os.path.exists(INSTANCE_DIR):
        os.makedirs(INSTANCE_DIR)
    
    # Creamos las carpetas para PDFs si no existen
    carpetas_pdf = ['ofertas', 'partes', 'facturas']
    for carpeta in carpetas_pdf:
        ruta = os.path.join(INSTANCE_DIR, 'pdfs', carpeta)
        if not os.path.exists(ruta):
            os.makedirs(ruta)
    
    # ==============================================================================
    # INICIALIZAR BASE DE DATOS
    # ==============================================================================
    
    # Conectamos SQLAlchemy con Flask
    db.init_app(app)
    
    # Creamos las tablas dentro del contexto de la aplicación
    with app.app_context():
        # Importamos todos los modelos para que SQLAlchemy los conozca
        from models import Cliente, Numerador, Oferta, ParteTrabajo, Factura
        
        # Creamos todas las tablas que no existan
        db.create_all()
    
    # ==============================================================================
    # REGISTRAR BLUEPRINTS
    # ==============================================================================
    
    # Registramos cada Blueprint de la lista
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
    
    return app


# ==============================================================================
# PUNTO DE ENTRADA
# ==============================================================================

if __name__ == '__main__':
    # Importamos las variables del servidor desde config
    from config import SERVER_HOST, SERVER_PORT, DEBUG_MODE
    
    # Creamos la aplicación
    app = crear_app()
    
    # Mensaje informativo
    print("=" * 60)
    print("SISTEMA DE GESTIÓN EMPRESARIAL")
    print("=" * 60)
    print(f"Servidor iniciado en: http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"Acceso local: http://localhost:{SERVER_PORT}")
    print("Presiona Ctrl+C para detener el servidor")
    print("=" * 60)
    
    # Ejecutamos el servidor
    # host='0.0.0.0' permite acceso desde otros dispositivos en la red local
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=DEBUG_MODE)
