# Sistema de Gestión Empresarial

Aplicación web Flask para gestión de clientes, ofertas, partes de trabajo y facturas con generación de PDFs.

## Requisitos Previos

### Para ejecutar con Docker (recomendado)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado

### Para ejecutar sin Docker
- Python 3.12 o superior
- pip (gestor de paquetes de Python)

---

## Instalación y Ejecución con Docker

### Primer uso

```powershell
# 1. Abrir terminal en la carpeta del proyecto
cd c:\Users\local_1\Documents\APP_V1

# 2. Construir la imagen Docker (puede tardar unos minutos la primera vez)
docker-compose build

# 3. Iniciar el contenedor
docker-compose up -d
```

### Acceso a la aplicación

- **Desde el mismo ordenador**: http://localhost:5000
- **Desde otros dispositivos en la red**: 
  1. Obtén la IP de tu ordenador ejecutando `ipconfig` en PowerShell
  2. Accede desde el otro dispositivo a `http://[TU_IP]:5000`

### Comandos útiles

```powershell
# Ver estado del contenedor
docker-compose ps

# Ver logs en tiempo real
docker-compose logs -f

# Detener la aplicación
docker-compose down

# Reiniciar después de cambios en el código
docker-compose down
docker-compose build
docker-compose up -d
```

---

## Instalación sin Docker (desarrollo local)

```powershell
# 1. Crear entorno virtual
python -m venv venv

# 2. Activar entorno virtual
.\venv\Scripts\Activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Instalar navegador para PDFs
playwright install chromium

# 5. Ejecutar la aplicación
python app.py
```

---

## Estructura del Proyecto

```
APP_V1/
├── app.py                 # Punto de entrada de la aplicación
├── config.py              # Configuración centralizada
├── requirements.txt       # Dependencias de Python
├── Dockerfile             # Definición de imagen Docker
├── docker-compose.yml     # Orquestación de contenedor
├── .dockerignore          # Archivos excluidos de Docker
│
├── models/                # Modelos de base de datos
│   ├── cliente.py
│   ├── oferta.py
│   ├── parte.py
│   ├── factura.py
│   └── numerador.py
│
├── routes/                # Rutas y lógica de negocio
│   ├── principal.py       # Dashboard
│   ├── clientes.py
│   ├── ofertas.py
│   ├── partes.py
│   └── facturas.py
│
├── templates/             # Plantillas HTML (Jinja2)
│   ├── base.html
│   ├── dashboard.html
│   ├── clientes/
│   ├── ofertas/
│   ├── partes/
│   └── facturas/
│
├── static/                # Archivos estáticos
│   ├── css/style.css
│   └── img/
│
├── instance/              # Datos persistentes (NO incluido en Docker)
│   ├── database.db        # Base de datos SQLite
│   └── pdfs/              # PDFs generados
│
└── utils/                 # Utilidades
    └── pdf_generator.py   # Generación de PDFs con Playwright
```

---

## Datos Persistentes

Los siguientes datos se mantienen **fuera del contenedor Docker** mediante volúmenes:

| Carpeta | Contenido |
|---------|-----------|
| `instance/database.db` | Base de datos SQLite con todos los datos |
| `instance/pdfs/` | PDFs generados (facturas, ofertas, partes) |
| `static/img/` | Imágenes (firma, logos) |

Estos datos **no se pierden** al reiniciar o actualizar el contenedor.

---

## Solución de Problemas

### Error: "Docker is not running"
- Asegúrate de que Docker Desktop esté abierto y funcionando

### Error: "Port 5000 already in use"
- Otro programa está usando el puerto 5000
- Cambia el puerto en `docker-compose.yml`:
  ```yaml
  ports:
    - "5001:5000"  # Acceder en localhost:5001
  ```

### No puedo acceder desde otro dispositivo
1. Verifica que ambos dispositivos estén en la misma red WiFi
2. Comprueba el firewall de Windows (permite conexiones al puerto 5000)
3. Usa la IP correcta (ejecuta `ipconfig` para obtenerla)

### Los PDFs no se generan
- Verifica los logs: `docker-compose logs -f`
- Puede ser un problema de permisos en la carpeta `instance/pdfs/`

---

## Configuración

### Variables de entorno disponibles

| Variable | Valor por defecto | Descripción |
|----------|-------------------|-------------|
| `SECRET_KEY` | (desarrollo) | Clave secreta para sesiones |
| `SERVER_HOST` | `0.0.0.0` | Host del servidor |
| `SERVER_PORT` | `5000` | Puerto del servidor |
| `FLASK_ENV` | `development` | Entorno (development/production) |

Para cambiar estas variables, edita `docker-compose.yml`:

```yaml
environment:
  - SECRET_KEY=mi-clave-super-secreta
  - FLASK_ENV=production
```

---

## Datos del Autónomo

Los datos que aparecen en los PDFs se configuran en `config.py`:

```python
AUTONOMO = {
    'nombre': 'Javier Aranguren Meneses',
    'dni': '78784784J',
    'direccion': 'C/ Foz de Lumbier 1',
    'cuenta_bancaria': '89898 89898 8989',
    'profesion': 'Electricista·Pequeños arreglos',
    'telefono': '(55) 1234-5678',
    'email': 'hola@sitioincreible.com',
    'web': '@sitioincreible'
}
```

---

## Licencia

Uso privado - Sistema desarrollado para gestión empresarial personal.
