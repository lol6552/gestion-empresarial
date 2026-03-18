# **Documento de Especificación de Requisitos (SRS)**

## **Sistema de Gestión Empresarial para Autónomo**

**Versión:** 1.1  
 **Fecha:** 21 de enero de 2026  
 **Cliente:** Javier Aranguren Meneses  
 **Preparado para:** Antigravity

---

## **1\. Introducción**

### **1.1 Propósito del documento**

Este documento especifica los requisitos funcionales y técnicos para el desarrollo de una aplicación web local destinada a reemplazar una solución basada en Excel para la gestión integral de clientes, ofertas, partes de trabajo y facturación de un trabajador autónomo.

### **1.2 Alcance del proyecto**

La aplicación permitirá gestionar el ciclo completo de trabajo desde el contacto inicial con el cliente hasta la facturación, incluyendo:

* Base de datos de clientes  
* Generación de ofertas/presupuestos  
* Registro de partes de trabajo con control horario y costes detallados  
* Emisión de facturas  
* Generación automática de documentos PDF  
* Consulta y filtrado de históricos

  ### **1.3 Contexto de negocio**

El cliente trabaja en dos modalidades:

1. **Trabajos planificados:** Oferta → Aceptación → Factura  
2. **Trabajos de emergencia:** Parte de trabajo → Cobro inmediato → Factura posterior  
   ---

   ## **2\. Requisitos Funcionales**

   ### **2.1 Gestión de Clientes**

   #### **RF-01: Crear cliente**

**Descripción:** El sistema debe permitir crear nuevos clientes con información completa.

**Campos obligatorios:**

* ID (auto-generado)  
* Nombre  
* Apellido  
* DNI  
* Teléfono  
* Dirección  
* Código postal  
* Localidad  
* Trabajo a realizar

**Criterios de aceptación:**

* El formulario valida campos obligatorios  
* El DNI debe ser único en el sistema  
* Al guardar, el sistema confirma la creación exitosa

  #### **RF-02: Listar clientes**

**Descripción:** Visualizar todos los clientes registrados en formato tabla.

**Criterios de aceptación:**

* Mostrar al menos: nombre completo, DNI, teléfono, localidad  
* Incluir opciones de editar y eliminar por cada registro  
* Ordenación por defecto alfabética por apellido

  #### **RF-03: Editar cliente**

**Descripción:** Modificar datos de un cliente existente.

**Criterios de aceptación:**

* Formulario precargado con datos actuales  
* Validación de campos obligatorios  
* Confirmación tras actualización exitosa

  #### **RF-04: Eliminar cliente**

**Descripción:** Borrar un cliente del sistema.

**Criterios de aceptación:**

* Solicitar confirmación antes de eliminar  
* Verificar que no existan ofertas/partes/facturas vinculados (integridad referencial)

  #### **RF-05: Creación automática desde oferta/parte**

**Descripción:** Al crear una oferta o parte de trabajo, si el cliente no existe, debe poder crearse en ese mismo flujo.

**Criterios de aceptación:**

* Opción de "crear nuevo cliente" desde formulario de oferta/parte  
* Guardar cliente antes de procesar oferta/parte  
* Vincular automáticamente el cliente recién creado  
  ---

  ### **2.2 Gestión de Ofertas**

  #### **RF-06: Crear oferta**

**Descripción:** Generar una nueva oferta/presupuesto para un cliente.

**Datos requeridos:**

* Número de oferta (auto-generado, correlativo)  
* Cliente (seleccionar existente o crear nuevo)  
* Descripción del trabajo  
* Partidas/conceptos (descripción, cantidad, precio unitario)  
* Subtotal  
* IVA (calculado)  
* Total (calculado)  
* Datos del autónomo:  
  * Nombre: Javier Aranguren Meneses  
  * DNI: 78784784J  
  * Dirección: C/ Foz de Lumbier 1  
* Formas de pago disponibles:  
  * Transferencia (cuenta: 89898 89898 8989\)  
  * Bizum  
  * Efectivo

