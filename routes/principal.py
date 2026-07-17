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

def obtener_facturacion_mensual():
    """
    Calcula la facturación total de los meses con datos (mínimo 6, máximo 24).
    
    Retorna:
        dict: {'etiquetas': ['Ene', 'Feb', ...], 'valores': [1500.00, 2300.00, ...]}
    """
    hoy = datetime.now()
    
    # Buscamos la fecha de la factura más antigua para saber cuántos meses consultar
    factura_antigua = Factura.query.order_by(Factura.fecha.asc()).first()
    
    meses = 6
    if factura_antigua:
        # Calcular diferencia en meses
        diferencia_anios = hoy.year - factura_antigua.fecha.year
        diferencia_meses = hoy.month - factura_antigua.fecha.month
        meses_totales = diferencia_anios * 12 + diferencia_meses + 1
        # Limitamos entre 6 y 24 meses por rendimiento y UX, pero garantizando navegación
        meses = max(6, min(24, meses_totales))
        
    etiquetas = []
    valores = []
    
    # Nombres de meses en español
    nombres_meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                     'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    
    for i in range(meses - 1, -1, -1):
        # Calculamos el mes objetivo (hacia atrás)
        fecha_objetivo = hoy - timedelta(days=i * 30.5)  # Usamos 30.5 días aproximado para evitar saltos de mes incorrectos
        mes = fecha_objetivo.month
        anio = fecha_objetivo.year
        
        # Consulta: suma de facturas de ese mes/año
        total_mes = db.session.query(func.sum(Factura.total)).filter(
            extract('month', Factura.fecha) == mes,
            extract('year', Factura.fecha) == anio
        ).scalar()
        
        # Si no hay facturas, el total es 0
        total_mes = float(total_mes) if total_mes else 0.0
        
        # Etiqueta en formato "Mes AÑO" (ej: "Ene 26")
        etiqueta_mes = f"{nombres_meses[mes - 1]} {str(anio)[2:]}"
        etiquetas.append(etiqueta_mes)
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
    
    # Facturas cuya fecha es anterior al límite y no están cobradas (pagada == False)
    facturas_vencidas = Factura.query.filter(
        Factura.fecha < fecha_limite,
        Factura.pagada == False
    ).order_by(Factura.fecha.asc()).all()
    
    return facturas_vencidas


def obtener_kpis_facturacion():
    """
    Calcula KPIs de facturación: total mes actual, total año actual y ticket medio.
    
    Retorna:
        dict: {'total_mes_actual': X, 'total_anio_actual': Y, 'ticket_medio': Z}
    """
    hoy = datetime.now()
    
    # Total facturado este mes
    total_mes = db.session.query(func.sum(Factura.total)).filter(
        extract('month', Factura.fecha) == hoy.month,
        extract('year', Factura.fecha) == hoy.year
    ).scalar()
    total_mes = float(total_mes) if total_mes else 0.0
    
    # Total facturado este año
    total_anio = db.session.query(func.sum(Factura.total)).filter(
        extract('year', Factura.fecha) == hoy.year
    ).scalar()
    total_anio = float(total_anio) if total_anio else 0.0
    
    # Ticket medio (total / número de facturas)
    num_facturas = Factura.query.count()
    total_global = db.session.query(func.sum(Factura.total)).scalar()
    total_global = float(total_global) if total_global else 0.0
    
    ticket_medio = 0.0
    if num_facturas > 0:
        ticket_medio = round(total_global / num_facturas, 2)
    
    return {
        'total_mes_actual': round(total_mes, 2),
        'total_anio_actual': round(total_anio, 2),
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
    
    # Datos para gráficas (obtener todos los meses con datos)
    facturacion_mensual = obtener_facturacion_mensual()
    estados_ofertas = obtener_estados_ofertas()
    
    # Facturas vencidas (más de 30 días y no pagadas)
    facturas_vencidas = obtener_facturas_vencidas(30)
    
    # KPIs
    kpis = obtener_kpis_facturacion()
    
    return render_template('dashboard.html',
                           estadisticas=estadisticas,
                           facturacion_mensual=facturacion_mensual,
                           estados_ofertas=estados_ofertas,
                           facturas_vencidas=facturas_vencidas,
                           kpis=kpis)
