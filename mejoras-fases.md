
---

## Fase 1 — Ordenación dinámica de tablas (empezando por Clientes)

````
Quiero añadir ordenación dinámica a las tablas de la aplicación, empezando por la tabla de Clientes.

CONTEXTO PREVIO (antes de tocar código)
Analiza la estructura actual del proyecto: framework y ORM utilizados, cómo está implementada hoy la vista/listado de Clientes (ruta, plantilla, consulta), y cómo funcionan ya la paginación y la búsqueda/filtros en esa vista. Adapta todo lo que sigue a lo que encuentres; no asumas una estructura de archivos concreta.

OBJETIVO
Permitir que el usuario haga clic sobre el encabezado de cualquier columna de la tabla de Clientes para ordenar los registros de forma ascendente o descendente. Cada clic debe alternar entre ambos sentidos.

COLUMNAS ORDENABLES
Código, Nombre, DNI, Teléfono, Localidad, Trabajo.

COMPORTAMIENTO DE LOS CLICS
- Primer clic sobre una columna: orden ascendente.
- Segundo clic sobre la misma columna: orden descendente.
- Tercer clic: ascendente de nuevo (alterna indefinidamente).
- Si la URL no trae parámetros de ordenación, mantén el orden por defecto que la vista ya tiene hoy; no lo cambies.

REQUISITOS TÉCNICOS
- La ordenación se resuelve en la consulta SQLAlchemy (order_by), nunca solo en JavaScript.
- Usa parámetros GET: sort (columna) y order (asc/desc), salvo que el proyecto ya tenga una convención de nombres distinta para algo equivalente; en ese caso, síguela.
- Valida "sort" contra una lista blanca que mapee el valor recibido por GET a la columna real del modelo. Si el valor no está en la lista blanca, ignóralo y usa el valor por defecto. Nunca construyas el order_by a partir de un string sin validar contra esa lista.

Ejemplo orientativo (adapta nombres y ubicación a tu estructura real; no lo copies literalmente si no encaja):

```
ALLOWED_SORT_FIELDS = {
    "codigo": Cliente.codigo,
    "nombre": Cliente.nombre,
    "dni": Cliente.dni,
    "telefono": Cliente.telefono,
    "localidad": Cliente.localidad,
    "trabajo": Cliente.trabajo,
}

def aplicar_ordenacion(query, sort_key, order):
    columna = ALLOWED_SORT_FIELDS.get(sort_key)
    if columna is None:
        return query  # se mantiene el order_by por defecto actual
    return query.order_by(columna.desc() if order == "desc" else columna.asc())
```

- Los enlaces de cada encabezado deben conservar el resto de parámetros ya presentes en la URL (texto de búsqueda, filtros, página actual) y cambiar solo sort/order. Los enlaces de paginación y el formulario de búsqueda, a su vez, deben conservar sort/order al regenerarse.
- Muestra un indicador visual (↑ ascendente, ↓ descendente) en el encabezado actualmente ordenado. En el resto de encabezados ordenables puedes añadir un icono neutro (por ejemplo ⇅) para sugerir que son clicables.

DISEÑO
No cambies el diseño actual de la tabla ni el estilo visual existente (colores, tipografías, estructura). Se permiten micro-interacciones que no alteran esa identidad visual, como cursor: pointer o un hover sutil en los encabezados clicables.

EVITAR DUPLICACIÓN Y ARQUITECTURA REUTILIZABLE
Si existen vistas similares (Ofertas, Facturas, Partes, etc.), construye la lógica de ordenación como una función/utilidad reutilizable, no la repitas por vista. Si el proyecto usa plantillas Jinja, crea también un macro reutilizable para renderizar un encabezado ordenable (recibe columna, etiqueta, sort y order actuales), en vez de repetir el HTML del enlace y el indicador en cada <th>.

Ejemplo orientativo de macro (adapta a tu estructura real):