**Criterios de aceptación:**

* La plantilla HTML se muestra vacía al acceder  
* Al guardar: se almacenan datos en BD, se genera PDF, se guarda ruta del PDF  
* Tras guardar, se redirige a plantilla vacía (no persiste datos)  
* PDF generado incluye toda la información de la oferta

  #### **RF-07: Listar ofertas**

**Descripción:** Visualizar todas las ofertas creadas.

**Criterios de aceptación:**

* Mostrar: número, cliente, fecha, total, estado (pendiente/aceptada)  
* Filtros por: cliente, rango de fechas, estado  
* Opción de ver/descargar PDF asociado  
  ---

  ### **2.3 Gestión de Partes de Trabajo**

  #### **RF-08: Crear parte de trabajo**

**Descripción:** Registrar un trabajo realizado (generalmente emergencias) con control detallado de tiempos, desplazamientos y materiales.

**Datos requeridos:**

**A. Información general:**

* Número de parte (auto-generado, correlativo)  
* Cliente (seleccionar existente o crear nuevo)  
* Descripción del trabajo realizado  
* Fecha de realización

**B. Control horario:**

* Hora de inicio (formato HH:MM)  
* Hora de fin (formato HH:MM)  
* Horas de trabajo (calculadas automáticamente: fin \- inicio)  
* Precio por hora de trabajo  
* **Subtotal horas trabajo** \= horas\_trabajo × precio\_hora\_trabajo

**C. Desplazamiento:**

* Horas de desplazamiento (campo numérico, puede incluir decimales)  
* Precio por hora de desplazamiento  
* **Subtotal desplazamiento** \= horas\_desplazamiento × precio\_hora\_desplazamiento

**D. Materiales:**

* Descripción de materiales comprados/utilizados  
* Importe total de materiales

**E. Totales:**

* **Subtotal general** \= subtotal\_horas\_trabajo \+ subtotal\_desplazamiento \+ materiales  
* IVA (calculado sobre subtotal general)  
* **Total final** \= subtotal\_general \+ IVA

**F. Datos del autónomo y pago:**

* Datos del autónomo (mismo que ofertas)  
* Formas de pago (transferencia/bizum/efectivo)

**Criterios de aceptación:**

* La plantilla HTML se muestra vacía al acceder  
* Las horas de trabajo se calculan automáticamente al introducir inicio y fin  
* Los subtotales se calculan automáticamente según las fórmulas indicadas  
* El total final incluye trabajo \+ desplazamiento \+ materiales \+ IVA  
* Al guardar: se almacenan todos los datos en BD, se genera PDF con desglose detallado, se guarda ruta del PDF  
* Tras guardar, se redirige a plantilla vacía (no persiste datos)  
* PDF muestra claramente el desglose de: horas trabajo, desplazamiento, materiales y totales

  #### **RF-09: Validaciones específicas del parte de trabajo**

**Descripción:** Validar la coherencia de los datos temporales y económicos.

**Criterios de aceptación:**

* Hora de fin debe ser posterior a hora de inicio  
* Las horas de trabajo calculadas deben ser positivas  
* Las horas de desplazamiento no pueden ser negativas  
* Todos los precios e importes deben ser positivos  
* El IVA se calcula correctamente sobre el subtotal general

  #### **RF-10: Listar partes de trabajo**

**Descripción:** Consultar histórico de partes con información resumida.

**Criterios de aceptación:**

* Mostrar: número, cliente, fecha, horas trabajadas, total  
* Filtros por: cliente, rango de fechas  
* Opción de ver/descargar PDF  
* Indicador visual si incluye desplazamiento y/o materiales  
  ---

  ### **2.4 Gestión de Facturas**

  #### **RF-11: Crear factura desde oferta**

**Descripción:** Generar factura automáticamente a partir de una oferta aceptada.

**Criterios de aceptación:**

