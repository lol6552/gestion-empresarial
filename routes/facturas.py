# -*- coding: utf-8 -*-
"""
routes/facturas.py - Rutas para gestión de Facturas

Contiene todas las rutas CRUD para facturas con tabla de partidas/conceptos.
"""

import os
from datetime import datetime, date
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file

from models import db, Cliente, Oferta, OfertaPartida, ParteTrabajo, PartePartida, Factura, FacturaPartida, Numerador
from config import IVA_PORCENTAJE, AUTONOMO, INSTANCE_DIR, FORMAS_PAGO, BASE_DIR

# ==============================================================================
# CONFIGURACIÓN DEL BLUEPRINT
# ==============================================================================

facturas_bp = Blueprint('facturas', __name__, url_prefix='/facturas')


# ==============================================================================
# LISTAR FACTURAS
# ==============================================================================

@facturas_bp.route('/')
def lista():
    """Muestra la lista de todas las facturas."""
    termino = request.args.get('q', '').strip()
    fecha_desde = request.args.get('fecha_desde', '').strip()
    fecha_hasta = request.args.get('fecha_hasta', '').strip()
    forma_pago_filtro = request.args.get('forma_pago', '').strip()
    
    query = Factura.query.join(Cliente)
    
    if termino:
        from sqlalchemy import or_
        query = query.filter(or_(
            Cliente.nombre.ilike(f'%{termino}%'),
            Cliente.apellido.ilike(f'%{termino}%'),
            Factura.numero.ilike(f'%{termino}%')
        ))
    
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            query = query.filter(Factura.fecha >= fecha_desde_dt)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            query = query.filter(Factura.fecha <= fecha_hasta_dt)
        except ValueError:
            pass
    
    if forma_pago_filtro:
        query = query.filter(Factura.forma_pago == forma_pago_filtro)
    
    facturas = query.order_by(Factura.fecha.desc()).all()
    
    return render_template('facturas/lista.html', 
                           facturas=facturas, 
                           busqueda=termino,
                           fecha_desde=fecha_desde,
                           fecha_hasta=fecha_hasta,
                           forma_pago_filtro=forma_pago_filtro)


# ==============================================================================
# CREAR FACTURA MANUAL
# ==============================================================================

@facturas_bp.route('/nueva', methods=['GET', 'POST'])
def nueva():
    """Crea una nueva factura manual."""
    clientes = Cliente.query.order_by(Cliente.apellido.asc()).all()
    
    if request.method == 'POST':
        return _procesar_formulario_factura(request.form, clientes)
    
    return render_template('facturas/formulario.html',
                           clientes=clientes,
                           factura=None,
                           datos=None,
                           origen=None,
                           fecha_hoy=date.today().isoformat())


# ==============================================================================
# CREAR FACTURA DESDE OFERTA
# ==============================================================================

@facturas_bp.route('/desde-oferta/<int:oferta_id>', methods=['GET', 'POST'])
def desde_oferta(oferta_id):
    """Crea una factura a partir de una oferta con sus partidas."""
    oferta = Oferta.query.get_or_404(oferta_id)
    clientes = Cliente.query.order_by(Cliente.apellido.asc()).all()
    
    if request.method == 'POST':
        return _procesar_formulario_factura(request.form, clientes, oferta_id=oferta_id)
    
    # Pre-cargar partidas de la oferta
    partidas_oferta = oferta.partidas.order_by(OfertaPartida.orden).all()
    partidas_precargadas = [
        {'descripcion': p.descripcion, 'cantidad': str(p.cantidad), 'precio': str(p.precio), 'total': str(p.total)}
        for p in partidas_oferta
    ]
    
    datos_precargados = {
        'cliente_id': str(oferta.cliente_id),
        'descripcion': f'Según oferta {oferta.numero}',
        'forma_pago': oferta.forma_pago or ''
    }
    
    return render_template('facturas/formulario.html',
                           clientes=clientes,
                           factura=None,
                           datos=datos_precargados,
                           partidas_precargadas=partidas_precargadas,
                           origen={'tipo': 'oferta', 'id': oferta_id, 'numero': oferta.numero},
                           fecha_hoy=date.today().isoformat())


# ==============================================================================
# CREAR FACTURA DESDE PARTE
# ==============================================================================

