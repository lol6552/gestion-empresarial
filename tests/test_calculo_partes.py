"""Pruebas aisladas: codigo real de calculo, sin importar app/config ni usar BD.

Ejecutar: python -B -m unittest discover -s tests -v
Requiere Node.js para contrastar el JavaScript real con Python.
"""
import ast
import json
from datetime import date, time
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace
import unittest

RAIZ = Path(__file__).resolve().parents[1]


def arbol(nombre):
    return ast.parse((RAIZ / nombre).read_text(encoding="utf-8"))


def cargar_modelo():
    # Solo metodos de calculo: nunca se importa SQLAlchemy ni se abre SQLite.
    clase = next(n for n in arbol("models/parte.py").body
                 if isinstance(n, ast.ClassDef) and n.name == "ParteTrabajo")
    clase.bases = []
    clase.body = [n for n in clase.body if isinstance(n, ast.FunctionDef)
                  and n.name.startswith("calcular_")]
    espacio = {"Decimal": Decimal, "ROUND_HALF_UP": ROUND_HALF_UP}
    exec(compile(ast.Module(body=[clase], type_ignores=[]), "modelo_aislado", "exec"), espacio)
    return espacio["ParteTrabajo"]


MODELO = cargar_modelo()


def calcular_ruta(nombre, minutos, tarifa, materiales="0", horas_desp="0", precio_desp="0"):
    # Ejecuta las asignaciones monetarias originales de alta o edicion.
    funcion = next(n for n in arbol("routes/partes.py").body
                   if isinstance(n, ast.FunctionDef) and n.name == nombre)
    campos = {"subtotal_trabajo", "subtotal_desplazamiento", "subtotal_general", "iva", "total"}
    nodos = [n for n in ast.walk(funcion) if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id in campos for t in n.targets)]
    nodos.sort(key=lambda n: n.lineno)
    assert len(nodos) == 5
    espacio = dict(Decimal=Decimal, ROUND_HALF_UP=ROUND_HALF_UP, ParteTrabajo=MODELO,
                   hora_inicio=time(9), hora_fin=time(9 + minutos // 60, minutos % 60),
                   precio_hora_trabajo=Decimal(tarifa), materiales_importe=Decimal(materiales),
                   horas_desplazamiento=Decimal(horas_desp),
                   precio_hora_desplazamiento=Decimal(precio_desp), IVA_PORCENTAJE=21)
    exec(compile(ast.Module(body=nodos, type_ignores=[]), "ruta_aislada", "exec"), espacio)
    return {campo: espacio[campo] for campo in campos}


def calcular_js(casos):
    # Ejecuta el script real con un DOM ficticio; no abre navegador ni servidor.
    plantilla = (RAIZ / "templates/partes/formulario.html").read_text(encoding="utf-8")
    script = plantilla.split("<script>")[-1].split("</script>")[0]
    programa = r"""
const vm = require('node:vm');
const fs = require('node:fs');
const entrada = JSON.parse(fs.readFileSync(0, 'utf8'));
const salida = entrada.casos.map(caso => {
    const elementos = {};
    const valores = {
        hora_inicio: caso.inicio || '09:00',
        hora_fin: caso.fin,
        precio_hora_trabajo: caso.tarifa,
        horas_desplazamiento: caso.horasDesp || '0',
        precio_hora_desplazamiento: caso.precioDesp || '0'
    };
    const documento = {
        addEventListener() {},
        getElementById(id) {
            return elementos[id] ||= {value: valores[id] || '', textContent: ''};
        },
        querySelectorAll() {
            return [{querySelector(selector) {
                return {value: selector === '.cantidad-input' ? '1' : (caso.materiales || '0')};
            }}];
        }
    };
    const contexto = vm.createContext({document: documento});
    vm.runInContext(entrada.script, contexto);
    vm.runInContext('calcularTotales()', contexto);
    return Object.fromEntries(Object.entries(elementos).map(([k, v]) => [k, v.textContent]));
});
process.stdout.write(JSON.stringify(salida));
"""
    proceso = subprocess.run([shutil.which("node"), "-e", programa],
                             input=json.dumps({"script": script, "casos": casos}),
                             text=True, capture_output=True, check=True)
    return json.loads(proceso.stdout)


class CalculoPartesTest(unittest.TestCase):
    def test_duraciones_solicitadas_alta_y_edicion(self):
        esperados = {20: ("11.67", "2.45", "14.12"),
                     30: ("17.50", "3.68", "21.18"),
                     45: ("26.25", "5.51", "31.76"),
                     60: ("35.00", "7.35", "42.35")}
        for ruta in ("nuevo", "editar"):
            for minutos, valores in esperados.items():
                with self.subTest(ruta=ruta, minutos=minutos):
                    resultado = calcular_ruta(ruta, minutos, "35")
                    self.assertEqual(tuple(resultado[c] for c in ("subtotal_trabajo", "iva", "total")),
                                     tuple(map(Decimal, valores)))
                    self.assertEqual(resultado["total"], resultado["subtotal_general"] + resultado["iva"])

    def test_medio_centimo_y_otros_campos(self):
        for ruta in ("nuevo", "editar"):
            self.assertEqual(calcular_ruta(ruta, 1, "0.30")["subtotal_trabajo"], Decimal("0.01"))
            resultado = calcular_ruta(ruta, 20, "35", "12.34", "0.5", "10")
            self.assertEqual(resultado["subtotal_desplazamiento"], Decimal("5"))
            self.assertEqual(resultado["subtotal_general"], Decimal("29.01"))
            self.assertEqual(resultado["iva"], Decimal("6.09"))
            self.assertEqual(resultado["total"], Decimal("35.10"))

    def test_medianoche_e_intervalos_invalidos_siguen_rechazados(self):
        for inicio, fin in ((time(23, 50), time(0, 10)), (time(9), time(9)), (time(10), time(9))):
            with self.assertRaises(ValueError):
                MODELO.calcular_importe_trabajo(inicio, fin, Decimal("35"))
        for nombre in ("nuevo", "editar"):
            funcion = next(n for n in arbol("routes/partes.py").body
                           if isinstance(n, ast.FunctionDef) and n.name == nombre)
            self.assertTrue(any(isinstance(n, ast.If)
                                and ast.unparse(n.test) == "hora_fin <= hora_inicio"
                                and any(isinstance(r, ast.Return) for r in ast.walk(n))
                                for n in ast.walk(funcion)))

    @unittest.skipUnless(shutil.which("node"), "Node.js no disponible")
    def test_javascript_coincide_con_python(self):
        casos = []
        for minutos in (1, 20, 30, 45, 59, 60):
            for tarifa in ("0.30", "1.005", "19.99", "35", "99.99"):
                casos.append(dict(fin=f"{9 + minutos // 60:02}:{minutos % 60:02}",
                                  tarifa=tarifa, minutos=minutos))
        casos.append(dict(fin="09:20", tarifa="35", minutos=20,
                          materiales="12.34", horasDesp="0.5", precioDesp="10"))
        for caso, vista in zip(casos, calcular_js(casos)):
            with self.subTest(caso=caso):
                resultado = calcular_ruta("nuevo", caso["minutos"], caso["tarifa"],
                                         caso.get("materiales", "0"), caso.get("horasDesp", "0"),
                                         caso.get("precioDesp", "0"))
                for campo, elemento in (("subtotal_trabajo", "subtotal-trabajo-display"),
                                        ("subtotal_general", "subtotal-display"),
                                        ("iva", "iva-display"), ("total", "total-display")):
                    self.assertEqual(Decimal(vista[elemento].split()[0]), resultado[campo])
        vista = calcular_js([dict(inicio="23:50", fin="00:10", tarifa="35")])[0]
        self.assertEqual(Decimal(vista["subtotal-trabajo-display"].split()[0]), Decimal("0.00"))

    def test_conversion_factura_conserva_importe_incluso_historico(self):
        funcion = next(n for n in arbol("routes/facturas.py").body
                       if isinstance(n, ast.FunctionDef) and n.name == "desde_parte")
        funcion.decorator_list = []
        class ConsultaFicticia:
            def order_by(self, *args): return self
            def all(self): return []
        consulta = ConsultaFicticia()
        for importe in ("11.67", "11.55"):
            parte = SimpleNamespace(hora_inicio=time(9), hora_fin=time(9, 20),
                                    horas_trabajo=Decimal("0.33"), precio_hora_trabajo=Decimal("35"),
                                    subtotal_trabajo=Decimal(importe), partidas=consulta,
                                    incluye_desplazamiento=False, cliente_id=1, numero="PRUEBA-001")
            espacio = dict(ParteTrabajo=SimpleNamespace(query=SimpleNamespace(get_or_404=lambda _: parte)),
                           Cliente=SimpleNamespace(query=consulta, apellido=SimpleNamespace(asc=lambda: None)),
                           PartePartida=SimpleNamespace(orden=None), request=SimpleNamespace(method="GET"),
                           date=date, render_template=lambda plantilla, **datos: datos)
            exec(compile(ast.Module(body=[funcion], type_ignores=[]), "conversion_aislada", "exec"), espacio)
            linea = espacio["desde_parte"](1)["partidas_precargadas"][0]
            self.assertEqual(Decimal(linea["cantidad"]) * Decimal(linea["precio"]), Decimal(importe))
            self.assertIn("20 min", linea["descripcion"])
            self.assertEqual(parte.subtotal_trabajo, Decimal(importe))

    def test_sintaxis_archivos_python(self):
        for nombre in ("models/parte.py", "routes/partes.py", "routes/facturas.py"):
            compile(arbol(nombre), nombre, "exec")


if __name__ == "__main__":
    unittest.main()