* Seleccionar oferta desde listado  
* Datos del cliente se cargan automáticamente  
* Descripción del trabajo se carga automáticamente  
* Importes (subtotal, IVA, total) se cargan automáticamente  
* **Todos los campos son editables** antes de generar el PDF  
* Número de factura auto-generado y correlativo  
* Al guardar: BD \+ PDF \+ redirigir vacío

  #### **RF-12: Crear factura desde parte de trabajo**

**Descripción:** Generar factura a partir de un parte de trabajo registrado.

**Criterios de aceptación:**

* Seleccionar parte desde listado  
* Datos del cliente se cargan automáticamente  
* **Descripción incluye desglose del parte:** horas trabajo, desplazamiento, materiales  
* Los subtotales del parte se transfieren correctamente  
* IVA y total se cargan correctamente  
* **Todos los campos son editables** antes de generar el PDF  
* Número de factura auto-generado y correlativo  
* Al guardar: BD \+ PDF \+ redirigir vacío

  #### **RF-13: Crear factura manual**

**Descripción:** Crear una factura sin vincularla a oferta ni parte previo.

**Criterios de aceptación:**

* Formulario vacío para completar manualmente  
* Cliente seleccionable o nuevo  
* Resto del flujo idéntico a RF-11 y RF-12

  #### **RF-14: Listar facturas**

**Descripción:** Consultar histórico de facturas emitidas.

**Criterios de aceptación:**

* Mostrar: número, cliente, fecha, total, origen (oferta/parte/manual)  
* Filtros por: cliente, rango de fechas, forma de pago  
* Opción de ver/descargar PDF  
  ---

  ### **2.5 Sistema de Numeración**

  #### **RF-15: Numeradores automáticos**

**Descripción:** Cada tipo de documento (oferta, parte, factura) debe tener numeración correlativa independiente.

**Criterios de aceptación:**

* Tabla de numeradores en BD con campos: tipo\_documento, ultimo\_numero  
* Incremento automático al crear nuevo documento  
* Formato: OFERTA-001, PARTE-001, FACTURA-001 (o similar configurable)  
* Sin saltos ni duplicados  
  ---

  ### **2.6 Generación de PDFs**

  #### **RF-16: Generación de PDF desde plantilla HTML**

**Descripción:** Convertir plantillas HTML (Jinja2) a PDF.

**Criterios de aceptación:**

* Usar librería compatible con Flask (WeasyPrint o similar)  
* PDF debe reflejar exactamente el diseño de la plantilla HTML  
* Estilos CSS aplicados correctamente en PDF

  #### **RF-17: Almacenamiento de PDFs**

**Descripción:** Guardar PDFs generados en sistema de archivos.

**Criterios de aceptación:**

* Estructura de carpetas: `/pdfs/ofertas/`, `/pdfs/partes/`, `/pdfs/facturas/`  
* Nomenclatura: `TIPO-NUMERO.pdf` (ej: `FACTURA-001.pdf`)  
* Ruta del archivo guardada en BD vinculada al documento

  #### **RF-18: Descarga de PDFs**

**Descripción:** Permitir visualizar/descargar PDFs desde el listado.

**Criterios de aceptación:**

* Enlace directo desde listado  
* Abrir en nueva pestaña o descargar directamente  
  ---

  ### **2.7 Plantillas HTML**

  #### **RF-19: Diseño coherente entre documentos**

**Descripción:** Ofertas, partes y facturas deben compartir estética visual uniforme.

**Criterios de aceptación:**

* Mismo encabezado con datos del autónomo  
* Misma tipografía, colores, espaciados  
* Estructura similar (cabecera → datos cliente → detalle → totales → pie)  
* CSS centralizado o reutilizado

  #### **RF-20: Plantilla específica para partes de trabajo**

**Descripción:** La plantilla del parte debe mostrar claramente el desglose de costes.

**Criterios de aceptación:**

* Sección de control horario con inicio, fin y horas totales  
* Subtotal de horas de trabajo claramente identificado  
* Sección de desplazamiento con horas y subtotal  
* Sección de materiales con descripción e importe  
* Desglose visual claro del cálculo del total final  
* Formato tabular para facilitar lectura

  #### **RF-21: Editabilidad de plantillas**