@facturas_bp.route('/desde-parte/<int:parte_id>', methods=['GET', 'POST'])
def desde_parte(parte_id):
    """Crea una factura a partir de un parte de trabajo con desglose."""
    parte = ParteTrabajo.query.get_or_404(parte_id)
    clientes = Cliente.query.order_by(Cliente.apellido.asc()).all()
    
    if request.method == 'POST':
        return _procesar_formulario_factura(request.form, clientes, parte_id=parte_id)
    
    # Pre-cargar partidas del parte
    partidas_precargadas = []
    
    # Materiales del parte
    partidas_parte = parte.partidas.order_by(PartePartida.orden).all()
    for p in partidas_parte:
        partidas_precargadas.append({
            'descripcion': p.descripcion,
            'cantidad': str(p.cantidad),
            'precio': str(p.precio),
            'total': str(p.total)
        })
    
    # Mano de obra
    partidas_precargadas.append({
        'descripcion': f'Mano de obra ({parte.horas_trabajo}h)',
        'cantidad': str(parte.horas_trabajo),
        'precio': str(parte.precio_hora_trabajo),
        'total': str(parte.subtotal_trabajo)
    })
    
    # Desplazamiento
    if parte.incluye_desplazamiento:
        partidas_precargadas.append({
            'descripcion': f'Desplazamiento ({parte.horas_desplazamiento}h)',
            'cantidad': str(parte.horas_desplazamiento),
            'precio': str(parte.precio_hora_desplazamiento),
            'total': str(parte.subtotal_desplazamiento)
        })
    
    datos_precargados = {
        'cliente_id': str(parte.cliente_id),
        'descripcion': f'Según parte de trabajo {parte.numero}',
        'forma_pago': ''
    }
    
    return render_template('facturas/formulario.html',
                           clientes=clientes,
                           factura=None,
                           datos=datos_precargados,
                           partidas_precargadas=partidas_precargadas,
                           origen={'tipo': 'parte', 'id': parte_id, 'numero': parte.numero},
                           fecha_hoy=date.today().isoformat())


# ==============================================================================
# FUNCIÓN AUXILIAR: PROCESAR FORMULARIO
# ==============================================================================

