# -*- coding: utf-8 -*-
"""
routes/ofertas.py - Rutas para gestión de ofertas/presupuestos

Contiene todas las rutas CRUD para ofertas:
- Listar ofertas con filtros
- Crear nueva oferta con partidas
- Editar oferta existente
- Eliminar oferta
- Cambiar estado de oferta
- Generar PDF de oferta

Este Blueprint maneja todas las operaciones relacionadas con ofertas.
"""

import os
from datetime import datetime, date
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app

# Importamos la base de datos, modelos y configuración
from models import db, Cliente, Oferta, OfertaPartida, Numerador
from config import IVA_PORCENTAJE, AUTONOMO, INSTANCE_DIR, FORMAS_PAGO, BASE_DIR

# ==============================================================================
# CONFIGURACIÓN DEL BLUEPRINT
# ==============================================================================

# Creamos el Blueprint 'ofertas'
ofertas_bp = Blueprint('ofertas', __name__, url_prefix='/ofertas')


# ==============================================================================
# LISTAR OFERTAS
# ==============================================================================

@ofertas_bp.route('/')
def lista():
    """
    Muestra la lista de todas las ofertas.
    """
    termino = request.args.get('q', '').strip()
    estado_filtro = request.args.get('estado', '').strip()
    
    query = Oferta.query.join(Cliente)
    
    if termino:
        from sqlalchemy import or_
        query = query.filter(or_(
            Cliente.nombre.ilike(f'%{termino}%'),
            Cliente.apellido.ilike(f'%{termino}%'),
            Oferta.numero.ilike(f'%{termino}%')
        ))
    
    if estado_filtro:
        query = query.filter(Oferta.estado == estado_filtro)
    
    ofertas = query.order_by(Oferta.fecha.desc()).all()
    
    return render_template('ofertas/lista.html', 
                           ofertas=ofertas, 
                           busqueda=termino,
                           estado_filtro=estado_filtro)


# ==============================================================================
# CREAR OFERTA
# ==============================================================================