**Descripción:** El diseño visual debe modificarse solo editando HTML/CSS, sin tocar Python.

**Criterios de aceptación:**

* Variables Jinja2 claramente identificadas  
* CSS modular y comentado  
* Cambios visuales no requieren modificar lógica de negocio  
  ---

  ## **3\. Requisitos Técnicos**

  ### **3.1 Arquitectura y Tecnologías**

  #### **RT-01: Framework backend**

* **Framework:** Flask  
* **Sin Docker:** Despliegue directo en sistema operativo

  #### **RT-02: Lenguaje de programación**

* **Lenguaje:** Python 3.8+

  #### **RT-03: Base de datos**

* **Motor:** SQLite  
* **ORM:** SQLAlchemy  
* **Ubicación:** `instance/database.db`  
* **Configuración:** Ruta definida únicamente en `config.py`

  #### **RT-04: Estructura del proyecto**

  proyecto/  
  ├── app.py                  \# Punto de entrada (mínimo código, solo inicialización)  
  ├── config.py               \# Configuración (ruta BD, secretos, etc.)  
  ├── models/                 \# Modelos SQLAlchemy  
  │   ├── \_\_init\_\_.py  
  │   ├── cliente.py  
  │   ├── oferta.py  
  │   ├── parte.py  
  │   ├── factura.py  
  │   └── numerador.py  
  ├── routes/                 \# Blueprints (rutas/controladores)  
  │   ├── \_\_init\_\_.py  
  │   ├── clientes.py  
  │   ├── ofertas.py  
  │   ├── partes.py  
  │   └── facturas.py  
  ├── templates/              \# Plantillas Jinja2  
  │   ├── base.html  
  │   ├── clientes/  
  │   ├── ofertas/  
  │   ├── partes/  
  │   └── facturas/  
  ├── static/                 \# CSS, JS, imágenes  
  │   ├── css/  
  │   └── img/  
  ├── instance/               \# Datos persistentes (BD, PDFs)  
  │   ├── database.db  
  │   └── pdfs/  
  │       ├── ofertas/  
  │       ├── partes/  
  │       └── facturas/  
  └── requirements.txt        \# Dependencias Python


  #### **RT-05: Uso de Blueprints**

* Cada módulo (clientes, ofertas, partes, facturas) debe ser un Blueprint independiente  
* Registro de Blueprints en `app.py`

  #### **RT-06: Calidad del código**

