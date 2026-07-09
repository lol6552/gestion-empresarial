# -*- coding: utf-8 -*-
"""
models/numerador.py - Sistema de numeración automática de documentos

Este modelo gestiona la numeración correlativa de:
- Ofertas (OFERTA-001, OFERTA-002, ...)
- Partes de trabajo (PARTE-001, PARTE-002, ...)
- Facturas (FACTURA-001, FACTURA-002, ...)

Cada tipo de documento tiene su propia secuencia independiente.
Los números nunca se repiten ni tienen saltos.
"""

from models import db


class Numerador(db.Model):
    """
    Modelo SQLAlchemy para controlar la numeración de documentos.
    
    Almacena el último número usado para cada tipo de documento
    y proporciona métodos para obtener el siguiente número.
    """
    
    # Nombre de la tabla en la base de datos
    __tablename__ = 'numeradores'
    
    # ==============================================================================
    # COLUMNAS DE LA TABLA
    # ==============================================================================
    
    # Identificador único
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Tipo de documento: 'oferta', 'parte' o 'factura'
    # Es único porque solo puede haber un registro por tipo
    tipo_documento = db.Column(db.String(50), unique=True, nullable=False)
    
    # Último número usado (empieza en 0, el primero será 1)
    ultimo_numero = db.Column(db.Integer, default=0)
    
    # ==============================================================================
    # MÉTODOS ESTÁTICOS
    # ==============================================================================
    
    @staticmethod
    def obtener_siguiente_numero(tipo_documento):
        """
        Obtiene el siguiente número correlativo sin hacer commit.
        El commit se realizará junto con la creación del documento.
        """

        numerador = Numerador.query.filter_by(tipo_documento=tipo_documento).first()

        if numerador is None:
        numerador = Numerador(
            tipo_documento=tipo_documento,
            ultimo_numero=0
            )
        db.session.add(numerador)
        db.session.flush()   # Para asegurarnos de que existe en la sesión

        numerador.ultimo_numero += 1

        numero_formateado = (
        f"{tipo_documento.upper()}-"
        f"{str(numerador.ultimo_numero).zfill(3)}"
        )

        return numero_formateado

    @staticmethod
    def obtener_ultimo_numero(tipo_documento):
        """
        Consulta el último número usado sin incrementarlo.
        
        Útil para mostrar información sin modificar la secuencia.
        
        Parámetros:
            tipo_documento (str): 'oferta', 'parte' o 'factura'
        
        Retorna:
            int: Último número usado, o 0 si no hay registros
        """
        numerador = Numerador.query.filter_by(tipo_documento=tipo_documento).first()
        
        if numerador is None:
            return 0
        
        return numerador.ultimo_numero
    
    def __repr__(self):
        """
        Representación en texto del numerador.
        
        Retorna:
            str: Representación del objeto Numerador
        """
        return f'<Numerador {self.tipo_documento}: {self.ultimo_numero}>'
