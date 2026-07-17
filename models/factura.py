# -*- coding: utf-8 -*-
"""
models/factura.py - Modelo de datos para Facturas

Define la estructura de la tabla 'facturas' en la base de datos.
Una factura puede crearse:
- Desde una oferta aceptada
- Desde un parte de trabajo
- De forma manual (sin vincular a oferta ni parte)
"""

from datetime import datetime
from decimal import Decimal
from models import db


class Factura(db.Model):
    """
    Modelo SQLAlchemy para la tabla de facturas.
    
    Representa cada factura emitida al cliente,
    que puede originarse de una oferta, un parte, o ser manual.
    """
    
    # Nombre de la tabla en la base de datos
    __tablename__ = 'facturas'
    
    # ==============================================================================
    # COLUMNAS DE LA TABLA
    # ==============================================================================
    
    # Identificador único
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Número de factura formateado (ej: FACTURA-001)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    
    # Cliente al que se emite la factura
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    
    # Oferta de origen (opcional, solo si se crea desde oferta)
    oferta_id = db.Column(db.Integer, db.ForeignKey('ofertas.id'), nullable=True)
    
    # Parte de trabajo de origen (opcional, solo si se crea desde parte)
    parte_id = db.Column(db.Integer, db.ForeignKey('partes_trabajo.id'), nullable=True)
    
    # Fecha de emisión de la factura
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Descripción general del trabajo facturado (opcional, para notas adicionales)
    descripcion = db.Column(db.Text, nullable=True)
    
    # Importes económicos
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    iva = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Forma de pago utilizada (transferencia, bizum, efectivo)
    forma_pago = db.Column(db.String(50), nullable=False)
    
    # Estado de pago de la factura (True para pagada, False para pendiente)
    pagada = db.Column(db.Boolean, default=False, nullable=False)
    
    # Ruta al archivo PDF generado
    ruta_pdf = db.Column(db.String(500), nullable=True)
    
    # Fecha de creación del registro
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ==============================================================================
    # RELACIONES
    # ==============================================================================
    
    # Relación con cliente
    cliente = db.relationship('Cliente', back_populates='facturas')
    
    # Relación con oferta (si se creó desde una oferta)
    oferta = db.relationship('Oferta', back_populates='facturas')
    
    # Relación con parte de trabajo (si se creó desde un parte)
    parte = db.relationship('ParteTrabajo', back_populates='facturas')
    
    # Relación con partidas: una factura tiene múltiples líneas de conceptos
    partidas = db.relationship('FacturaPartida', back_populates='factura', 
                               cascade='all, delete-orphan', lazy='dynamic')
    
    # ==============================================================================
    # PROPIEDADES
    # ==============================================================================
    
    @property
    def origen(self):
        """
        Indica el origen de la factura.
        
        Retorna:
            str: 'oferta', 'parte' o 'manual'
        """
        if self.oferta_id:
            return 'oferta'
        elif self.parte_id:
            return 'parte'
        else:
            return 'manual'
    
    @property
    def origen_detalle(self):
        """
        Devuelve información detallada del origen.
        
        Retorna:
            str: Número del documento origen o 'Manual'
        """
        if self.oferta:
            return f"Oferta {self.oferta.numero}"
        elif self.parte:
            return f"Parte {self.parte.numero}"
        else:
            return "Manual"
    
    def __repr__(self):
        """Representación en texto de la factura."""
        return f'<Factura {self.numero}>'


class FacturaPartida(db.Model):
    """
    Modelo SQLAlchemy para las partidas/líneas de una factura.
    
    Cada partida representa un concepto o material con su
    descripción, cantidad, precio unitario y total.
    """
    
    # Nombre de la tabla en la base de datos
    __tablename__ = 'factura_partidas'
    
    # ==============================================================================
    # COLUMNAS DE LA TABLA
    # ==============================================================================
    
    # Identificador único
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Factura a la que pertenece esta partida
    factura_id = db.Column(db.Integer, db.ForeignKey('facturas.id'), nullable=False)
    
    # Descripción del concepto o material
    descripcion = db.Column(db.String(500), nullable=False)
    
    # Cantidad
    cantidad = db.Column(db.Numeric(10, 2), nullable=False, default=1)
    
    # Precio unitario
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Total de la partida (cantidad * precio)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Orden de la partida en la factura
    orden = db.Column(db.Integer, default=0)
    
    # ==============================================================================
    # RELACIONES
    # ==============================================================================
    
    # Relación inversa con factura
    factura = db.relationship('Factura', back_populates='partidas')
    
    # ==============================================================================
    # MÉTODOS
    # ==============================================================================
    
    def __repr__(self):
        """Representación en texto de la partida."""
        return f'<FacturaPartida {self.descripcion[:30]}>'