* Código comentado en español  
* Docstrings en funciones clave  
* Nomenclatura clara y consistente (snake\_case)  
* Nivel de complejidad: entendible para programador Python intermedio  
  ---

  ### **3.2 Modelado de Datos**

  #### **RT-07: Modelo Cliente**

  Cliente:  
      \- id: Integer, PK, autoincrement  
      \- nombre: String(100), NOT NULL  
      \- apellido: String(100), NOT NULL  
      \- dni: String(20), UNIQUE, NOT NULL  
      \- telefono: String(20), NOT NULL  
      \- direccion: String(200), NOT NULL  
      \- codigo\_postal: String(10), NOT NULL  
      \- localidad: String(100), NOT NULL  
      \- trabajo\_a\_realizar: Text, NULLABLE  
      \- fecha\_creacion: DateTime, default=now


  #### **RT-08: Modelo Numerador**

  Numerador:  
      \- id: Integer, PK, autoincrement  
      \- tipo\_documento: String(50), UNIQUE, NOT NULL  \# 'oferta', 'parte', 'factura'  
      \- ultimo\_numero: Integer, default=0


  #### **RT-09: Modelo Oferta**

  Oferta:  
      \- id: Integer, PK, autoincrement  
      \- numero: String(50), UNIQUE, NOT NULL  
      \- cliente\_id: Integer, FK(Cliente.id), NOT NULL  
      \- fecha: DateTime, default=now  
      \- descripcion: Text, NOT NULL  
      \- subtotal: Decimal(10,2), NOT NULL  
      \- iva: Decimal(10,2), NOT NULL  
      \- total: Decimal(10,2), NOT NULL  
      \- estado: String(20), default='pendiente'  \# pendiente/aceptada/rechazada  
      \- ruta\_pdf: String(500), NULLABLE  
      \- fecha\_creacion: DateTime, default=now


  #### **RT-10: Modelo Parte de Trabajo (ACTUALIZADO)**

  ParteTrabajo:  
      \- id: Integer, PK, autoincrement  
      \- numero: String(50), UNIQUE, NOT NULL  
      \- cliente\_id: Integer, FK(Cliente.id), NOT NULL  
      \- fecha\_realizacion: Date, NOT NULL  
      \- descripcion: Text, NOT NULL  
        
      \# Control horario  
      \- hora\_inicio: Time, NOT NULL  
      \- hora\_fin: Time, NOT NULL  
      \- horas\_trabajo: Decimal(5,2), NOT NULL  \# Calculado: fin \- inicio  
      \- precio\_hora\_trabajo: Decimal(10,2), NOT NULL  
      \- subtotal\_trabajo: Decimal(10,2), NOT NULL  \# horas\_trabajo × precio\_hora\_trabajo  
        
      \# Desplazamiento  
      \- horas\_desplazamiento: Decimal(5,2), default=0  
      \- precio\_hora\_desplazamiento: Decimal(10,2), default=0  
      \- subtotal\_desplazamiento: Decimal(10,2), default=0  \# horas\_desp × precio\_hora\_desp  
        
      \# Materiales  
      \- materiales\_descripcion: Text, NULLABLE  
      \- materiales\_importe: Decimal(10,2), default=0  
        
      \# Totales  
      \- subtotal\_general: Decimal(10,2), NOT NULL  \# trabajo \+ desplazamiento \+ materiales  
      \- iva: Decimal(10,2), NOT NULL  
      \- total: Decimal(10,2), NOT NULL  \# subtotal\_general \+ iva  
        
      \- ruta\_pdf: String(500), NULLABLE  
      \- fecha\_creacion: DateTime, default=now


  #### **RT-11: Modelo Factura**

  Factura:  
      \- id: Integer, PK, autoincrement  
      \- numero: String(50), UNIQUE, NOT NULL  
      \- cliente\_id: Integer, FK(Cliente.id), NOT NULL  
      \- oferta\_id: Integer, FK(Oferta.id), NULLABLE  
      \- parte\_id: Integer, FK(ParteTrabajo.id), NULLABLE  
      \- fecha: DateTime, default=now  
      \- descripcion: Text, NOT NULL  
      \- subtotal: Decimal(10,2), NOT NULL  
      \- iva: Decimal(10,2), NOT NULL  
      \- total: Decimal(10,2), NOT NULL  
      \- forma\_pago: String(50), NOT NULL  \# transferencia/bizum/efectivo  
      \- ruta\_pdf: String(500), NULLABLE  
      \- fecha\_creacion: DateTime, default=now  
    
  ---

  ### **3.3 Restricciones y Validaciones**

  #### **RT-12: Integridad referencial**

* No permitir eliminar clientes con ofertas/partes/facturas asociados  
* Cascada de eliminación debe ser manual (previa confirmación)

  #### **RT-13: Validaciones de datos**

* DNI único por cliente  
* Números de documento únicos (oferta, parte, factura)  
* Importes siempre positivos  
* Fechas no futuras (excepto si se requiere)  
* **Para partes de trabajo:**  
  * hora\_fin \> hora\_inicio  
  * horas\_trabajo \> 0  
  * horas\_desplazamiento \>= 0  
  * Todos los precios e importes \>= 0  
  * Consistencia entre subtotales calculados y almacenados

  #### **RT-14: Cálculos automáticos en partes**

* Las horas de trabajo se calculan automáticamente en el backend  
* Los subtotales se calculan automáticamente antes de guardar  
* Validar que los cálculos manuales (si se permiten) coincidan con las fórmulas  
  ---

  ### **3.4 Despliegue**

  #### **RT-15: Entorno de ejecución**

