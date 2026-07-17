# -*- coding: utf-8 -*-
"""
routes/clientes.py - Rutas para gestión de clientes

Contiene todas las rutas CRUD para clientes:
- Listar clientes
- Crear nuevo cliente
- Editar cliente existente
- Eliminar cliente

Este Blueprint maneja todas las operaciones relacionadas con clientes.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash

# Importamos la base de datos, modelo Cliente y Numerador
from models import db, Cliente, Numerador

# Importamos la función de ordenación reutilizable
from utils.ordenacion import aplicar_ordenacion

# ==============================================================================
# CONFIGURACIÓN DEL BLUEPRINT
# ==============================================================================

# Creamos el Blueprint 'clientes'
# url_prefix='/clientes' significa que todas las rutas empezarán con /clientes
clientes_bp = Blueprint('clientes', __name__, url_prefix='/clientes')

# ==============================================================================
# CAMPOS ORDENABLES PARA CLIENTES
# ==============================================================================

# Lista blanca de campos por los que se puede ordenar la tabla de clientes.
# La clave es el valor que llega por GET (?sort=nombre),
# el valor es la columna real del modelo SQLAlchemy.
CAMPOS_ORDENABLES_CLIENTES = {
    'codigo': Cliente.codigo,
    'nombre': Cliente.apellido,       # Ordenar por "Nombre" usa el apellido
    'dni': Cliente.dni,
    'telefono': Cliente.telefono,
    'localidad': Cliente.localidad,
    'trabajo': Cliente.trabajo_a_realizar,
}


# ==============================================================================
# LISTAR CLIENTES
# ==============================================================================

@clientes_bp.route('/')
def lista():
    """
    Muestra la lista de todos los clientes.
    
    Permite filtrar por un término de búsqueda (nombre, id/código, teléfono).
    Permite ordenar por columna haciendo clic en los encabezados.
    
    Parámetros GET:
        q (str): Término de búsqueda
        sort (str): Campo por el que ordenar (codigo, nombre, dni, telefono, localidad, trabajo)
        order (str): Dirección de la ordenación (asc o desc)
    
    Retorna:
        HTML: Plantilla con la tabla de clientes
    """
    # Obtenemos el término de búsqueda desde la URL (?q=termino)
    termino = request.args.get('q', '').strip()
    
    # Obtenemos los parámetros de ordenación desde la URL
    sort_key = request.args.get('sort', '').strip()
    order = request.args.get('order', 'asc').strip()
    
    # Consulta base
    query = Cliente.query
    
    # Si hay un término de búsqueda, aplicamos filtros
    if termino:
        # Importamos or_ para búsquedas múltiples
        from sqlalchemy import or_
        
        # Filtramos por nombre, apellido, código, dni o teléfono
        # ilike hace la búsqueda insensible a mayúsculas/minúsculas
        query = query.filter(or_(
            Cliente.nombre.ilike(f'%{termino}%'),
            Cliente.apellido.ilike(f'%{termino}%'),
            Cliente.codigo.ilike(f'%{termino}%'),
            Cliente.dni.ilike(f'%{termino}%'),
            Cliente.telefono.ilike(f'%{termino}%')
        ))
    
    # Aplicamos la ordenación dinámica (validada contra lista blanca)
    query = aplicar_ordenacion(query, sort_key, order, CAMPOS_ORDENABLES_CLIENTES)
    
    # Si no se pidió ordenación específica, usamos el orden por defecto (apellido)
    if sort_key not in CAMPOS_ORDENABLES_CLIENTES:
        query = query.order_by(Cliente.apellido.asc())
    
    # Obtenemos todos los clientes
    clientes = query.all()
    
    # Renderizamos la plantilla pasando también sort/order para los encabezados
    return render_template('clientes/lista.html', 
                           clientes=clientes, 
                           busqueda=termino,
                           sort_actual=sort_key,
                           order_actual=order)


# ==============================================================================
# CREAR CLIENTE
# ==============================================================================

@clientes_bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo():
    """
    Crea un nuevo cliente.
    
    GET: Muestra el formulario vacío
    POST: Procesa el formulario y guarda el cliente
    
    Retorna:
        GET: HTML del formulario vacío
        POST: Redirección a la lista (si éxito) o formulario con errores
    """
    # Si es una petición POST, procesamos el formulario
    if request.method == 'POST':
        # Recogemos los datos del formulario
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        dni = request.form.get('dni', '').strip().upper()
        telefono = request.form.get('telefono', '').strip()
        email = request.form.get('email', '').strip()
        direccion = request.form.get('direccion', '').strip()
        codigo_postal = request.form.get('codigo_postal', '').strip()
        localidad = request.form.get('localidad', '').strip()
        trabajo_a_realizar = request.form.get('trabajo_a_realizar', '').strip()
        
        # Validamos campos obligatorios
        if not all([nombre, apellido, dni, telefono, direccion, codigo_postal, localidad]):
            flash('Todos los campos marcados con * son obligatorios', 'error')
            return render_template('clientes/formulario.html', 
                                   cliente=None, 
                                   datos=request.form)
        
        # Verificamos que el DNI no exista ya
        cliente_existente = Cliente.query.filter_by(dni=dni).first()
        if cliente_existente:
            flash(f'Ya existe un cliente con el DNI {dni}', 'error')
            return render_template('clientes/formulario.html', 
                                   cliente=None, 
                                   datos=request.form)
        
        # Creamos el nuevo cliente
        try:
            nuevo_cliente = Cliente(
                nombre=nombre,
                apellido=apellido,
                dni=dni,
                telefono=telefono,
                email=email if email else None,
                direccion=direccion,
                codigo_postal=codigo_postal,
                localidad=localidad,
                trabajo_a_realizar=trabajo_a_realizar if trabajo_a_realizar else None
            )
            
            # Guardamos en la base de datos
            db.session.add(nuevo_cliente)
            db.session.flush()  # Obtener el ID sin hacer commit todavía
            
            # Generamos el código de cliente (CLI-001, CLI-002, etc.)
            nuevo_cliente.codigo = Numerador.obtener_siguiente_numero('cliente')
            
            db.session.commit()
            
            flash('Cliente guardado correctamente', 'success')
            return redirect(url_for('clientes.lista'))
            
        except Exception as e:
            # Si hay error, deshacemos los cambios
            db.session.rollback()
            flash(f'Error al guardar el cliente: {str(e)}', 'error')
            return render_template('clientes/formulario.html', 
                                   cliente=None, 
                                   datos=request.form)
    
    # Si es GET, mostramos el formulario vacío
    return render_template('clientes/formulario.html', cliente=None, datos=None)


# ==============================================================================
# EDITAR CLIENTE
# ==============================================================================

@clientes_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    """
    Edita un cliente existente.
    
    Parámetros:
        id (int): Identificador del cliente a editar
    
    GET: Muestra el formulario con los datos actuales
    POST: Procesa el formulario y actualiza el cliente
    
    Retorna:
        GET: HTML del formulario con datos
        POST: Redirección a la lista (si éxito) o formulario con errores
    """
    # Buscamos el cliente o mostramos error 404
    cliente = Cliente.query.get_or_404(id)
    
    # Si es una petición POST, procesamos el formulario
    if request.method == 'POST':
        # Recogemos los datos del formulario
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        dni = request.form.get('dni', '').strip().upper()
        telefono = request.form.get('telefono', '').strip()
        email = request.form.get('email', '').strip()
        direccion = request.form.get('direccion', '').strip()
        codigo_postal = request.form.get('codigo_postal', '').strip()
        localidad = request.form.get('localidad', '').strip()
        trabajo_a_realizar = request.form.get('trabajo_a_realizar', '').strip()
        
        # Validamos campos obligatorios
        if not all([nombre, apellido, dni, telefono, direccion, codigo_postal, localidad]):
            flash('Todos los campos marcados con * son obligatorios', 'error')
            return render_template('clientes/formulario.html', 
                                   cliente=cliente, 
                                   datos=request.form)
        
        # Verificamos que el DNI no exista en OTRO cliente
        cliente_existente = Cliente.query.filter_by(dni=dni).first()
        if cliente_existente and cliente_existente.id != id:
            flash(f'Ya existe otro cliente con el DNI {dni}', 'error')
            return render_template('clientes/formulario.html', 
                                   cliente=cliente, 
                                   datos=request.form)
        
        # Actualizamos el cliente
        try:
            cliente.nombre = nombre
            cliente.apellido = apellido
            cliente.dni = dni
            cliente.telefono = telefono
            cliente.email = email if email else None
            cliente.direccion = direccion
            cliente.codigo_postal = codigo_postal
            cliente.localidad = localidad
            cliente.trabajo_a_realizar = trabajo_a_realizar if trabajo_a_realizar else None
            
            # Guardamos los cambios
            db.session.commit()
            
            flash('Cliente actualizado correctamente', 'success')
            return redirect(url_for('clientes.lista'))
            
        except Exception as e:
            # Si hay error, deshacemos los cambios
            db.session.rollback()
            flash(f'Error al actualizar el cliente: {str(e)}', 'error')
            return render_template('clientes/formulario.html', 
                                   cliente=cliente, 
                                   datos=request.form)
    
    # Si es GET, mostramos el formulario con datos del cliente
    return render_template('clientes/formulario.html', cliente=cliente, datos=None)


# ==============================================================================
# ELIMINAR CLIENTE
# ==============================================================================

@clientes_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar(id):
    """
    Elimina un cliente del sistema.
    
    Solo acepta peticiones POST para evitar eliminaciones accidentales.
    Verifica que el cliente no tenga documentos asociados.
    
    Parámetros:
        id (int): Identificador del cliente a eliminar
    
    Retorna:
        Redirección a la lista con mensaje de resultado
    """
    # Buscamos el cliente o mostramos error 404
    cliente = Cliente.query.get_or_404(id)
    
    # Verificamos que no tenga documentos asociados (integridad referencial)
    if cliente.tiene_documentos:
        flash('No se puede eliminar el cliente porque tiene ofertas, partes o facturas asociados', 
              'error')
        return redirect(url_for('clientes.lista'))
    
    try:
        # Eliminamos el cliente
        db.session.delete(cliente)
        db.session.commit()
        
        flash('Cliente eliminado correctamente', 'success')
        
    except Exception as e:
        # Si hay error, deshacemos los cambios
        db.session.rollback()
        flash(f'Error al eliminar el cliente: {str(e)}', 'error')
    
    return redirect(url_for('clientes.lista'))