def _procesar_formulario_factura(form, clientes, oferta_id=None, parte_id=None, factura=None):
    """Procesa el formulario de factura con partidas."""
    cliente_id = form.get('cliente_id', '').strip()
    fecha_str = form.get('fecha', '').strip()
    descripcion = form.get('descripcion', '').strip()
    forma_pago = form.get('forma_pago', '').strip()
    
    # Partidas (arrays)
    partidas_desc = form.getlist('partida_descripcion[]')
    partidas_cantidad = form.getlist('partida_cantidad[]')
    partidas_precio = form.getlist('partida_precio[]')
    
    if not all([cliente_id, fecha_str, forma_pago]):
        flash('Todos los campos marcados con * son obligatorios', 'error')
        return render_template('facturas/formulario.html',
                               clientes=clientes,
                               factura=factura,
                               datos=form,
                               origen=None,
                               fecha_hoy=date.today().isoformat())
    
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
        
        # Procesar partidas
        subtotal = Decimal('0')
        partidas_procesadas = []
        
        for i, desc in enumerate(partidas_desc):
            if desc.strip():
                cantidad = Decimal(partidas_cantidad[i].replace(',', '.')) if partidas_cantidad[i] else Decimal('1')
                precio = Decimal(partidas_precio[i].replace(',', '.')) if partidas_precio[i] else Decimal('0')
                total_partida = cantidad * precio
                subtotal += total_partida
                
                partidas_procesadas.append({
                    'descripcion': desc.strip(),
                    'cantidad': cantidad,
                    'precio': precio,
                    'total': total_partida,
                    'orden': i
                })
        
        # Calcular IVA y total
        iva = subtotal * Decimal(str(IVA_PORCENTAJE)) / Decimal('100')
        total = subtotal + iva
        
        if factura:
            # Editar existente
            factura.cliente_id = int(cliente_id)
            factura.fecha = fecha
            factura.descripcion = descripcion if descripcion else None
            factura.subtotal = subtotal
            factura.iva = iva
            factura.total = total
            factura.forma_pago = forma_pago
            
            # Eliminar partidas antiguas y crear nuevas
            FacturaPartida.query.filter_by(factura_id=factura.id).delete()
            
            for p in partidas_procesadas:
                partida = FacturaPartida(
                    factura_id=factura.id,
                    descripcion=p['descripcion'],
                    cantidad=p['cantidad'],
                    precio=p['precio'],
                    total=p['total'],
                    orden=p['orden']
                )
                db.session.add(partida)
            
            db.session.commit()
            flash('Factura actualizada correctamente', 'success')
        else:
            try:
                # Obtener el siguiente número de factura
                numero_factura = Numerador.obtener_siguiente_numero('factura')

                 # Crear la factura
                nueva_factura = Factura(
                    numero=numero_factura,
                    cliente_id=int(cliente_id),
                    oferta_id=oferta_id,
                    parte_id=parte_id,
                    fecha=fecha,
                    descripcion=descripcion if descripcion else None,
                    subtotal=subtotal,
                    iva=iva,
                    total=total,
                    forma_pago=forma_pago
                )

                db.session.add(nueva_factura)
                db.session.flush()  # Obtiene el ID de la factura sin hacer commit

                # Crear las partidas de la factura
                for p in partidas_procesadas:
                    partida = FacturaPartida(
                        factura_id=nueva_factura.id,
                        descripcion=p['descripcion'],
                        cantidad=p['cantidad'],
                        precio=p['precio'],
                        total=p['total'],
                        orden=p['orden']
                    )
                    db.session.add(partida)

                # Guardar todo junto (numerador + factura + partidas)
                db.session.commit()

                flash('Factura guardada correctamente', 'success')

            except Exception as e:
                db.session.rollback()

                # Opcional: mostrar el error en la consola del servidor
                print(f"Error al guardar la factura: {e}")

                flash('Ha ocurrido un error al guardar la factura.', 'danger')
                return redirect(url_for('facturas.lista'))

        return redirect(url_for('facturas.lista'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al guardar la factura: {str(e)}', 'error')
        return render_template('facturas/formulario.html',
                               clientes=clientes,
                               factura=factura,
                               datos=form,
                               origen=None,
                               fecha_hoy=date.today().isoformat())


# ==============================================================================
# EDITAR FACTURA
# ==============================================================================

@facturas_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    """Edita una factura existente."""
    factura = Factura.query.get_or_404(id)
    clientes = Cliente.query.order_by(Cliente.apellido.asc()).all()
    
    if request.method == 'POST':
        return _procesar_formulario_factura(request.form, clientes, factura=factura)
    
    # Cargar partidas existentes
    partidas_existentes = factura.partidas.order_by(FacturaPartida.orden).all()
    
    return render_template('facturas/formulario.html',
                           clientes=clientes,
                           factura=factura,
                           partidas_existentes=partidas_existentes,
                           datos=None,
                           origen=None,
                           fecha_hoy=date.today().isoformat())


# ==============================================================================
# ELIMINAR FACTURA
# ==============================================================================

@facturas_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar(id):
    """Elimina una factura."""
    factura = Factura.query.get_or_404(id)
    
    try:
        db.session.delete(factura)
        db.session.commit()
        flash('Factura eliminada correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la factura: {str(e)}', 'error')
    
    return redirect(url_for('facturas.lista'))


# ==============================================================================
# GENERAR PDF DE FACTURA
# ==============================================================================

@facturas_bp.route('/pdf/<int:id>')
def generar_pdf(id):
    """
    Genera un archivo PDF de la factura utilizando xhtml2pdf.
    
    NOTA: Se usa xhtml2pdf en lugar de WeasyPrint para garantizar
    compatibilidad en Windows sin instalar librerías GTK3 adicionales.
    """
    factura = Factura.query.get_or_404(id)
    partidas = factura.partidas.order_by(FacturaPartida.orden).all()
    
    # Leer firma y convertir a Base64
    import base64
    firma_path = os.path.join(BASE_DIR, 'static', 'img', 'firma_v2.png')
    firma_b64 = None
    
    if os.path.exists(firma_path):
        with open(firma_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            firma_b64 = f"data:image/png;base64,{encoded_string}"

    # Renderizar plantilla HTML con todos los datos necesarios
    html_content = render_template('facturas/pdf.html',
                                   factura=factura,
                                   partidas=partidas,
                                   autonomo=AUTONOMO,
                                   iva_porcentaje=IVA_PORCENTAJE,
                                   config_formas_pago=FORMAS_PAGO,
                                   url_firma=firma_b64)
    
    # Definir nombre y ruta del archivo
    pdf_filename = f"{factura.numero}.pdf"
    pdf_dir = os.path.join(INSTANCE_DIR, 'pdfs', 'facturas')
    pdf_path = os.path.join(pdf_dir, pdf_filename)
    
    # Asegurar que el directorio existe
    os.makedirs(pdf_dir, exist_ok=True)
    
    try:
        # Generar PDF con Playwright
        from utils.pdf_generator import html_to_pdf
        html_to_pdf(html_content, pdf_path)
        
        # Actualizar ruta en base de datos
        factura.ruta_pdf = pdf_path
        db.session.commit()
        
        # Enviar archivo al usuario
        return send_file(pdf_path, as_attachment=False, download_name=pdf_filename)
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error grave al generar el PDF: {str(e)}', 'error')
        print(f"ERROR PLAYWRIGHT: {e}") 
        return redirect(url_for('facturas.lista'))
