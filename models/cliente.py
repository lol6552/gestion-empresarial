# -*- coding: utf-8 -*-
"""
models/cliente.py - Modelo de datos para Clientes

Define la estructura de la tabla 'clientes' en la base de datos.
Cada cliente tiene información de contacto completa y descripción
del trabajo que necesita realizar.

Campos:
- id: Identificador único interno (auto-generado)
- codigo: Código visible del cliente (CLI-001, CLI-002, etc.)
- nombre, apellido: Nombre completo del cliente
- dni: Documento de identidad (único, no puede repetirse)
- telefono, direccion, codigo_postal, localidad: Datos de contacto
- trabajo_a_realizar: Descripción del trabajo solicitado
- fecha_creacion: Cuándo se registró el cliente
"""

from datetime import datetime
from models import db


class Cliente(db.Model):
    """
    Modelo SQLAlchemy para la tabla de clientes.
    
    Representa a cada cliente en el sistema con toda su información
    de contacto y el trabajo que necesita realizar.
    """
    
    # Nombre de la tabla en la base de datos
    __tablename__ = 'clientes'
    
    # ==============================================================================
    # COLUMNAS DE LA TABLA
    # ==============================================================================
    
    # Identificador único interno del cliente (se genera automáticamente)
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Código visible del cliente (CLI-001, CLI-002, etc.)
    # Este es el código que se muestra al usuario y se usa en documentos
    codigo = db.Column(db.String(20), unique=True, nullable=True)
    
    # Nombre del cliente (obligatorio, máximo 100 caracteres)
    nombre = db.Column(db.String(100), nullable=False)
    
    # Apellido del cliente (obligatorio, máximo 100 caracteres)
    apellido = db.Column(db.String(100), nullable=False)
    
    # DNI/NIE del cliente (obligatorio, único - no puede haber dos clientes con el mismo)
    dni = db.Column(db.String(20), unique=True, nullable=False)
    
    # Teléfono de contacto (obligatorio)
    telefono = db.Column(db.String(20), nullable=False)
    
    # Dirección completa (obligatorio)
    direccion = db.Column(db.String(200), nullable=False)
    
    # Código postal (obligatorio)
    codigo_postal = db.Column(db.String(10), nullable=False)
    
    # Localidad/Ciudad (obligatorio)
    localidad = db.Column(db.String(100), nullable=False)
    
    # Descripción del trabajo a realizar (opcional, puede ser largo)
    trabajo_a_realizar = db.Column(db.Text, nullable=True)
    
    # Fecha y hora de creación del registro (se pone automáticamente)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ==============================================================================
    # RELACIONES CON OTRAS TABLAS
    # ==============================================================================
    
    # Relación con ofertas: un cliente puede tener muchas ofertas
    # back_populates permite navegar en ambas direcciones
    ofertas = db.relationship('Oferta', back_populates='cliente', lazy='dynamic')
    
    # Relación con partes de trabajo
    partes = db.relationship('ParteTrabajo', back_populates='cliente', lazy='dynamic')
    
    # Relación con facturas
    facturas = db.relationship('Factura', back_populates='cliente', lazy='dynamic')
    
    # ==============================================================================
    # MÉTODOS
    # ==============================================================================
    
    @property
    def nombre_completo(self):
        """
        Devuelve el nombre completo del cliente (nombre + apellido).
        
        Retorna:
            str: Nombre y apellido concatenados
        """
        return f"{self.nombre} {self.apellido}"
    
    @property
    def tiene_documentos(self):
        """
        Verifica si el cliente tiene documentos asociados (ofertas, partes o facturas).
        
        Se usa para evitar eliminar clientes que tienen historial.
        
        Retorna:
            bool: True si tiene algún documento, False si no tiene ninguno
        """
        return (self.ofertas.count() > 0 or 
                self.partes.count() > 0 or 
                self.facturas.count() > 0)
    
    def __repr__(self):
        """
        Representación en texto del cliente (útil para debugging).
        
        Retorna:
            str: Representación del objeto Cliente
        """
        return f'<Cliente {self.id}: {self.nombre_completo}>'