```
{% macro th_ordenable(clave, etiqueta, sort_actual, order_actual) %}
  {% set siguiente_order = 'desc' if sort_actual == clave and order_actual == 'asc' else 'asc' %}
  <th>
    <a href="{{ url_for(request.endpoint, **request.args.to_dict(), sort=clave, order=siguiente_order) }}">
      {{ etiqueta }}
      {% if sort_actual == clave %}{{ '↑' if order_actual == 'asc' else '↓' }}{% endif %}
    </a>
  </th>
{% endmacro %}
```

ENTREGABLE FINAL
Cuando termines, indícame:
1. Qué archivos has modificado o creado.
2. Qué cambios concretos has hecho en cada uno.
3. Cómo puedo reutilizar esta misma funcionalidad en el resto de tablas de la aplicación.
4. Si has encontrado alguna ambigüedad o has tenido que tomar alguna decisión no especificada aquí, dímelo explícitamente en vez de asumirla en silencio.
````

---

## Fase 2 — Dashboard: facturación mensual/anual y gráfico navegable

````
Quiero ampliar el dashboard con datos de facturación y hacer navegable el gráfico mensual que ya existe.

CONTEXTO PREVIO
Analiza cómo está construido el dashboard actual: la ruta/vista, cómo se calculan hoy los datos que alimentan el gráfico mensual de facturación (librería de gráficos usada, cómo se agregan los importes por mes, qué campo de fecha de la factura se usa como referencia), y qué estilo siguen las tarjetas/indicadores que ya existen en el dashboard, si los hay.

PARTE A: indicadores de facturación mensual y anual
- Añade dos indicadores al dashboard, con el mismo estilo visual que el resto de tarjetas/indicadores ya existentes:
  - "Facturación mensual": suma de importes facturados en el mes en curso.
  - "Facturación anual": suma de importes facturados en el año en curso.
- Usa exactamente la misma lógica/consulta (mismo campo de fecha, mismo criterio de qué facturas cuentan) que ya usa el gráfico mensual existente, para que ambos datos sean siempre coherentes entre sí.
- Si el proyecto distingue entre facturas emitidas, pagadas o anuladas y no está claro cuál de esas categorías debe sumarse, usa el mismo criterio que ya aplica el gráfico mensual actual, y dilo en tu resumen final.

PARTE B: gráfico de facturación mensual navegable
- Mantén el tipo de gráfico, colores y estilo actuales.
- Modifícalo para que se puedan ver todos los meses con datos, no solo la ventana fija actual, añadiendo desplazamiento horizontal o controles de navegación (flechas anterior/siguiente, o un contenedor con scroll horizontal), según lo que mejor encaje con la librería de gráficos ya utilizada.
- No elimines funcionalidad actual (tooltips, interactividad, granularidad de los datos); añade solo la capacidad de alcanzar meses fuera del rango visible hoy.
- Prioriza la solución que requiera menos dependencias nuevas.

ENTREGABLE FINAL
Indícame:
1. Qué archivos has modificado o creado.
2. El criterio exacto usado para calcular "facturación mensual/anual".
3. Cómo funciona la navegación añadida al gráfico y si has incorporado alguna dependencia nueva.
````

---

## Fase 3 — Marcar facturas como pagadas y renombrar la alarma de vencidas

````
Quiero poder marcar una factura como pagada desde la aplicación, que eso afecte al aviso de facturas vencidas, y renombrar ese aviso.

CONTEXTO PREVIO
Analiza el modelo de Factura actual (¿existe ya algún campo de estado o de pago?), dónde y cómo se calcula hoy el aviso/contador de "facturas vencidas" (dashboard, badge, vista aparte...), y qué criterio usa actualmente para considerar una factura "vencida" (por ejemplo, fecha de vencimiento pasada).

PARTE A: botón "Marcar como pagada"
- Añade una acción (botón o interruptor) en el listado y/o la ficha de cada factura para marcarla como pagada, y para revertirlo si hace falta.
- Si el modelo de Factura no tiene ya un campo para esto, añádelo (por ejemplo, un booleano "pagada" o un campo de estado, lo que mejor encaje con el esquema actual) junto con la migración necesaria.
- El botón debe seguir el estilo visual (colores, tipografía, tamaños) ya usado en otras acciones de la aplicación.
- Sigue el patrón de interacción ya existente en el resto de la app (si ya usáis peticiones AJAX/fetch en acciones similares, usa lo mismo; si no, un formulario simple es suficiente).

