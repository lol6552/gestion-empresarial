"""KPIs y series sin IVA con la aplicación copiada y SQLite temporal protegido."""
import subprocess
import sys
from pathlib import Path
import unittest


class DashboardIvaTest(unittest.TestCase):
    def test_metricas_en_sqlite_aislado(self):
        resultado = subprocess.run([sys.executable, '-B', str(Path(__file__).resolve()), '--aislado'],
                                   capture_output=True, text=True, timeout=60)
        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)


def comprobar(aplicacion, db, cliente_http):
    from datetime import datetime, timezone
    from decimal import Decimal
    from unittest.mock import patch
    from models import Factura, Cliente
    import routes.principal as principal

    # El auxiliar ya ha creado facturas ficticias para otras comprobaciones.
    # Usar un año exclusivo evita alterar esos registros.
    cliente = Cliente.query.first()
    filas = [
        ('ANT', datetime(2031, 12, 31, 23, 59, 59), '50', '5'),
        ('ENE', datetime(2032, 1, 1), '100', '21'),
        ('MAR', datetime(2032, 3, 31, 23, 59, 59), '200', '42'),
        ('ABR', datetime(2032, 4, 1), '100', '10'),
        ('JUN', datetime(2032, 6, 30, 23, 59, 59), '200', '42'),
        ('JUL1', datetime(2032, 7, 1), '100', '21'),
        ('JUL2', datetime(2032, 7, 31, 23, 59, 59), '200', '42'),
        ('SEP', datetime(2032, 9, 30, 23, 59, 59), '40', '4'),
        ('OCT', datetime(2032, 10, 1), '100', '10'),
        ('DIC', datetime(2032, 12, 31, 23, 59, 59), '200', '42'),
        ('SIG', datetime(2033, 1, 1), '100', '4'),
    ]
    for i, (numero, fecha, base, iva) in enumerate(filas):
        base, iva = Decimal(base), Decimal(iva)
        db.session.add(Factura(numero='IVA-'+numero, cliente_id=cliente.id, fecha=fecha,
                               subtotal=base, iva=iva, total=base+iva,
                               forma_pago='efectivo', pagada=bool(i % 2)))
    db.session.commit()
    antes = [(f.id, f.fecha, f.subtotal, f.iva, f.total, f.pagada)
             for f in Factura.query.order_by(Factura.id)]
    casos = [
        (datetime(2032, 1, 1), 1, '63.00', 'abril', 2032),
        (datetime(2032, 4, 1), 2, '52.00', 'julio', 2032),
        (datetime(2032, 7, 1), 3, '67.00', 'octubre', 2032),
        (datetime(2032, 12, 31), 4, '52.00', 'enero', 2033),
        (datetime(2033, 1, 1), 1, '4.00', 'abril', 2033),
        (datetime(2033, 4, 1), 2, '0.00', 'julio', 2033),
    ]
    for hoy, trimestre, iva, mes, anio in casos:
        with patch.object(principal, 'fecha_actual_madrid', return_value=hoy):
            kpis = principal.obtener_kpis_facturacion()
            assert kpis['hucha_iva'] == Decimal(iva), kpis
            assert isinstance(kpis['hucha_iva'], Decimal)
            assert (kpis['trimestre'], kpis['mes_presentacion'], kpis['anio_presentacion']) == (trimestre, mes, anio)
            assert kpis['total_anio_actual'] == Decimal('1240' if hoy.year == 2032 else '100')
            respuesta = cliente_http.get('/')
            assert respuesta.status_code == 200
            html = respuesta.get_data(as_text=True)
            assert iva.replace('.', ',') + ' €' in html
            assert 'Facturación anual (sin IVA)' in html
            assert "label: 'Facturación sin IVA (€)'" in html
            assert 'Euros (sin IVA)' in html
            assert f'Declaración ordinaria en {mes} {anio}' in html
    kpis = principal.obtener_kpis_facturacion(datetime(2032, 1, 20))
    assert kpis['total_mes_actual'] == Decimal('100.00')  # 121 con IVA
    kpis = principal.obtener_kpis_facturacion(datetime(2032, 7, 31))
    assert kpis['total_mes_actual'] == Decimal('300.00')
    datos = principal.obtener_facturacion_mensual(datetime(2032, 7, 31))
    mapa = dict(zip(datos['etiquetas'], datos['valores']))
    assert mapa['Jul 32'] == 300.0  # 363 con IVA
    assert mapa['Feb 32'] == 0.0
    assert len(datos['etiquetas']) == 24
    assert len(set(datos['etiquetas'])) == 24
    total = sum((f.subtotal for f in Factura.query), Decimal('0'))
    assert kpis['ticket_medio'] == (total / Factura.query.count()).quantize(Decimal('.01'))

    # UTC aún en junio/diciembre; Madrid ya en julio/enero.
    for utc, esperado in [(datetime(2032, 6, 30, 22, 30, tzinfo=timezone.utc), datetime(2032, 7, 1, 0, 30)),
                           (datetime(2032, 12, 31, 23, 30, tzinfo=timezone.utc), datetime(2033, 1, 1, 0, 30))]:
        class Reloj(datetime):
            @classmethod
            def now(cls, tz=None):
                return utc.astimezone(tz)
        with patch.object(principal, 'datetime', Reloj):
            assert principal.fecha_actual_madrid() == esperado
    despues = [(f.id, f.fecha, f.subtotal, f.iva, f.total, f.pagada)
               for f in Factura.query.order_by(Factura.id)]
    assert antes == despues


if __name__ == '__main__':
    if '--aislado' in sys.argv:
        from test_facturas_integracion import ejecutar_aislado
        ejecutar_aislado(comprobar)
    else:
        unittest.main()
