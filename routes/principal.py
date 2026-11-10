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
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo
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

def fecha_actual_madrid():
    """Fecha civil del negocio, independiente de la zona horaria del servidor."""
    return datetime.now(ZoneInfo("Europe/Madrid")).replace(tzinfo=None)


def sumar_importe(campo, *filtros):
    """Mantiene Decimal hasta la presentación; los periodos son [inicio, fin)."""
    valor = db.session.query(func.sum(campo)).filter(*filtros).scalar()
    return (valor or Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def obtener_facturacion_mensual(hoy=None):
    """
    Calcula la facturación total de los meses con datos (mínimo 6, máximo 24).
    
    Retorna:
        dict: {'etiquetas': ['Ene', 'Feb', ...], 'valores': [1500.00, 2300.00, ...]}
    """
    hoy = hoy if hoy is not None else fecha_actual_madrid()
    
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
        # Restar meses naturales evita saltar febrero o repetir meses de 31 días.
        indice_mes = hoy.year * 12 + hoy.month - 1 - i
        anio, mes_desde_cero = divmod(indice_mes, 12)
        mes = mes_desde_cero + 1
        
        # Consulta: suma de facturas de ese mes/año
        total_mes = sumar_importe(
            Factura.subtotal,
            extract('month', Factura.fecha) == mes,
            extract('year', Factura.fecha) == anio
        )

        # Etiqueta en formato "Mes AÑO" (ej: "Ene 26")
        etiqueta_mes = f"{nombres_meses[mes - 1]} {str(anio)[2:]}"
        etiquetas.append(etiqueta_mes)
        valores.append(float(total_mes))
    
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


def obtener_kpis_facturacion(hoy=None):
    """Bases sin IVA por fecha de emisión e IVA real del trimestre natural.

    Todas las facturas emitidas cuentan, tanto pagadas como pendientes.
    El modelo actual no tiene estados de borrador, anulación o rectificación.
    """
    hoy = hoy if hoy is not None else fecha_actual_madrid()
    inicio_mes = datetime(hoy.year, hoy.month, 1)
    fin_mes = datetime(hoy.year + (hoy.month == 12), hoy.month % 12 + 1, 1)
    inicio_anio = datetime(hoy.year, 1, 1)
    fin_anio = datetime(hoy.year + 1, 1, 1)
    trimestre = (hoy.month - 1) // 3 + 1
    inicio_trimestre = datetime(hoy.year, 3 * trimestre - 2, 1)
    fin_trimestre = (datetime(hoy.year + 1, 1, 1) if trimestre == 4
                     else datetime(hoy.year, 3 * trimestre + 1, 1))
    num_facturas = Factura.query.count()
    total_global = sumar_importe(Factura.subtotal)
    ticket_medio = ((total_global / num_facturas).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP) if num_facturas else Decimal("0.00"))
    # Solo el mes ordinario: los vencimientos dependen de calendario y modalidad.
    # https://sede.agenciatributaria.gob.es/Sede/iva/presentar-declaracion-iva-modelo-303/plazo-presentacion-modelo-303.html
    mes_presentacion = ("abril", "julio", "octubre", "enero")[trimestre - 1]
    return {
        'total_mes_actual': sumar_importe(Factura.subtotal, Factura.fecha >= inicio_mes,
                                          Factura.fecha < fin_mes),
        'total_anio_actual': sumar_importe(Factura.subtotal, Factura.fecha >= inicio_anio,
                                           Factura.fecha < fin_anio),
        'ticket_medio': ticket_medio,
        'hucha_iva': sumar_importe(Factura.iva, Factura.fecha >= inicio_trimestre,
                                  Factura.fecha < fin_trimestre),
        'trimestre': trimestre,
        'anio': hoy.year,
        'mes_presentacion': mes_presentacion,
        'anio_presentacion': hoy.year + (trimestre == 4),
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
    hoy = fecha_actual_madrid()
    facturacion_mensual = obtener_facturacion_mensual(hoy)
    estados_ofertas = obtener_estados_ofertas()
    
    # Facturas vencidas (más de 30 días y no pagadas)
    facturas_vencidas = obtener_facturas_vencidas(30)
    
    # KPIs
    kpis = obtener_kpis_facturacion(hoy)
    
    return render_template('dashboard.html',
                           estadisticas=estadisticas,
                           facturacion_mensual=facturacion_mensual,
                           estados_ofertas=estados_ofertas,
                           facturas_vencidas=facturas_vencidas,
                           kpis=kpis)
