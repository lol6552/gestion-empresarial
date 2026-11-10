"""Vista manual aislada: python tests/vista_dashboard_local.py. Salir con Ctrl+C."""
import os
from pathlib import Path
import shutil
import sys
import tempfile


def main():
    origen = Path(__file__).resolve().parents[1]
    anterior = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="dashboard-local-") as carpeta:
        temporal = Path(carpeta).resolve()
        for nombre in ("app.py", "config.py", "version.py"):
            shutil.copy2(origen / nombre, temporal / nombre)
        for nombre in ("models", "routes", "utils", "templates", "static"):
            # Los PDF admiten la ausencia de firma; no copiar las firmas originales.
            shutil.copytree(origen / nombre, temporal / nombre,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc",
                                                         "firma.png", "firma_v2.png"))
        base = temporal / "instance" / "prueba.db"
        os.environ.update(DATABASE_URL="sqlite:///" + base.as_posix(),
                          SECRET_KEY="solo-pruebas-locales", FLASK_ENV="production")
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(temporal))
        os.chdir(temporal)
        try:
            import config
            assert Path(config.INSTANCE_DIR).resolve() == temporal / "instance"
            config.AUTONOMO = {clave: "FICTICIO" for clave in config.AUTONOMO}
            from app import crear_app
            from models import db, Cliente, Factura
            from routes.principal import fecha_actual_madrid
            from decimal import Decimal
            aplicacion = crear_app()
            with aplicacion.app_context():
                assert db.engine.url.database == str(base).replace("\\", "/")
                cliente = Cliente(nombre="Cliente ficticio", apellido="Dashboard", dni="DEMO-LOCAL",
                                  telefono="000000000", direccion="Calle de pruebas 1",
                                  codigo_postal="00000", localidad="Localidad ficticia")
                db.session.add(cliente)
                db.session.flush()
                for numero, base_f, iva in ((1, "100.00", "21.00"), (2, "200.00", "42.00")):
                    base_f, iva = Decimal(base_f), Decimal(iva)
                    db.session.add(Factura(numero=f"DEMO-{numero}", cliente_id=cliente.id,
                                           fecha=fecha_actual_madrid(), subtotal=base_f, iva=iva,
                                           total=base_f + iva, forma_pago="efectivo", pagada=True))
                db.session.commit()
            print(f"Copia aislada: {temporal}", flush=True)
            print("http://127.0.0.1:5017 | Mes y año: 300.00 EUR | IVA: 63,00 EUR", flush=True)
            aplicacion.run(host="127.0.0.1", port=5017, debug=False, use_reloader=False)
        finally:
            if "aplicacion" in locals():
                with aplicacion.app_context():
                    db.session.remove()
                    db.engine.dispose()
            os.chdir(anterior)


if __name__ == "__main__":
    main()
