# Auxiliar de pruebas: compatibilidad Linux

## Alcance de la entrega local

- `tests/test_facturas_integracion.py`: extrae la instalación del protector a `instalar_protector` y resuelve aperturas relativas a descriptores de Linux. Conserva el aislamiento de las integraciones existentes y comprueba también el destino de los borrados usados durante la limpieza.
- `tests/test_protector_rutas.py`: siete regresiones independientes, ejecutadas con archivos ficticios en subprocesos para que sus hooks no afecten a pytest ni al proceso padre.
- Este documento.

No se modifican Flask, Dashboard, modelos, cálculos, plantillas, generadores de PDF, dependencias ni Dockerfile. Los cambios previos del propietario en README y otros archivos quedan fuera de esta entrega. No se han hecho commits, pushes, merges ni despliegues.

## Causa y corrección

En Linux, `shutil.rmtree` recorre los subdirectorios mediante `os.open(nombre, ..., dir_fd=descriptor)`, conservando sus comprobaciones contra cambios de enlaces simbólicos. El evento de auditoría `open` solo recibe ruta, modo y flags: no incluye `dir_fd`. Al limpiar el temporal, el nombre relativo `instance` se resolvía incorrectamente desde el directorio de trabajo del repositorio, como si fuese su `instance` real.

El auxiliar presenta esas aperturas mediante `/proc/self/fd/<descriptor>/<ruta>`. Así, tanto el sistema como el auditor reciben una ruta anclada al mismo descriptor, incluso si el directorio de trabajo es otro. Se mantiene la llamada original y sus flags; no se cambia la implementación de `rmtree`, ni se desactiva su protección frente a enlaces simbólicos. Las rutas absolutas conservan su comportamiento y no dependen del descriptor. Si no se puede resolver el descriptor, se rechaza la operación.

El prefijo `/proc` no constituye una autorización: se resuelve el destino y se aplican las mismas reglas. Solo se admite el SQLite temporal exacto; se sigue bloqueando la lectura del `instance` del origen y toda apertura de escritura fuera del temporal. También se comprueban `shutil.rmtree`, `os.remove` y `os.rmdir`, cuyos eventos sí incluyen `dir_fd`, para impedir borrados fuera del temporal. Las lecturas de código y dependencias siguen permitidas como antes.

El reemplazo de `os.open` y el hook solo viven en el subproceso de pruebas. En Linux requieren `/proc/self/fd`, disponible en el contenedor comprobado. No se aplican a la aplicación desplegada. Debe ejecutarse Python sin `-O`, como en los comandos siguientes, para conservar las aserciones de aislamiento.

Referencias: [auditoría y dir_fd de os.open](https://docs.python.org/3.12/library/os.html#os.open), [limpieza de directorios con shutil.rmtree](https://docs.python.org/3.12/library/shutil.html#shutil.rmtree). La investigación incluyó la implementación real de `shutil._rmtree_safe_fd` en la imagen Linux con Python 3.12.16.

## Regresiones

Se comprueban aperturas válidas de PDF y SQLite temporales, rutas de tipo bytes, bloqueo de SQLite ajenos y en memoria, lectura del `instance` protegido, escrituras externas, prefijos parecidos al temporal y escapes con `..`. La limpieza reproduce un temporal con un subdirectorio llamado `instance` mientras el directorio de trabajo es el origen.

Las pruebas específicas de Linux comprueban aperturas y limpieza relativas a `dir_fd`, escapes mediante un descriptor externo, rutas absolutas con descriptor, descriptores inválidos y enlaces simbólicos hacia destinos protegidos. Los documentos protegidos de estas regresiones son ficticios y se comprueba desde el padre que conservan su contenido. Nunca se utiliza el `instance` real.

## Resultados

Comando en cada entorno de Windows: `python -B -m pytest -q -rs -p no:cacheprovider`.

| Entorno | Resultado |
| --- | --- |
| Windows, Python 3.14 | 16 tests y 39 subtests aprobados; 2 omitidos específicos de Linux |
| Windows, Python 3.12.16 | 16 tests y 39 subtests aprobados; 2 omitidos específicos de Linux |
| Docker Linux/amd64, Python 3.12.16 | 17 tests y 8 subtests aprobados; 1 omitido por ausencia de Node.js |

Para Linux se reutilizó `dashboard-compat-tests:7af268c`, derivada de la imagen construida con el Dockerfile original del commit 7af268c, y se superpusieron únicamente los dos archivos de pruebas. En una carpeta temporal se copiaron esos dos archivos y se pasó por stdin este Dockerfile de pruebas, sin modificar el del proyecto:

```dockerfile
FROM dashboard-compat-tests:7af268c
COPY test_facturas_integracion.py test_protector_rutas.py /app/tests/
```

Comandos de Docker (el contexto contiene exclusivamente esos dos archivos):

```powershell
docker build --platform linux/amd64 --progress plain -t dashboard-protector-tests:local -f - <contexto-temporal>
docker run --rm --platform linux/amd64 --network none --name dashboard-protector-linux -e PYTHONDONTWRITEBYTECODE=1 -e SECRET_KEY=solo-pruebas-docker -e FLASK_ENV=production dashboard-protector-tests:local python -B -m pytest -q -rs -p no:cacheprovider
```

No se montaron carpetas, volúmenes, secretos ni servicios de producción. La suite conserva sus SQLite y PDF temporales; el contenedor de ejecución se eliminó al terminar. Las imágenes de prueba permanecen locales.

## Prueba JavaScript omitida en Linux

`tests/test_calculo_partes.py::CalculoPartesTest::test_javascript_coincide_con_python` compara el JavaScript del formulario de partes con Python y requiere Node.js. No se ha instalado Node.js en la imagen de producción ni se ha cambiado el criterio de omisión. Esta prueba sí se ejecutó dentro de la suite Windows, donde Node ya está disponible, y explica la diferencia entre 39 y 8 subtests.

Se puede repetir desde ese entorno de pruebas Windows, independiente de producción:

```powershell
node --version
.\venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider tests/test_calculo_partes.py::CalculoPartesTest::test_javascript_coincide_con_python
```

La comprobación es del auxiliar y sus regresiones; no necesita abrir el Dashboard ni iniciar Flask. El Agente 2 debe revisar esta entrega local antes de cualquier publicación.