PARTE B: vínculo con la alarma de vencidas
- Actualiza la lógica del aviso/contador para que no cuente como vencida ninguna factura ya marcada como pagada, sin importar su fecha de vencimiento.
- No cambies el criterio de "vencida" en ningún otro sentido, solo excluye las pagadas, salvo que el propio código actual ya lo definiera de otra forma; en ese caso, dime qué has encontrado antes de decidir.

PARTE C: renombrar "Facturas vencidas" a "Facturas pendientes de cobro"
- Busca y cambia todas las apariciones del texto visible "Facturas vencidas" (y variantes de "vencida(s)" en títulos, badges, menús o cabeceras) por "Facturas pendientes de cobro".
- Cambia solo el texto/etiqueta visible para el usuario, no renombres variables, funciones, rutas o campos internos salvo que sea trivial y no añada riesgo.
- Este es un cambio de nombre, no necesariamente un cambio de criterio: mantén la misma lógica de qué facturas se cuentan (vencidas y no pagadas). Si tienes dudas sobre si el nuevo nombre "pendientes de cobro" debería ampliar el criterio a "todas las facturas no pagadas" (no solo las vencidas), pregúntamelo antes de decidirlo por tu cuenta.

ENTREGABLE FINAL
Indícame:
1. Qué archivos has modificado o creado.
2. Qué campo o migración has añadido, si aplica, y el comando para aplicarla.
3. El criterio exacto que usa ahora el aviso "pendientes de cobro" tras el cambio.
4. Cualquier ambigüedad que hayas encontrado y cómo la has resuelto.
````

---

## Fase 4 — Email en clientes y en el PDF de factura

````
Quiero añadir un campo de email a los clientes y que aparezca también en el PDF de la factura.

CONTEXTO PREVIO
Analiza el modelo de Cliente actual, las plantillas/formularios de alta y edición de clientes, la vista de ficha/listado de clientes, y cómo se genera hoy el PDF de factura (librería usada y dónde se insertan los datos del cliente en esa plantilla).

REQUISITOS
- Añade un campo email al modelo de Cliente (opcional/nullable), junto con la migración correspondiente.
- Añade el campo de email al formulario de alta y edición de clientes, con una validación básica de formato (en cliente y servidor), siguiendo el mismo patrón de validación que ya se use para otros campos, si existe alguno.
- Muestra el email en la ficha/listado de clientes, junto al resto de datos de contacto (teléfono, localidad), respetando el estilo visual actual.
- Incluye el email del cliente en el PDF de la factura generada, junto al resto de datos del cliente que ya aparecen (nombre, DNI, teléfono, etc.), manteniendo el estilo visual actual del PDF.
- Los clientes ya existentes no tendrán email guardado: si el campo está vacío, no muestres la línea de email en el PDF, salvo que ese sea ya el patrón usado para otros campos opcionales.

ENTREGABLE FINAL
Indícame:
1. Qué archivos has modificado o creado.
2. El comando de migración necesario para aplicar el cambio en la base de datos.
3. Confirmación de que las facturas generadas anteriormente no se ven afectadas y que las nuevas incluirán el email cuando exista.
````

---

## Extender esto al resto de tablas

Una vez completada la Fase 1, aplicar el mismo patrón a Ofertas, Facturas o Partes debería requerir un prompt mucho más corto, por ejemplo:

> "Aplica a la tabla de Ofertas el mismo patrón de ordenación dinámica que implementaste en Clientes (función de ordenación reutilizable + macro de encabezado con indicador ↑/↓). No dupliques esa lógica, reutiliza lo ya creado. Columnas ordenables: [lista de columnas de Ofertas]."

Solo cambia el nombre de la tabla y la lista de columnas; el resto ya estará resuelto por la Fase 1. Antigravity también debería haberte dado su propia recomendación de reutilización al terminar esa fase (se lo pide el punto 3 del entregable final) — compárala con esto y usa la que mejor encaje con lo que realmente haya construido.
