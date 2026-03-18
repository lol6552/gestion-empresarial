# -*- coding: utf-8 -*-
"""
models/parte.py - Modelo de datos para Partes de Trabajo

Define la estructura de la tabla 'partes_trabajo' en la base de datos.
Un parte de trabajo registra un servicio realizado, generalmente en emergencias.

Incluye desglose detallado de:
- Control horario (hora inicio, fin, horas trabajadas)
- Desplazamiento (horas y coste)
- Materiales utilizados
- Cálculo automático de totales
"""

from datetime import datetime, date, time
from decimal import Decimal
from models import db


class ParteTrabajo(db.Model):
    """
    Modelo SQLAlchemy para la tabla de partes de trabajo.
    
    Representa cada trabajo realizado con control detallado de:
    tiempos, desplazamientos, materiales y costes.
    """
    
    # Nombre de la tabla en la base de datos
    __tablename__ = 'partes_trabajo'
    
    # ==============================================================================
    # IDENTIFICACIÓN
    # ==============================================================================
    
    # Identificador único
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Número de parte formateado (ej: PARTE-001)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    
    # Cliente para el que se realizó el trabajo
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    
    # Fecha en que se realizó el trabajo
    fecha_realizacion = db.Column(db.Date, nullable=False)
    
    # Descripción del trabajo realizado
    descripcion = db.Column(db.Text, nullable=False)
    
    # ==============================================================================
    # CONTROL HORARIO
    # ==============================================================================
    
    # Hora de inicio del trabajo (formato HH:MM)
    hora_inicio = db.Column(db.Time, nullable=False)
    
    # Hora de finalización del trabajo (formato HH:MM)
    hora_fin = db.Column(db.Time, nullable=False)
    
    # Horas de trabajo (calculadas: fin - inicio)
    # Se almacena el resultado del cálculo para mantener historial
    horas_trabajo = db.Column(db.Numeric(5, 2), nullable=False)
    
    # Precio por hora de trabajo
    precio_hora_trabajo = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Subtotal de horas de trabajo = horas_trabajo × precio_hora_trabajo
    subtotal_trabajo = db.Column(db.Numeric(10, 2), nullable=False)
    
    # ==============================================================================
    # DESPLAZAMIENTO
    # ==============================================================================
    
    # Horas de desplazamiento (puede incluir decimales, ej: 1.5 horas)
    horas_desplazamiento = db.Column(db.Numeric(5, 2), default=0)
    
    # Precio por hora de desplazamiento
    precio_hora_desplazamiento = db.Column(db.Numeric(10, 2), default=0)
    
    # Subtotal desplazamiento = horas_desplazamiento × precio_hora_desplazamiento
    subtotal_desplazamiento = db.Column(db.Numeric(10, 2), default=0)
    
    # ==============================================================================
    # MATERIALES
    # ==============================================================================
    
    # Descripción de los materiales usados (opcional)
    materiales_descripcion = db.Column(db.Text, nullable=True)
    
    # Importe total de materiales
    materiales_importe = db.Column(db.Numeric(10, 2), default=0)
    
    # ==============================================================================
    # TOTALES
    # ==============================================================================
    
    # Subtotal general = trabajo + desplazamiento + materiales
    subtotal_general = db.Column(db.Numeric(10, 2), nullable=False)
    
    # IVA (21% sobre subtotal_general)
    iva = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Total final = subtotal_general + IVA
    total = db.Column(db.Numeric(10, 2), nullable=False)
    
    # ==============================================================================
    # METADATOS
    # ==============================================================================
    
    # Ruta al archivo PDF generado
    ruta_pdf = db.Column(db.String(500), nullable=True)
    
    # Fecha de creación del registro
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ==============================================================================
    # RELACIONES
    # ==============================================================================
    
    # Relación con cliente
    cliente = db.relationship('Cliente', back_populates='partes')
    
    # Relación con facturas (un parte puede generar una factura)
    facturas = db.relationship('Factura', back_populates='parte', lazy='dynamic')
    
    # Relación con partidas: un parte tiene múltiples líneas de materiales/trabajos
    partidas = db.relationship('PartePartida', back_populates='parte', 
                               cascade='all, delete-orphan', lazy='dynamic')
    
    # ==============================================================================
    # MÉTODOS DE CÁLCULO
    # ==============================================================================
    
    @staticmethod
    def calcular_horas_trabajo(hora_inicio, hora_fin):
        """
        Calcula las horas de trabajo a partir de hora inicio y fin.
        
        Parámetros:
            hora_inicio (time): Hora de inicio del trabajo
            hora_fin (time): Hora de finalización
        
        Retorna:
            Decimal: Horas trabajadas con precisión de 2 decimales
        
        Ejemplo:
            horas = ParteTrabajo.calcular_horas_trabajo(
                time(9, 0),   # 09:00
                time(14, 30)  # 14:30
            )
            # Devuelve: Decimal('5.50')
        """
        # Convertir a minutos desde medianoche
        minutos_inicio = hora_inicio.hour * 60 + hora_inicio.minute
        minutos_fin = hora_fin.hour * 60 + hora_fin.minute
        
        # Calcular diferencia en horas (con 2 decimales)
        diferencia_minutos = minutos_fin - minutos_inicio
        horas = Decimal(diferencia_minutos) / Decimal(60)
        
        return round(horas, 2)
    
    @property
    def incluye_desplazamiento(self):
        """Indica si el parte incluye costes de desplazamiento."""
        return self.horas_desplazamiento > 0
    
    @property
    def incluye_materiales(self):
        """Indica si el parte incluye materiales (partidas)."""
        return self.partidas.count() > 0 or self.materiales_importe > 0
    
    def __repr__(self):
        """Representación en texto del parte."""
        return f'<ParteTrabajo {self.numero}>'


class PartePartida(db.Model):
    """
    Modelo SQLAlchemy para las partidas/líneas de un parte de trabajo.
    
    Cada partida representa un material o trabajo con su
    descripción, cantidad, precio unitario y total.
    """
    
    # Nombre de la tabla en la base de datos
    __tablename__ = 'parte_partidas'
    
    # ==============================================================================
    # COLUMNAS DE LA TABLA
    # ==============================================================================
    
    # Identificador único
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Parte al que pertenece esta partida
    parte_id = db.Column(db.Integer, db.ForeignKey('partes_trabajo.id'), nullable=False)
    
    # Descripción del material o trabajo
    descripcion = db.Column(db.String(500), nullable=False)
    
    # Cantidad
    cantidad = db.Column(db.Numeric(10, 2), nullable=False, default=1)
    
    # Precio unitario
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Total de la partida (cantidad * precio)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Orden de la partida en el parte
    orden = db.Column(db.Integer, default=0)
    
    # ==============================================================================
    # RELACIONES
    # ==============================================================================
    
    # Relación inversa con parte
    parte = db.relationship('ParteTrabajo', back_populates='partidas')
    
    # ==============================================================================
    # MÉTODOS
    # ==============================================================================
    
    def __repr__(self):
        """Representación en texto de la partida."""
        return f'<PartePartida {self.descripcion[:30]}>'