* **Modo:** Local, accesible desde red local  
* **Puerto:** Configurable (default: 5000\)  
* **Host:** 0.0.0.0 para acceso en red local

  #### **RT-16: Dependencias**

* Flask  
* SQLAlchemy  
* WeasyPrint (o librería PDF compatible)  
* Otras según necesidad (Flask-WTF, etc.)  
  ---

  ## **4\. Alcance de la Fase Inicial**

  ### **4.1 Entregables de Fase 1**

1. **Estructura completa del proyecto** según RT-04  
2. **Módulo de Clientes completo:**  
   * CRUD funcional desde navegador  
   * Listado con filtros básicos  
   * Validaciones implementadas  
3. **Sistema de numeradores automáticos:**  
   * Tabla Numerador creada  
   * Lógica de incremento implementada  
   * Probada para al menos un tipo de documento  
4. **Modelos de BD definidos:**  
   * Cliente, Oferta, ParteTrabajo (con todos los campos nuevos), Factura, Numerador  
   * Relaciones establecidas  
5. **Configuración inicial:**  
   * `config.py` funcional  
   * Base de datos inicializada en `instance/database.db`  
   * Blueprints registrados

   ### **4.2 Fuera de Fase 1**

* Implementación completa de ofertas, partes y facturas  
* Generación de PDFs  
* Plantillas HTML finalizadas  
* Filtros avanzados y reportes  
* Cálculos automáticos de horas en frontend (JavaScript)  
  ---

  ## **5\. Requisitos No Funcionales**

  ### **RNF-01: Usabilidad**

* Interfaz intuitiva, navegación clara  
* Formularios con labels descriptivos  
* Mensajes de error comprensibles  
* **Para partes:** Cálculo visual de horas y subtotales en tiempo real (JavaScript)

  ### **RNF-02: Rendimiento**

* Tiempo de respuesta \< 2 segundos para operaciones estándar  
* Generación de PDF \< 5 segundos  
* Cálculos automáticos instantáneos

  ### **RNF-03: Mantenibilidad**

* Código modular y bien documentado  
* Fácil modificación de plantillas sin tocar lógica  
* Configuración centralizada  
* Fórmulas de cálculo claramente documentadas

  ### **RNF-04: Seguridad**

* Validación de entradas en servidor  
* Protección contra inyección SQL (ORM)  
* Acceso restringido a red local  
* Validación de coherencia en cálculos (servidor verifica cálculos del cliente)  
  ---

  ## **6\. Criterios de Aceptación Generales**

1. **Funcionalidad:** Todos los RF de Fase 1 implementados y probados  
2. **Código:** Cumple estándares de RT-06 (limpio, comentado, estructurado)  
3. **Base de datos:** Creada en ubicación correcta con modelos funcionales  
4. **Despliegue:** Aplicación ejecutable en local y accesible desde red  
5. **Documentación:** README con instrucciones de instalación y uso básico  
6. **Cálculos:** Verificación de fórmulas para partes de trabajo funcionales  
   ---

   ## **7\. Casos de Uso Detallados**

   ### **7.1 Caso de Uso: Crear Parte de Trabajo con Desglose Completo**

**Actor:** Autónomo (Javier)

**Precondiciones:**

* Sistema iniciado  
* Cliente puede existir o no

**Flujo Principal:**

1. Usuario accede a "Nuevo Parte de Trabajo"  
2. Sistema muestra formulario vacío  
3. Usuario selecciona/crea cliente  
4. Usuario introduce:  
   * Fecha: 21/01/2026  
   * Hora inicio: 09:00  
   * Hora fin: 14:30  
   * Precio hora trabajo: 25.00€  
   * Horas desplazamiento: 1.5  
   * Precio hora desplazamiento: 15.00€  
   * Materiales descripción: "Tuberías PVC 50mm (3m), codos, silicona"  
   * Materiales importe: 45.50€  
