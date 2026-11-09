"""Calendario y recuperacion de formularios con Flask real y SQLite temporal."""
import subprocess
import sys
from pathlib import Path
import unittest


class DashboardFormulariosTest(unittest.TestCase):
    def test_calendario_y_formularios_en_sqlite_temporal(self):
        resultado = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), "--aislado"],
                                   capture_output=True, text=True, timeout=60)
        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)


def comprobar(aplicacion, db, cliente_http):
    from datetime import datetime
    from decimal import Decimal
    from html.parser import HTMLParser
    from unittest.mock import patch
    from models import Cliente, Factura, Oferta, ParteTrabajo, Numerador
    import routes.principal as principal

    clientes = Cliente.query.order_by(Cliente.id).all()
    cliente_id, otro_id = clientes[0].id, clientes[1].id
    for numero, fecha, total in (("CAL-FEB", datetime(2024, 2, 29), "123.45"),
                                  ("CAL-DIC", datetime(2024, 12, 31), "67.89"),
                                  ("CAL-ENE", datetime(2025, 1, 1), "10.00")):
        db.session.add(Factura(numero=numero, cliente_id=cliente_id, fecha=fecha,
                               subtotal=Decimal(total), iva=Decimal("0"), total=Decimal(total),
                               forma_pago="efectivo"))
    db.session.commit()
    escenarios = ((datetime(2024, 3, 31, 18), ["Ene 24", "Feb 24", "Mar 24"]),
                  (datetime(2025, 1, 1), ["Nov 24", "Dic 24", "Ene 25"]),
                  (datetime(2025, 3, 1), ["Ene 25", "Feb 25", "Mar 25"]))
    for hoy, ultimas in escenarios:
        class Reloj(datetime):
            @classmethod
            def now(cls, tz=None): return hoy
        with patch.object(principal, "datetime", Reloj):
            datos = principal.obtener_facturacion_mensual()
        assert datos["etiquetas"][-3:] == ultimas, datos
        assert len(datos["etiquetas"]) == len(set(datos["etiquetas"]))
        mapa = dict(zip(datos["etiquetas"], datos["valores"]))
        if "Feb 24" in mapa: assert mapa["Feb 24"] == 123.45
        if "Dic 24" in mapa: assert mapa["Dic 24"] == 67.89
        if "Ene 25" in mapa: assert mapa["Ene 25"] == 10.0

    class Formulario(HTMLParser):
        def __init__(self):
            super().__init__(); self.valores = {}; self.clientes = []; self.pagos = []
            self.textarea = None; self.textos = {}; self.select = None
        def handle_starttag(self, tag, attrs):
            a = dict(attrs)
            if tag == "input" and "name" in a:
                self.valores.setdefault(a["name"], []).append(a.get("value", ""))
                if a["name"] == "forma_pago" and "checked" in a: self.pagos.append(a["value"])
            if tag == "select": self.select = a.get("name")
            if tag == "option" and self.select == "cliente_id" and "selected" in a:
                self.clientes.append(a.get("value"))
            if tag == "textarea": self.textarea = a.get("name")
        def handle_data(self, data):
            if self.textarea: self.textos[self.textarea] = self.textos.get(self.textarea, "") + data
        def handle_endtag(self, tag):
            if tag == "textarea": self.textarea = None
            if tag == "select": self.select = None

    def estado():
        db.session.expire_all()
        salida = []
        for modelo in (Oferta, ParteTrabajo, Numerador):
            for registro in modelo.query.order_by(modelo.id).all():
                salida.append((modelo.__name__, tuple(getattr(registro, c.name) for c in modelo.__table__.columns)))
                if hasattr(registro, "partidas"):
                    salida.append([(tuple(getattr(p, c.name) for c in p.__table__.columns))
                                   for p in registro.partidas.order_by("id").all()])
        return salida

    for tipo, modelo, nuevo in (("ofertas", Oferta, "nueva"), ("partes", ParteTrabajo, "nuevo")):
        datos = dict(cliente_id=str(otro_id), descripcion='Notas <ficticias> & nuevas', forma_pago="bizum",
                     **{"partida_descripcion[]": ['Servicio <A> & uno', 'Material "B"', 'Linea nueva C'],
                        "partida_cantidad[]": ["2", "0.50", "3"],
                        "partida_precio[]": ["12.34", "7.80", "1.25"]})
        if tipo == "ofertas":
            datos.update(fecha="2026-01-15", fecha_vencimiento="2026-02-15")
            registro = modelo.query.first()
        else:
            datos.update(fecha_realizacion="2026-01-15", hora_inicio="09:00", hora_fin="09:20",
                         precio_hora_trabajo="35", horas_desplazamiento="0.5", precio_hora_desplazamiento="10")
            registro = modelo.query.first()
        # Los objetos guardados pertenecen al primer cliente; enviar el segundo al fallar.
        assert registro.cliente_id == cliente_id
        rutas = (f"/{tipo}/{nuevo}", f"/{tipo}/editar/{registro.id}")
        for ruta in rutas:
            campo_fecha = "fecha" if tipo == "ofertas" else "fecha_realizacion"
            errores = [dict(datos, **{campo_fecha: ""}),
                       dict(datos, **{campo_fecha: "2026-02-30"})]
            incompleto = dict(datos)
            incompleto["partida_precio[]"] = ["12.34", "7.80"]
            errores.append(incompleto)
            if tipo == "partes": errores.append(dict(datos, hora_fin="08:00"))
            for enviado in errores:
                anterior = estado()
                respuesta = cliente_http.post(ruta, data=enviado)
                assert respuesta.status_code == 200, (ruta, respuesta.status_code)
                html = respuesta.get_data(as_text=True)
                formulario = Formulario(); formulario.feed(html)
                for campo in ("partida_descripcion[]", "partida_cantidad[]", "partida_precio[]"):
                    esperado = list(enviado[campo])
                    if campo == "partida_precio[]" and len(esperado) < 3: esperado.append("")
                    assert formulario.valores[campo] == esperado, (ruta, campo, formulario.valores[campo])
                assert formulario.clientes == [str(otro_id)], (ruta, formulario.clientes)
                assert formulario.pagos == ["bizum"], (ruta, formulario.pagos)
                assert formulario.textos["descripcion"] == enviado["descripcion"]
                campos = ("fecha", "fecha_vencimiento") if tipo == "ofertas" else (
                    "fecha_realizacion", "hora_inicio", "hora_fin", "precio_hora_trabajo",
                    "horas_desplazamiento", "precio_hora_desplazamiento")
                for campo in campos:
                    assert formulario.valores[campo] == [enviado[campo]], (ruta, campo)
                assert "obligatori" in html or "Revisa" in html or "posterior" in html or "fecha no" in html
                assert estado() == anterior, "Se guardaron cambios durante un error"
            # Tras corregir el error se puede guardar sin perder las tres filas.
            respuesta = cliente_http.post(ruta, data=datos)
            assert respuesta.status_code == 302
            db.session.expire_all()
            guardado = modelo.query.order_by(modelo.id.desc()).first() if ruta.endswith(nuevo) else db.session.get(modelo, registro.id)
            assert guardado.cliente_id == otro_id
            assert guardado.partidas.count() == 3
            assert [p.descripcion for p in guardado.partidas.order_by("orden").all()] == datos["partida_descripcion[]"]


if __name__ == "__main__":
    if "--aislado" in sys.argv:
        from test_facturas_integracion import ejecutar_aislado
        ejecutar_aislado(comprobar)
    else:
        unittest.main()
