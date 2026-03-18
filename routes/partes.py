# -*- coding: utf-8 -*-
"""
routes/partes.py - Rutas para gestión de Partes de Trabajo

Contiene todas las rutas CRUD para partes de trabajo:
- Listar partes con filtros
- Crear nuevo parte con partidas de materiales
- Editar parte existente
- Eliminar parte
- Generar PDF de parte

Este Blueprint maneja todas las operaciones relacionadas con partes de trabajo.
"""

import os
from datetime import datetime, date, time
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file

# Importamos la base de datos, modelos y configuración
from models import db, Cliente, ParteTrabajo, PartePartida, Numerador
from config import IVA_PORCENTAJE, AUTONOMO, INSTANCE_DIR, FORMAS_PAGO

# ==============================================================================
# CONFIGURACIÓN DEL BLUEPRINT
# ==============================================================================

partes_bp = Blueprint('partes', __name__, url_prefix='/partes')


# ==============================================================================
# LISTAR PARTES
# ==============================================================================

@partes_bp.route('/')
def lista():
    """
    Muestra la lista de todos los partes de trabajo.
    """
    termino = request.args.get('q', '').strip()
    fecha_desde = request.args.get('fecha_desde', '').strip()
    fecha_hasta = request.args.get('fecha_hasta', '').strip()
    
    query = ParteTrabajo.query.join(Cliente)
    
    if termino:
        from sqlalchemy import or_
        query = query.filter(or_(
            Cliente.nombre.ilike(f'%{termino}%'),
            Cliente.apellido.ilike(f'%{termino}%'),
            ParteTrabajo.numero.ilike(f'%{termino}%')
        ))
    
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            query = query.filter(ParteTrabajo.fecha_realizacion >= fecha_desde_dt)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            query = query.filter(ParteTrabajo.fecha_realizacion <= fecha_hasta_dt)
        except ValueError:
            pass
    
    partes = query.order_by(ParteTrabajo.fecha_realizacion.desc()).all()
    
    return render_template('partes/lista.html', 
                           partes=partes, 
                           busqueda=termino,
                           fecha_desde=fecha_desde,
                           fecha_hasta=fecha_hasta)


# ==============================================================================
# CREAR PARTE
# ==============================================================================

