# -*- coding: utf-8 -*-
"""
models/oferta.py - Modelo de datos para Ofertas/Presupuestos

Define la estructura de la tabla 'ofertas' en la base de datos.
Una oferta es un presupuesto que se envía al cliente antes de realizar un trabajo.

Estados posibles:
- pendiente: Enviada al cliente, esperando respuesta
- aceptada: El cliente ha aceptado el presupuesto
- rechazada: El cliente ha rechazado el presupuesto
"""

from datetime import datetime
from decimal import Decimal
from models import db


class Oferta(db.Model):
    """
    Modelo SQLAlchemy para la tabla de ofertas/presupuestos.
    
    Representa cada presupuesto enviado a un cliente,
    con desglose de conceptos y totales.
    """
    
    # Nombre de la tabla en la base de datos
    __tablename__ = 'ofertas'
    
    # ==============================================================================
    # COLUMNAS DE LA TABLA
    # ==============================================================================
    
    # Identificador único
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Número de oferta formateado (ej: OFERTA-001)
    # Es único, no puede haber dos ofertas con el mismo número
    numero = db.Column(db.String(50), unique=True, nullable=False)
    
    # Cliente al que se envía la oferta (relación con tabla clientes)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    
    # Fecha de creación de la oferta
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Fecha de vencimiento de la oferta (opcional)
    fecha_vencimiento = db.Column(db.DateTime, nullable=True)
    
    # Descripción general del trabajo (opcional, ahora las partidas tienen el detalle)
    descripcion = db.Column(db.Text, nullable=True)
    
    # Importes económicos (usamos Numeric para precisión decimal)
    # Subtotal: suma de todos los conceptos antes de IVA
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    
    # IVA calculado sobre el subtotal
    iva = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Total final: subtotal + IVA
    total = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Estado de la oferta (pendiente, aceptada, rechazada)
    estado = db.Column(db.String(20), default='pendiente')
    
    # Forma de pago seleccionada por el cliente (efectivo, bizum, transferencia)
    forma_pago = db.Column(db.String(50), nullable=True)
    
    # Ruta al archivo PDF generado (puede ser nulo si no se ha generado)
    ruta_pdf = db.Column(db.String(500), nullable=True)
    
    # Fecha de creación del registro
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ==============================================================================
    # RELACIONES
    # ==============================================================================
    
    # Relación con cliente: cada oferta pertenece a un cliente
    cliente = db.relationship('Cliente', back_populates='ofertas')
    
    # Relación con facturas: una oferta puede generar una factura
    facturas = db.relationship('Factura', back_populates='oferta', lazy='dynamic')
    
    # Relación con partidas: una oferta tiene múltiples líneas/partidas
    partidas = db.relationship('OfertaPartida', back_populates='oferta', 
                               cascade='all, delete-orphan', lazy='dynamic')
    
    # ==============================================================================
    # MÉTODOS
    # ==============================================================================
    
    def __repr__(self):
        """Representación en texto de la oferta."""
        return f'<Oferta {self.numero}>'


class OfertaPartida(db.Model):
    """
    Modelo SQLAlchemy para las partidas/líneas de una oferta.
    
    Cada partida representa un concepto del presupuesto con su
    descripción, precio unitario, cantidad y total.
    """
    
    # Nombre de la tabla en la base de datos
    __tablename__ = 'oferta_partidas'
    
    # ==============================================================================
    # COLUMNAS DE LA TABLA
    # ==============================================================================
    
    # Identificador único
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Oferta a la que pertenece esta partida
    oferta_id = db.Column(db.Integer, db.ForeignKey('ofertas.id'), nullable=False)
    
    # Descripción del concepto/trabajo
    descripcion = db.Column(db.String(500), nullable=False)
    
    # Precio unitario
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Cantidad (puede ser decimal para horas, metros, etc.)
    cantidad = db.Column(db.Numeric(10, 2), nullable=False, default=1)
    
    # Total de la partida (precio * cantidad)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Orden de la partida en la oferta
    orden = db.Column(db.Integer, default=0)
    
    # ==============================================================================
    # RELACIONES
    # ==============================================================================
    
    # Relación inversa con oferta
    oferta = db.relationship('Oferta', back_populates='partidas')
    
    # ==============================================================================
    # MÉTODOS
    # ==============================================================================
    
    def __repr__(self):
        """Representación en texto de la partida."""
        return f'<OfertaPartida {self.descripcion[:30]}>'

