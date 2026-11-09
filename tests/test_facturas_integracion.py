"""Regresion con Flask real y SQLite temporal, sin importar la aplicacion original.

Ejecutar con el entorno del proyecto:
python -B -m unittest discover -s tests -v
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


class FacturasIntegracionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Otro proceso evita compartir modulos, variables o conexiones con otras pruebas.
        resultado = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), "--aislado"],
                                   capture_output=True, text=True, timeout=60)
        if resultado.returncode:
            raise AssertionError(resultado.stdout + resultado.stderr)
        cls.resultados = json.loads(resultado.stdout)

    def test_flujos_completos_20_30_45_60(self):
        self.assertEqual(len(self.resultados), 4)
        self.assertTrue(all(r["flujos_ok"] for r in self.resultados))

    def test_relaciones_clientes_validas_e_incorrectas(self):
        self.assertTrue(all(r["clientes_ok"] for r in self.resultados))

    def test_regresion_iva_30_minutos_persistido(self):
        caso = next(r for r in self.resultados if r["minutos"] == 30)
        self.assertEqual(caso["subtotal"], "17.50")
        self.assertEqual(caso["iva"], "3.68")
        self.assertEqual(caso["total"], "21.18")


def ejecutar_aislado(comprobaciones=None):
    import shutil
    import tempfile
    from decimal import Decimal
    from html.parser import HTMLParser
    origen = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="flask_iva_regresion_") as carpeta:
        temporal = Path(carpeta).resolve()
        assert temporal.parent == Path(tempfile.gettempdir()).resolve()
        for nombre in ("app.py", "config.py", "version.py"):
            shutil.copy2(origen / nombre, temporal / nombre)
        for nombre in ("models", "routes", "utils", "templates"):
            shutil.copytree(origen / nombre, temporal / nombre,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        # No copiar instance, firmas, datos reales ni el entorno virtual.
        base = temporal / "instance" / "prueba.db"
        os.environ.update(DATABASE_URL="sqlite:///" + base.as_posix(),
                          SECRET_KEY="clave-ficticia-prueba", FLASK_ENV="production")
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(temporal))
        os.chdir(temporal)

        def proteger(evento, argumentos):
            if evento == "sqlite3.connect":
                assert Path(argumentos[0]).resolve() == base, "Conexion SQLite no autorizada"
            if evento == "open" and isinstance(argumentos[0], (str, bytes, os.PathLike)):
                ruta = Path(argumentos[0]).resolve()
                assert not ruta.is_relative_to(origen / "instance"), "Acceso a instance real bloqueado"
                modo, flags = argumentos[1:3]
                escritura = ((isinstance(modo, str) and any(c in modo for c in "wax+")) or
                             (isinstance(flags, int) and flags &
                              (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)))
                if escritura:
                    assert ruta.is_relative_to(temporal), "Escritura fuera del temporal bloqueada"
        sys.addaudithook(proteger)
        import config
        assert Path(config.INSTANCE_DIR).resolve() == temporal / "instance"
        config.AUTONOMO = {clave: "FICTICIO" for clave in config.AUTONOMO}
        import app
        from models import db, Cliente, ParteTrabajo, Factura, Oferta, OfertaPartida, Numerador
        assert Path(app.__file__).resolve() == temporal / "app.py"
        aplicacion = app.crear_app()
        aplicacion.config.update(TESTING=True)
        cliente_http = aplicacion.test_client()
        resultados = []

        class Campos(HTMLParser):
            def __init__(self): super().__init__(); self.datos = {}
            def handle_starttag(self, etiqueta, atributos):
                atributos = dict(atributos)
                if etiqueta == "input" and "name" in atributos:
                    self.datos.setdefault(atributos["name"], []).append(atributos.get("value", ""))

        def enviar(ruta, datos):
            respuesta = cliente_http.post(ruta, data=datos, follow_redirects=True)
            assert respuesta.status_code == 200, ruta

        def estado_facturas():
            # Comparar tambien partidas y numeradores: un rechazo no debe escribir nada.
            db.session.expire_all()
            return (
                [(tuple(getattr(f, c.name) for c in Factura.__table__.columns),
                  [tuple(getattr(p, c.name) for c in p.__table__.columns)
                   for p in f.partidas.order_by("id").all()])
                 for f in Factura.query.order_by(Factura.id).all()],
                [(n.tipo_documento, n.ultimo_numero)
                 for n in Numerador.query.order_by(Numerador.id).all()]
            )

        def rechazar(ruta, datos):
            anterior = estado_facturas()
            respuesta = cliente_http.post(ruta, data=datos)
            assert respuesta.status_code == 400, (ruta, respuesta.status_code)
            assert estado_facturas() == anterior, "El rechazo ha alterado datos"

        def comprobar_factura(identificador, esperados):
            db.session.expire_all()  # Volver a leer lo persistido en SQLite.
            factura = db.session.get(Factura, identificador)
            valores = (factura.subtotal, factura.iva, factura.total)
            assert valores == esperados, (identificador, valores, esperados)
            assert factura.total == factura.subtotal + factura.iva, valores
            return factura

        with aplicacion.app_context():
            try:
                assert Path(db.engine.url.database).resolve() == base
                cliente = Cliente(codigo="CLI-FICTICIO", nombre="Cliente", apellido="Ficticio",
                                  dni="PRUEBA", telefono="000000000", direccion="Calle ficticia",
                                  codigo_postal="00000", localidad="Ciudad ficticia")
                otro_cliente = Cliente(codigo="CLI-OTRO", nombre="Otro", apellido="Ficticio",
                                       dni="OTRA-PRUEBA", telefono="000000001", direccion="Otra calle",
                                       codigo_postal="00000", localidad="Otra ciudad")
                db.session.add_all([cliente, otro_cliente]); db.session.commit()
                assert cliente_http.get("/version").status_code == 200
                esperados = {20: ("11.67", "2.45", "14.12"), 30: ("17.50", "3.68", "21.18"),
                             45: ("26.25", "5.51", "31.76"), 60: ("35.00", "7.35", "42.35")}
                for minutos, importes in esperados.items():
                    importes = tuple(map(Decimal, importes))
                    datos = dict(cliente_id=str(cliente.id), fecha_realizacion="2026-01-15",
                                 descripcion="Trabajo ficticio", hora_inicio="09:00", hora_fin="10:00",
                                 precio_hora_trabajo="35", horas_desplazamiento="0",
                                 precio_hora_desplazamiento="0",
                                 **{"partida_descripcion[]": [""], "partida_cantidad[]": ["1"],
                                    "partida_precio[]": ["0"]})
                    datos["hora_fin"] = f"{9 + minutos // 60:02}:{minutos % 60:02}"
                    assert cliente_http.get("/partes/nuevo").status_code == 200
                    enviar("/partes/nuevo", datos)
                    parte = ParteTrabajo.query.order_by(ParteTrabajo.id.desc()).first()
                    db.session.refresh(parte)
                    assert (parte.subtotal_general, parte.iva, parte.total) == importes
                    # Editar realmente la duracion y volver al caso solicitado.
                    datos_alternativos = dict(datos, hora_fin="09:10")
                    enviar(f"/partes/editar/{parte.id}", datos_alternativos)
                    enviar(f"/partes/editar/{parte.id}", datos)
                    db.session.refresh(parte)
                    assert (parte.subtotal_general, parte.iva, parte.total) == importes
                    assert parte.total == parte.subtotal_general + parte.iva
                    formulario = dict(cliente_id=str(cliente.id), fecha="2026-01-15",
                                      descripcion="Factura ficticia", forma_pago="transferencia",
                                      **{"partida_descripcion[]": ["Mano de obra ficticia"],
                                         "partida_cantidad[]": ["1"], "partida_precio[]": [str(importes[0])]})
                    # Creacion manual y edicion usan el mismo procesador.
                    enviar("/facturas/nueva", formulario)
                    factura = Factura.query.order_by(Factura.id.desc()).first()
                    comprobar_factura(factura.id, importes)
                    enviar(f"/facturas/editar/{factura.id}", dict(formulario, descripcion="Editada ficticia"))
                    comprobar_factura(factura.id, importes)
                    # Una factura manual puede cambiar a otro cliente existente.
                    enviar(f"/facturas/editar/{factura.id}", dict(formulario, cliente_id=str(otro_cliente.id)))
                    db.session.refresh(factura)
                    assert factura.cliente_id == otro_cliente.id
                    for cliente_invalido in ("999999", "no-es-un-id", "0"):
                        rechazar("/facturas/nueva", dict(formulario, cliente_id=cliente_invalido))
                        rechazar(f"/facturas/editar/{factura.id}", dict(formulario, cliente_id=cliente_invalido))
                    # Leer el formulario real de conversion y enviar sus partidas.
                    respuesta = cliente_http.get(f"/facturas/desde-parte/{parte.id}")
                    assert respuesta.status_code == 200
                    campos = Campos(); campos.feed(respuesta.get_data(as_text=True))
                    convertido = dict(formulario)
                    for campo in ("partida_descripcion[]", "partida_cantidad[]", "partida_precio[]"):
                        convertido[campo] = campos.datos[campo]
                    rechazar(f"/facturas/desde-parte/{parte.id}",
                             dict(convertido, cliente_id=str(otro_cliente.id)))
                    enviar(f"/facturas/desde-parte/{parte.id}", convertido)
                    factura = Factura.query.order_by(Factura.id.desc()).first()
                    comprobar_factura(factura.id, importes)
                    assert factura.parte_id == parte.id
                    rechazar(f"/facturas/editar/{factura.id}",
                             dict(convertido, cliente_id=str(otro_cliente.id)))
                    enviar(f"/facturas/editar/{factura.id}", dict(convertido, descripcion="Convertida editada"))
                    comprobar_factura(factura.id, importes)
                    # Conversion desde oferta: comprobar la otra entrada del procesador.
                    oferta = Oferta(numero=f"OFERTA-PRUEBA-{minutos}", cliente_id=cliente.id,
                                    subtotal=importes[0], iva=importes[1], total=importes[2], estado="aceptada")
                    db.session.add(oferta); db.session.flush()
                    db.session.add(OfertaPartida(oferta_id=oferta.id, descripcion="Servicio ficticio",
                                                precio=importes[0], cantidad=Decimal("1"), total=importes[0]))
                    db.session.commit()
                    rechazar(f"/facturas/desde-oferta/{oferta.id}",
                             dict(formulario, cliente_id=str(otro_cliente.id)))
                    enviar(f"/facturas/desde-oferta/{oferta.id}", formulario)
                    factura = Factura.query.order_by(Factura.id.desc()).first()
                    comprobar_factura(factura.id, importes)
                    assert factura.oferta_id == oferta.id
                    rechazar(f"/facturas/editar/{factura.id}",
                             dict(formulario, cliente_id=str(otro_cliente.id)))
                    enviar(f"/facturas/editar/{factura.id}", formulario)
                    comprobar_factura(factura.id, importes)
                    # HTML usa los valores ya guardados; sin generar PDF ni ejecutar navegador.
                    from flask import render_template
                    html = render_template("facturas/pdf.html", factura=factura,
                                           partidas=factura.partidas.all(), autonomo=config.AUTONOMO,
                                           iva_porcentaje=21, config_formas_pago=config.FORMAS_PAGO, url_firma=None)
                    assert str(importes[1]) in html and str(importes[2]) in html
                    resultados.append(dict(minutos=minutos, subtotal=str(importes[0]),
                                           iva=str(importes[1]), total=str(importes[2]), flujos_ok=True, clientes_ok=True))
                if comprobaciones is not None:
                    comprobaciones(aplicacion, db, cliente_http)
            finally:
                db.session.remove(); db.engine.dispose()
                os.chdir(origen)
        print(json.dumps(resultados))


if __name__ == "__main__":
    if "--aislado" in sys.argv:
        ejecutar_aislado()
    else:
        unittest.main()
