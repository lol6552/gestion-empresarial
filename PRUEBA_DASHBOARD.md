# Dashboard: entrega local al revisor-publicador

## Alcance

- `routes/principal.py`: KPI mensual y anual y ticket medio con `Factura.subtotal`; serie mensual con el mismo campo. Sumas y redondeo con `Decimal`; conversión a número únicamente para Chart.js.
- `templates/dashboard.html`: etiquetas sin IVA, eje y tooltip, nueva tarjeta de IVA trimestral con nota informativa. Se conserva Chart.js y la cuadrícula responsive existente.
- `requirements.txt`: `tzdata` para resolver `Europe/Madrid` también en Windows.
- `tests/test_dashboard_iva.py`: casos anuales, mensuales, cuatro trimestres, límites de año, trimestre vacío, IVA real de distintos tipos, fecha de Madrid y lectura sin alterar facturas.
- `tests/vista_dashboard_local.py`: vista manual sobre una copia temporal con SQLite y carpeta de PDF propios, emisor ficticio y dos facturas ficticias. Excluye `firma.png` y `firma_v2.png` al copiar, conservando los originales; los PDF locales pueden funcionar sin firma.

Se usa la fecha de emisión `Factura.fecha`, conservando sus fechas civiles almacenadas sin zona horaria. Madrid determina el periodo actual. Los periodos incluyen su inicio y excluyen el inicio del siguiente. Se incluyen facturas pagadas y pendientes; el modelo no tiene estados de borrador, anulación o rectificación. No se incluyen presupuestos ni partes sin facturar. El ticket medio conserva su alcance histórico completo.

La hucha suma `Factura.iva`, sin aplicar porcentajes ni descontar gastos, IVA soportado o IRPF. El trimestre se recalcula al cargar la página; no elimina ni reinicia registros. Se muestra el mes de presentación ordinaria y su año (enero del siguiente año para 4T), sin vencimiento exacto. Fuente: [AEAT](https://sede.agenciatributaria.gob.es/Sede/iva/presentar-declaracion-iva-modelo-303/plazo-presentacion-modelo-303.html).

## Comprobación en navegador

Desde PowerShell, en el repositorio:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt pytest
.\venv\Scripts\python.exe tests/vista_dashboard_local.py
```

Abre http://127.0.0.1:5017. Se usa un puerto distinto al 5001 para evitar confundirlo con otra sesión local. El lanzador sigue el aislamiento del README: copia únicamente código y recursos a una carpeta temporal nueva antes de importar la app; no copia `instance`. No necesita generar PDF ni instalar Chromium para visitar el Dashboard.

Comprueba:

1. Facturación mensual y anual: **300.00 €**. Ticket medio: **150.00 €**.
2. Hucha del trimestre actual: **63,00 €**, con el trimestre y mes de declaración correspondientes.
3. Barra del mes actual: **300 €**, con título, eje y tooltip sin IVA.
4. Redimensiona a móvil y escritorio; revisa las seis tarjetas y la nota fiscal.
5. Puedes añadir facturas ficticias desde la interfaz y cambiar su fecha a otro trimestre o año. Una factura con base 100 € aporta 100 € a facturación y su IVA guardado a la hucha si pertenece al trimestre actual.

Los botones de navegación estarán deshabilitados inicialmente porque hay seis meses de datos visibles. Para comprobarlos, crea una factura ficticia con fecha de hace más de seis meses. El histórico sigue limitado a 24 meses.

Sal con Ctrl+C. La carpeta temporal, su SQLite y sus PDF de prueba se eliminan al cerrar normalmente; la siguiente ejecución empieza con datos ficticios nuevos. Para una comprobación con un entorno nuevo de Python 3.12, sigue la creación de copia y entorno del README y ejecuta este lanzador desde esa copia.

## Validación y publicación

La suite completa ha pasado con Python **3.12.16** y **3.14**: **11 tests y 39 subtests aprobados en cada versión**, usando `python -B -m pytest -q -p no:cacheprovider` en sus respectivos entornos. Las pruebas utilizan SQLite temporal protegido y no acceden a `instance` real. El Agente 2 validó ambas versiones de forma independiente; Python 3.12.16 se preparó en un entorno temporal. La ejecución en el contenedor Linux de producción sigue pendiente.

Comprobación adicional con Chrome y Playwright en la copia aislada: seis tarjetas, KPI mensual/anual de 300 €, hucha de 63 €, barra mensual de 300 €, botones deshabilitados para el histórico inicial de seis meses, sin errores JavaScript ni desbordamiento horizontal a 1440 y 390 píxeles. Se inspeccionaron las capturas de escritorio y móvil. Chart.js sigue dependiendo del CDN existente; la comprobación necesitó acceso de red fuera del sandbox. La vista usa 5017 porque 5001 ya mostraba otra sesión local. El ajuste visual solo cambia el ancho mínimo de las tarjetas en esta plantilla y presenta la advertencia completa mediante tooltip.

Sin cambios de esquema, cálculos de documentos, generación de PDF ni configuración de producción. El README y los otros archivos previos del propietario quedan fuera del lote. No se han realizado commits, pushes, merges ni despliegues. El lote contiene seis archivos en total: los cinco enumerados en Alcance y este documento. El revisor-publicador debe revisarlos antes de continuar el flujo de autorizaciones de AGENTS.md.