5. Sistema calcula automáticamente:  
   * Horas trabajo: 5.5 horas  
   * Subtotal trabajo: 137.50€  
   * Subtotal desplazamiento: 22.50€  
   * Subtotal general: 205.50€  
   * IVA (21%): 43.16€  
   * Total: 248.66€  
6. Usuario revisa y confirma  
7. Sistema guarda en BD, genera PDF con desglose, almacena PDF  
8. Sistema redirige a formulario vacío

**Postcondiciones:**

* Parte creado con número correlativo  
* PDF generado en `/instance/pdfs/partes/PARTE-XXX.pdf`  
* Cliente vinculado (nuevo o existente)  
  ---

  ## **8\. Supuestos y Dependencias**

  ### **Supuestos**

* El cliente tiene conocimientos básicos de Python  
* El sistema operativo soporta Python 3.8+  
* Acceso a navegador moderno (Chrome, Firefox, Edge)  
* Los precios por hora son fijos por parte (no varían durante el trabajo)  
* El IVA aplicable es del 21% (configurable si es necesario)

  ### **Dependencias**

* Instalación de Python y pip  
* Posible instalación de dependencias de WeasyPrint (librerías del SO)  
* JavaScript habilitado para cálculos en tiempo real (opcional, mejora UX)  
  ---

  ## **9\. Glosario**

* **Autónomo:** Trabajador por cuenta propia  
* **Oferta/Presupuesto:** Documento previo a la prestación del servicio  
* **Parte de trabajo:** Registro de trabajo realizado con desglose de tiempos y costes  
* **Factura:** Documento fiscal de cobro  
* **Blueprint:** Módulo de rutas en Flask  
* **ORM:** Object-Relational Mapping (mapeo objeto-relacional)  
* **CRUD:** Create, Read, Update, Delete  
* **Subtotal trabajo:** Importe resultante de horas trabajadas × precio hora trabajo  
* **Subtotal desplazamiento:** Importe resultante de horas desplazamiento × precio hora desplazamiento  
* **Subtotal general:** Suma de trabajo \+ desplazamiento \+ materiales (antes de IVA)  
  ---

  ## **10\. Anexos**

  ### **Anexo A: Ejemplo de Desglose de Parte de Trabajo**

  PARTE DE TRABAJO Nº PARTE-015  
  Fecha: 21/01/2026  
    
  CLIENTE: Juan Pérez García  
  DNI: 12345678A  
  Dirección: C/ Mayor 15, 28001 Madrid  
    
  DESCRIPCIÓN: Reparación urgencia fuga tubería  
    
  ──────────────────────────────────────────  
  DESGLOSE DE TRABAJO  
  ──────────────────────────────────────────  
  Hora inicio:     09:00  
  Hora fin:        14:30  
  Horas totales:   5.5 h  
  Precio/hora:     25.00 €  
                            Subtotal: 137.50 €  
    
  ──────────────────────────────────────────  
  DESPLAZAMIENTO  
  ──────────────────────────────────────────  
  Horas:           1.5 h  
  Precio/hora:     15.00 €  
                            Subtotal:  22.50 €  
    
  ──────────────────────────────────────────  
  MATERIALES  
  ──────────────────────────────────────────  
  Tuberías PVC 50mm (3m), codos, silicona  
                            Importe:   45.50 €  
    
  ──────────────────────────────────────────  
  TOTALES  
  ──────────────────────────────────────────  
  Subtotal:                          205.50 €  
  IVA (21%):                          43.16 €  
  TOTAL:                             248.66 €  
  ──────────────────────────────────────────  
    
  Forma de pago: Efectivo  
    
  ---

  ## **11\. Aprobaciones**

| Rol | Nombre | Firma | Fecha |
| ----- | ----- | ----- | ----- |
| Cliente | Javier Aranguren Meneses |  |  |
| Desarrollador (Antigravity) |  |  |  |

  ---

**Fin del documento \- Versión 1.1**

**Historial de cambios:**

* v1.0 (21/01/2026): Versión inicial  
* v1.1 (21/01/2026): Añadido desglose detallado de partes de trabajo con control horario, desplazamiento y materiales