@partes_bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo():
    """
    Crea un nuevo parte de trabajo con partidas de materiales.
    """
    clientes = Cliente.query.order_by(Cliente.apellido.asc()).all()
    
    if request.method == 'POST':
        cliente_id = request.form.get('cliente_id', '').strip()
        fecha_str = request.form.get('fecha_realizacion', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        
        # Control horario
        hora_inicio_str = request.form.get('hora_inicio', '').strip()
        hora_fin_str = request.form.get('hora_fin', '').strip()
        precio_hora_trabajo_str = request.form.get('precio_hora_trabajo', '').strip()
        
        # Desplazamiento
        horas_desplazamiento_str = request.form.get('horas_desplazamiento', '0').strip()
        precio_hora_desplazamiento_str = request.form.get('precio_hora_desplazamiento', '0').strip()
        
        # Partidas de materiales (arrays)
        partidas_desc = request.form.getlist('partida_descripcion[]')
        partidas_cantidad = request.form.getlist('partida_cantidad[]')
        partidas_precio = request.form.getlist('partida_precio[]')
        
        # Validaciones básicas
        if not all([cliente_id, fecha_str, hora_inicio_str, hora_fin_str, precio_hora_trabajo_str]):
            flash('Los campos marcados con * son obligatorios', 'error')
            return render_template('partes/formulario.html',
                                   clientes=clientes,
                                   parte=None,
                                   datos=request.form,
                                   fecha_hoy=date.today().isoformat())
        
        # Validar cliente
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            flash('El cliente seleccionado no existe', 'error')
            return render_template('partes/formulario.html',
                                   clientes=clientes,
                                   parte=None,
                                   datos=request.form,
                                   fecha_hoy=date.today().isoformat())
        
        try:
            # Convertir datos
            fecha_realizacion = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
            hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()
            precio_hora_trabajo = Decimal(precio_hora_trabajo_str.replace(',', '.'))
            
            horas_desplazamiento = Decimal(horas_desplazamiento_str.replace(',', '.')) if horas_desplazamiento_str else Decimal('0')
            precio_hora_desplazamiento = Decimal(precio_hora_desplazamiento_str.replace(',', '.')) if precio_hora_desplazamiento_str else Decimal('0')
            
            # Validar hora_fin > hora_inicio
            if hora_fin <= hora_inicio:
                flash('La hora de fin debe ser posterior a la hora de inicio', 'error')
                return render_template('partes/formulario.html',
                                       clientes=clientes,
                                       parte=None,
                                       datos=request.form,
                                       fecha_hoy=date.today().isoformat())
            
            # Calcular horas de trabajo
            horas_trabajo = ParteTrabajo.calcular_horas_trabajo(hora_inicio, hora_fin)
            
            # Procesar partidas de materiales
            materiales_importe = Decimal('0')
            partidas_procesadas = []
            
            for i, desc in enumerate(partidas_desc):
                if desc.strip():
                    cantidad = Decimal(partidas_cantidad[i].replace(',', '.')) if partidas_cantidad[i] else Decimal('1')
                    precio = Decimal(partidas_precio[i].replace(',', '.')) if partidas_precio[i] else Decimal('0')
                    total_partida = cantidad * precio
                    materiales_importe += total_partida
                    
                    partidas_procesadas.append({
                        'descripcion': desc.strip(),
                        'cantidad': cantidad,
                        'precio': precio,
                        'total': total_partida,
                        'orden': i
                    })
            
            # Calcular subtotales
            subtotal_trabajo = horas_trabajo * precio_hora_trabajo
            subtotal_desplazamiento = horas_desplazamiento * precio_hora_desplazamiento
            subtotal_general = subtotal_trabajo + subtotal_desplazamiento + materiales_importe
            
            # Calcular IVA y total
            iva = subtotal_general * Decimal(str(IVA_PORCENTAJE)) / Decimal('100')
            total = subtotal_general + iva
            
            # Generar número de parte
            numero_parte = Numerador.obtener_siguiente_numero('parte')
            
            # Crear parte
            nuevo_parte = ParteTrabajo(
                numero=numero_parte,
                cliente_id=int(cliente_id),
                fecha_realizacion=fecha_realizacion,
                descripcion=descripcion,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                horas_trabajo=horas_trabajo,
                precio_hora_trabajo=precio_hora_trabajo,
                subtotal_trabajo=subtotal_trabajo,
                horas_desplazamiento=horas_desplazamiento,
                precio_hora_desplazamiento=precio_hora_desplazamiento,
                subtotal_desplazamiento=subtotal_desplazamiento,
                materiales_descripcion=None,
                materiales_importe=materiales_importe,
                subtotal_general=subtotal_general,
                iva=iva,
                total=total
            )
            
            db.session.add(nuevo_parte)
            db.session.flush()
            
            # Crear partidas de materiales
            for partida_data in partidas_procesadas:
                partida = PartePartida(
                    parte_id=nuevo_parte.id,
                    descripcion=partida_data['descripcion'],
                    cantidad=partida_data['cantidad'],
                    precio=partida_data['precio'],
                    total=partida_data['total'],
                    orden=partida_data['orden']
                )
                db.session.add(partida)
            
            db.session.commit()
            
            flash('Parte de trabajo guardado correctamente', 'success')
            return redirect(url_for('partes.lista'))
            
        except ValueError as e:
            flash(f'Error en los datos: {str(e)}', 'error')
            return render_template('partes/formulario.html',
                                   clientes=clientes,
                                   parte=None,
                                   datos=request.form,
                                   fecha_hoy=date.today().isoformat())
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar el parte: {str(e)}', 'error')
            return render_template('partes/formulario.html',
                                   clientes=clientes,
                                   parte=None,
                                   datos=request.form,
                                   fecha_hoy=date.today().isoformat())
    
    return render_template('partes/formulario.html',
                           clientes=clientes,
                           parte=None,
                           datos=None,
                           fecha_hoy=date.today().isoformat())


# ==============================================================================
# EDITAR PARTE
# ==============================================================================

@partes_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    """
    Edita un parte de trabajo existente con sus partidas.
    """
    parte = ParteTrabajo.query.get_or_404(id)
    clientes = Cliente.query.order_by(Cliente.apellido.asc()).all()
    
    if request.method == 'POST':
        cliente_id = request.form.get('cliente_id', '').strip()
        fecha_str = request.form.get('fecha_realizacion', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        
        hora_inicio_str = request.form.get('hora_inicio', '').strip()
        hora_fin_str = request.form.get('hora_fin', '').strip()
        precio_hora_trabajo_str = request.form.get('precio_hora_trabajo', '').strip()
        
        horas_desplazamiento_str = request.form.get('horas_desplazamiento', '0').strip()
        precio_hora_desplazamiento_str = request.form.get('precio_hora_desplazamiento', '0').strip()
        
        # Partidas de materiales (arrays)
        partidas_desc = request.form.getlist('partida_descripcion[]')
        partidas_cantidad = request.form.getlist('partida_cantidad[]')
        partidas_precio = request.form.getlist('partida_precio[]')
        
        try:
            fecha_realizacion = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
            hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()
            precio_hora_trabajo = Decimal(precio_hora_trabajo_str.replace(',', '.'))
            
            horas_desplazamiento = Decimal(horas_desplazamiento_str.replace(',', '.')) if horas_desplazamiento_str else Decimal('0')
            precio_hora_desplazamiento = Decimal(precio_hora_desplazamiento_str.replace(',', '.')) if precio_hora_desplazamiento_str else Decimal('0')
            
            if hora_fin <= hora_inicio:
                flash('La hora de fin debe ser posterior a la hora de inicio', 'error')
                return render_template('partes/formulario.html',
                                       clientes=clientes,
                                       parte=parte,
                                       datos=request.form,
                                       fecha_hoy=date.today().isoformat())
            
            # Eliminar partidas antiguas
            PartePartida.query.filter_by(parte_id=parte.id).delete()
            
            # Procesar nuevas partidas
            materiales_importe = Decimal('0')
            
            for i, desc in enumerate(partidas_desc):
                if desc.strip():
                    cantidad = Decimal(partidas_cantidad[i].replace(',', '.')) if partidas_cantidad[i] else Decimal('1')
                    precio = Decimal(partidas_precio[i].replace(',', '.')) if partidas_precio[i] else Decimal('0')
                    total_partida = cantidad * precio
                    materiales_importe += total_partida
                    
                    partida = PartePartida(
                        parte_id=parte.id,
                        descripcion=desc.strip(),
                        cantidad=cantidad,
                        precio=precio,
                        total=total_partida,
                        orden=i
                    )
                    db.session.add(partida)
            
            horas_trabajo = ParteTrabajo.calcular_horas_trabajo(hora_inicio, hora_fin)
            subtotal_trabajo = horas_trabajo * precio_hora_trabajo
            subtotal_desplazamiento = horas_desplazamiento * precio_hora_desplazamiento
            subtotal_general = subtotal_trabajo + subtotal_desplazamiento + materiales_importe
            iva = subtotal_general * Decimal(str(IVA_PORCENTAJE)) / Decimal('100')
            total = subtotal_general + iva
            
            # Actualizar parte
            parte.cliente_id = int(cliente_id)
            parte.fecha_realizacion = fecha_realizacion
            parte.descripcion = descripcion
            parte.hora_inicio = hora_inicio
            parte.hora_fin = hora_fin
            parte.horas_trabajo = horas_trabajo
            parte.precio_hora_trabajo = precio_hora_trabajo
            parte.subtotal_trabajo = subtotal_trabajo
            parte.horas_desplazamiento = horas_desplazamiento
            parte.precio_hora_desplazamiento = precio_hora_desplazamiento
            parte.subtotal_desplazamiento = subtotal_desplazamiento
            parte.materiales_importe = materiales_importe
            parte.subtotal_general = subtotal_general
            parte.iva = iva
            parte.total = total
            
            db.session.commit()
            
            flash('Parte de trabajo actualizado correctamente', 'success')
            return redirect(url_for('partes.lista'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el parte: {str(e)}', 'error')
            return render_template('partes/formulario.html',
                                   clientes=clientes,
                                   parte=parte,
                                   datos=request.form,
                                   fecha_hoy=date.today().isoformat())
    
    return render_template('partes/formulario.html',
                           clientes=clientes,
                           parte=parte,
                           datos=None,
                           fecha_hoy=date.today().isoformat())


# ==============================================================================
# ELIMINAR PARTE
# ==============================================================================

@partes_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar(id):
    """
    Elimina un parte de trabajo del sistema.
    """
    parte = ParteTrabajo.query.get_or_404(id)
    
    if parte.facturas.count() > 0:
        flash('No se puede eliminar el parte porque tiene facturas asociadas', 'error')
        return redirect(url_for('partes.lista'))
    
    try:
        db.session.delete(parte)
        db.session.commit()
        flash('Parte eliminado correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el parte: {str(e)}', 'error')
    
    return redirect(url_for('partes.lista'))


# ==============================================================================
# GENERAR PDF DE PARTE
# ==============================================================================

@partes_bp.route('/pdf/<int:id>')
def generar_pdf(id):
    """
    Genera un PDF del parte de trabajo usando xhtml2pdf.
    """
    parte = ParteTrabajo.query.get_or_404(id)
    partidas = parte.partidas.order_by(PartePartida.orden).all()
    
    # Renderizar plantilla HTML para PDF
    html_content = render_template('partes/pdf.html',
                                   parte=parte,
                                   partidas=partidas,
                                   autonomo=AUTONOMO,
                                   iva_porcentaje=IVA_PORCENTAJE,
                                   config_formas_pago=FORMAS_PAGO)
    
    # Configurar rutas
    pdf_filename = f"{parte.numero}.pdf"
    pdf_path = os.path.join(INSTANCE_DIR, 'pdfs', 'partes', pdf_filename)
    
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    
    try:
        from utils.pdf_generator import html_to_pdf
        html_to_pdf(html_content, pdf_path)
        
        parte.ruta_pdf = pdf_path
        db.session.commit()
        
        return send_file(pdf_path, as_attachment=False, download_name=pdf_filename)
        
    except Exception as e:
        flash(f'Error al generar PDF: {str(e)}', 'error')
        print(f"ERROR PLAYWRIGHT: {e}")
        return redirect(url_for('partes.lista'))
