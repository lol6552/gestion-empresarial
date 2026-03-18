# -*- coding: utf-8 -*-
"""
routes/principal.py - Rutas principales de la aplicación

Contiene las rutas generales:
- Dashboard (página de inicio) con gráficas y KPIs
- Información general

Este Blueprint maneja la página principal y estadísticas de negocio.
"""

from flask import Blueprint, render_template
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import func, extract

# Importamos los modelos para obtener estadísticas
from models import db, Cliente, Oferta, ParteTrabajo, Factura

# ==============================================================================
# CONFIGURACIÓN DEL BLUEPRINT
# ==============================================================================

# Creamos el Blueprint 'principal'
principal_bp = Blueprint('principal', __name__)


# ==============================================================================
# FUNCIONES AUXILIARES PARA MÉTRICAS
# ==============================================================================

def obtener_facturacion_mensual(meses=6):
    """
    Calcula la facturación total de los últimos N meses.
    
    Parámetros:
        meses (int): Número de meses a consultar (por defecto 6)
    
    Retorna:
        dict: {'etiquetas': ['Ene', 'Feb', ...], 'valores': [1500.00, 2300.00, ...]}
    """
    hoy = datetime.now()
    etiquetas = []
    valores = []
    
    # Nombres de meses en español
    nombres_meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                     'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    
    for i in range(meses - 1, -1, -1):
        # Calculamos el mes objetivo (hacia atrás)
        fecha_objetivo = hoy - timedelta(days=i * 30)
        mes = fecha_objetivo.month
        anio = fecha_objetivo.year
        
        # Consulta: suma de facturas de ese mes/año
        total_mes = db.session.query(func.sum(Factura.total)).filter(
            extract('month', Factura.fecha) == mes,
            extract('year', Factura.fecha) == anio
        ).scalar()
        
        # Si no hay facturas, el total es 0
        total_mes = float(total_mes) if total_mes else 0.0
        
        etiquetas.append(nombres_meses[mes - 1])
        valores.append(round(total_mes, 2))
    
    return {'etiquetas': etiquetas, 'valores': valores}


def obtener_estados_ofertas():
    """
    Cuenta las ofertas por cada estado.
    
    Retorna:
        dict: {'pendientes': X, 'aceptadas': Y, 'rechazadas': Z, 'tasa_conversion': float}
    """
    pendientes = Oferta.query.filter_by(estado='pendiente').count()
    aceptadas = Oferta.query.filter_by(estado='aceptada').count()
    rechazadas = Oferta.query.filter_by(estado='rechazada').count()
    
    total_decididas = aceptadas + rechazadas
    tasa_conversion = 0.0
    if total_decididas > 0:
        tasa_conversion = round((aceptadas / total_decididas) * 100, 1)
    
    return {
        'pendientes': pendientes,
        'aceptadas': aceptadas,
        'rechazadas': rechazadas,
        'tasa_conversion': tasa_conversion
    }


def obtener_facturas_vencidas(dias_limite=30):
    """
    Obtiene las facturas que tienen más de N días sin cobrar.
    
    Parámetros:
        dias_limite (int): Días después de los cuales se considera vencida
    
    Retorna:
        list: Lista de facturas vencidas
    """
    fecha_limite = datetime.now() - timedelta(days=dias_limite)
    
    # Facturas cuya fecha es anterior al límite
    # NOTA: Aquí asumimos que todas las facturas listadas están pendientes de cobro.
    # Para un sistema real, se añadiría un campo 'pagada' al modelo Factura.
    facturas_vencidas = Factura.query.filter(
        Factura.fecha < fecha_limite
    ).order_by(Factura.fecha.asc()).all()
    
    return facturas_vencidas


def obtener_kpis_facturacion():
    """
    Calcula KPIs de facturación: total mes actual, ticket medio.
    
    Retorna:
        dict: {'total_mes_actual': X, 'ticket_medio': Y}
    """
    hoy = datetime.now()
    
    # Total facturado este mes
    total_mes = db.session.query(func.sum(Factura.total)).filter(
        extract('month', Factura.fecha) == hoy.month,
        extract('year', Factura.fecha) == hoy.year
    ).scalar()
    total_mes = float(total_mes) if total_mes else 0.0
    
    # Ticket medio (total / número de facturas)
    num_facturas = Factura.query.count()
    total_global = db.session.query(func.sum(Factura.total)).scalar()
    total_global = float(total_global) if total_global else 0.0
    
    ticket_medio = 0.0
    if num_facturas > 0:
        ticket_medio = round(total_global / num_facturas, 2)
    
    return {
        'total_mes_actual': round(total_mes, 2),
        'ticket_medio': ticket_medio
    }


# ==============================================================================
# RUTAS
# ==============================================================================

@principal_bp.route('/')
def dashboard():
    """
    Muestra el dashboard principal con estadísticas, gráficas y KPIs.
    
    Esta es la página de inicio de la aplicación.
    Muestra:
    - Contadores generales
    - Gráfica de facturación mensual
    - Gráfica de estados de ofertas
    - Alertas de facturas vencidas
    - KPIs de negocio
    
    Retorna:
        HTML: Plantilla del dashboard renderizada
    """
    # Contadores básicos
    estadisticas = {
        'total_clientes': Cliente.query.count(),
        'total_ofertas': Oferta.query.count(),
        'total_partes': ParteTrabajo.query.count(),
        'total_facturas': Factura.query.count(),
        'ofertas_pendientes': Oferta.query.filter_by(estado='pendiente').count(),
    }
    
    # Datos para gráficas
    facturacion_mensual = obtener_facturacion_mensual(6)
    estados_ofertas = obtener_estados_ofertas()
    
    # Facturas vencidas (más de 30 días)
    facturas_vencidas = obtener_facturas_vencidas(30)
    
    # KPIs
    kpis = obtener_kpis_facturacion()
    
    return render_template('dashboard.html',
                           estadisticas=estadisticas,
                           facturacion_mensual=facturacion_mensual,
                           estados_ofertas=estados_ofertas,
                           facturas_vencidas=facturas_vencidas,
                           kpis=kpis)