@ofertas_bp.route('/nueva', methods=['GET', 'POST'])
def nueva():
    """
    Crea una nueva oferta con partidas dinámicas.
    """
    clientes = Cliente.query.order_by(Cliente.apellido.asc()).all()
    
    if request.method == 'POST':
        cliente_id = request.form.get('cliente_id', '').strip()
        fecha_str = request.form.get('fecha', '').strip()
        fecha_vencimiento_str = request.form.get('fecha_vencimiento', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        forma_pago = request.form.get('forma_pago', '').strip()
        
        # Obtener partidas del formulario (arrays)
        partidas_desc = request.form.getlist('partida_descripcion[]')
        partidas_precio = request.form.getlist('partida_precio[]')
        partidas_cantidad = request.form.getlist('partida_cantidad[]')
        
        # Validaciones básicas
        if not cliente_id or not fecha_str:
            flash('El cliente y la fecha son obligatorios', 'error')
            return render_template('ofertas/formulario.html',
                                   clientes=clientes,
                                   oferta=None,
                                   datos=request.form,
                                   fecha_hoy=date.today().isoformat())
        
        if not partidas_desc or len(partidas_desc) == 0 or not partidas_desc[0]:
            flash('Debe añadir al menos una partida', 'error')
            return render_template('ofertas/formulario.html',
                                   clientes=clientes,
                                   oferta=None,
                                   datos=request.form,
                                   fecha_hoy=date.today().isoformat())
        
        # Validar cliente
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            flash('El cliente seleccionado no existe', 'error')
            return render_template('ofertas/formulario.html',
                                   clientes=clientes,
                                   oferta=None,
                                   datos=request.form,
                                   fecha_hoy=date.today().isoformat())
        
        # Convertir fecha
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
            fecha_vencimiento = None
            if fecha_vencimiento_str:
                fecha_vencimiento = datetime.strptime(fecha_vencimiento_str, '%Y-%m-%d')
        except ValueError:
            flash('El formato de fecha no es válido', 'error')
            return render_template('ofertas/formulario.html',
                                   clientes=clientes,
                                   oferta=None,
                                   datos=request.form,
                                   fecha_hoy=date.today().isoformat())
        
        # Procesar partidas y calcular subtotal
        try:
            subtotal = Decimal('0')
            partidas_procesadas = []
            
            for i, desc in enumerate(partidas_desc):
                if desc.strip():  # Solo procesar si tiene descripción
                    precio = Decimal(partidas_precio[i].replace(',', '.')) if partidas_precio[i] else Decimal('0')
                    cantidad = Decimal(partidas_cantidad[i].replace(',', '.')) if partidas_cantidad[i] else Decimal('1')
                    total_partida = precio * cantidad
                    subtotal += total_partida
                    
                    partidas_procesadas.append({
                        'descripcion': desc.strip(),
                        'precio': precio,
                        'cantidad': cantidad,
                        'total': total_partida,
                        'orden': i
                    })
            
            if subtotal <= 0:
                flash('El subtotal debe ser mayor que 0', 'error')
                return render_template('ofertas/formulario.html',
                                       clientes=clientes,
                                       oferta=None,
                                       datos=request.form,
                                       fecha_hoy=date.today().isoformat())
            
            # Calcular IVA y total
            iva = subtotal * Decimal(str(IVA_PORCENTAJE)) / Decimal('100')
            total = subtotal + iva
            
            # Generar número de oferta
            numero_oferta = Numerador.obtener_siguiente_numero('oferta')
            
            # Crear oferta
            nueva_oferta = Oferta(
                numero=numero_oferta,
                cliente_id=int(cliente_id),
                fecha=fecha,
                fecha_vencimiento=fecha_vencimiento,
                descripcion=descripcion if descripcion else None,
                subtotal=subtotal,
                iva=iva,
                total=total,
                forma_pago=forma_pago if forma_pago else None,
                estado='pendiente'
            )
            
            db.session.add(nueva_oferta)
            db.session.flush()  # Para obtener el ID
            
            # Crear partidas
            for partida_data in partidas_procesadas:
                partida = OfertaPartida(
                    oferta_id=nueva_oferta.id,
                    descripcion=partida_data['descripcion'],
                    precio=partida_data['precio'],
                    cantidad=partida_data['cantidad'],
                    total=partida_data['total'],
                    orden=partida_data['orden']
                )
                db.session.add(partida)
            
            db.session.commit()
            
            flash('Oferta guardada correctamente', 'success')
            return redirect(url_for('ofertas.lista'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar la oferta: {str(e)}', 'error')
            return render_template('ofertas/formulario.html',
                                   clientes=clientes,
                                   oferta=None,
                                   datos=request.form,
                                   fecha_hoy=date.today().isoformat())
    
    return render_template('ofertas/formulario.html',
                           clientes=clientes,
                           oferta=None,
                           datos=None,
                           fecha_hoy=date.today().isoformat())


# ==============================================================================
# EDITAR OFERTA
# ==============================================================================

@ofertas_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    """
    Edita una oferta existente con sus partidas.
    """
    oferta = Oferta.query.get_or_404(id)
    clientes = Cliente.query.order_by(Cliente.apellido.asc()).all()
    
    if request.method == 'POST':
        cliente_id = request.form.get('cliente_id', '').strip()
        fecha_str = request.form.get('fecha', '').strip()
        fecha_vencimiento_str = request.form.get('fecha_vencimiento', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        forma_pago = request.form.get('forma_pago', '').strip()
        
        partidas_desc = request.form.getlist('partida_descripcion[]')
        partidas_precio = request.form.getlist('partida_precio[]')
        partidas_cantidad = request.form.getlist('partida_cantidad[]')
        
        if not cliente_id or not fecha_str:
            flash('El cliente y la fecha son obligatorios', 'error')
            return render_template('ofertas/formulario.html',
                                   clientes=clientes,
                                   oferta=oferta,
                                   datos=request.form,
                                   fecha_hoy=date.today().isoformat())
        
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            flash('El cliente seleccionado no existe', 'error')
            return render_template('ofertas/formulario.html',
                                   clientes=clientes,
                                   oferta=oferta,
                                   datos=request.form,
                                   fecha_hoy=date.today().isoformat())
        
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
            fecha_vencimiento = None
            if fecha_vencimiento_str:
                fecha_vencimiento = datetime.strptime(fecha_vencimiento_str, '%Y-%m-%d')
        except ValueError:
            flash('El formato de fecha no es válido', 'error')
            return render_template('ofertas/formulario.html',
                                   clientes=clientes,
                                   oferta=oferta,
                                   datos=request.form,
                                   fecha_hoy=date.today().isoformat())
        
        try:
            # Eliminar partidas antiguas
            OfertaPartida.query.filter_by(oferta_id=oferta.id).delete()
            
            # Procesar nuevas partidas
            subtotal = Decimal('0')
            
            for i, desc in enumerate(partidas_desc):
                if desc.strip():
                    precio = Decimal(partidas_precio[i].replace(',', '.')) if partidas_precio[i] else Decimal('0')
                    cantidad = Decimal(partidas_cantidad[i].replace(',', '.')) if partidas_cantidad[i] else Decimal('1')
                    total_partida = precio * cantidad
                    subtotal += total_partida
                    
                    partida = OfertaPartida(
                        oferta_id=oferta.id,
                        descripcion=desc.strip(),
                        precio=precio,
                        cantidad=cantidad,
                        total=total_partida,
                        orden=i
                    )
                    db.session.add(partida)
            
            iva = subtotal * Decimal(str(IVA_PORCENTAJE)) / Decimal('100')
            total = subtotal + iva
            
            oferta.cliente_id = int(cliente_id)
            oferta.fecha = fecha
            oferta.fecha_vencimiento = fecha_vencimiento
            oferta.descripcion = descripcion if descripcion else None
            oferta.subtotal = subtotal
            oferta.iva = iva
            oferta.total = total
            oferta.forma_pago = forma_pago if forma_pago else None
            
            db.session.commit()
            
            flash('Oferta actualizada correctamente', 'success')
            return redirect(url_for('ofertas.lista'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la oferta: {str(e)}', 'error')
            return render_template('ofertas/formulario.html',
                                   clientes=clientes,
                                   oferta=oferta,
                                   datos=request.form,
                                   fecha_hoy=date.today().isoformat())
    
    return render_template('ofertas/formulario.html',
                           clientes=clientes,
                           oferta=oferta,
                           datos=None,
                           fecha_hoy=date.today().isoformat())


# ==============================================================================
# ELIMINAR OFERTA
# ==============================================================================

@ofertas_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar(id):
    """
    Elimina una oferta del sistema.
    """
    oferta = Oferta.query.get_or_404(id)
    
    if oferta.facturas.count() > 0:
        flash('No se puede eliminar la oferta porque tiene facturas asociadas', 'error')
        return redirect(url_for('ofertas.lista'))
    
    try:
        db.session.delete(oferta)
        db.session.commit()
        flash('Oferta eliminada correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la oferta: {str(e)}', 'error')
    
    return redirect(url_for('ofertas.lista'))


# ==============================================================================
# CAMBIAR ESTADO DE OFERTA
# ==============================================================================

@ofertas_bp.route('/cambiar_estado/<int:id>', methods=['POST'])
def cambiar_estado(id):
    """
    Cambia el estado de una oferta.
    """
    oferta = Oferta.query.get_or_404(id)
    nuevo_estado = request.form.get('estado', '').strip()
    
    if nuevo_estado:
        if nuevo_estado not in ['pendiente', 'aceptada', 'rechazada']:
            flash('Estado no válido', 'error')
            return redirect(url_for('ofertas.lista'))
        oferta.estado = nuevo_estado
    else:
        ciclo_estados = {
            'pendiente': 'aceptada',
            'aceptada': 'rechazada',
            'rechazada': 'pendiente'
        }
        oferta.estado = ciclo_estados.get(oferta.estado, 'pendiente')
    
    try:
        db.session.commit()
        flash(f'Estado cambiado a "{oferta.estado}"', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar el estado: {str(e)}', 'error')
    
    return redirect(url_for('ofertas.lista'))


# ==============================================================================
# GENERAR PDF DE OFERTA
# ==============================================================================

@ofertas_bp.route('/pdf/<int:id>')
def generar_pdf(id):
    """
    Genera un PDF de la oferta usando xhtml2pdf (pisa).
    
    Compatible con Windows sin dependencias externas como GTK.
    El PDF se guarda en disco y su ruta se registra en la base de datos.
    
    Parámetros:
        id (int): Identificador de la oferta
    
    Retorna:
        Archivo PDF para descargar/visualizar
    """
    from xhtml2pdf import pisa
    from io import BytesIO
    
    oferta = Oferta.query.get_or_404(id)
    partidas = oferta.partidas.order_by(OfertaPartida.orden).all()
    
    # Leer firma y convertir a Base64 para incrustar directamente
    import base64
    firma_path = os.path.join(BASE_DIR, 'static', 'img', 'firma_v2.png')
    firma_b64 = None
    
    if os.path.exists(firma_path):
        with open(firma_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            firma_b64 = f"data:image/png;base64,{encoded_string}"

    # Renderizar plantilla HTML para PDF
    html_content = render_template('ofertas/pdf.html',
                                   oferta=oferta,
                                   partidas=partidas,
                                   autonomo=AUTONOMO,
                                   iva_porcentaje=IVA_PORCENTAJE,
                                   config_formas_pago=FORMAS_PAGO,
                                   url_firma=firma_b64)
    
    # Configurar rutas para el PDF
    pdf_filename = f"{oferta.numero}.pdf"
    pdf_path = os.path.join(INSTANCE_DIR, 'pdfs', 'ofertas', pdf_filename)
    
    # Asegurar que el directorio existe
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    
    # Crear PDF usando xhtml2pdf (pisa)
    # Crear PDF usando Playwright
    try:
        from utils.pdf_generator import html_to_pdf
        html_to_pdf(html_content, pdf_path)
        
        # Actualizar ruta en BD
        oferta.ruta_pdf = pdf_path
        db.session.commit()
        
        # Enviar archivo
        return send_file(pdf_path, as_attachment=False, download_name=pdf_filename)
        
    except Exception as e:
        flash(f'Error al generar PDF: {str(e)}', 'error')
        print(f"ERROR PLAYWRIGHT: {e}")
        return redirect(url_for('ofertas.lista'))

