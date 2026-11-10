"""Regresiones del aislamiento con archivos ficticios y hooks en subprocesos."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class ProtectorRutasTest(unittest.TestCase):
    def ejecutar(self, caso):
        with tempfile.TemporaryDirectory(prefix="protector-regresion-") as carpeta:
            raiz = Path(carpeta)
            for nombre in ("fuente/instance/pdfs", "aislado/instance/pdfs",
                           "aislado/borrar/instance/pdfs", "exterior", "aislado-hermano"):
                (raiz / nombre).mkdir(parents=True, exist_ok=True)
            for nombre in ("fuente/instance/database.db", "fuente/instance/pdfs/documento.pdf",
                           "exterior/documento.pdf", "aislado/borrar/instance/pdfs/prueba.pdf"):
                (raiz / nombre).write_text("FICTICIO", encoding="utf-8")
            resultado = subprocess.run(
                [sys.executable, "-B", str(Path(__file__).resolve()), "--aislado", caso, str(raiz)],
                capture_output=True, text=True, timeout=30)
            self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)
            for nombre in ("fuente/instance/database.db", "fuente/instance/pdfs/documento.pdf",
                           "exterior/documento.pdf"):
                self.assertEqual((raiz / nombre).read_text(encoding="utf-8"), "FICTICIO")
            return resultado.stdout

    def test_permite_archivos_pdf_y_sqlite_temporales(self):
        self.ejecutar("permitidos")

    def test_bloquea_lectura_instance_y_sqlite_ajeno(self):
        self.ejecutar("instance_sqlite")

    def test_bloquea_escrituras_externas_bytes_y_traversal(self):
        self.ejecutar("escrituras")

    def test_limpieza_temporal_con_nombre_instance_desde_origen(self):
        self.ejecutar("limpieza")

    def test_bloquea_borrados_externos(self):
        self.ejecutar("borrados")

    @unittest.skipUnless(sys.platform == "linux", "dir_fd y /proc/self/fd requieren Linux")
    def test_dir_fd_resuelve_destino_real_y_rechaza_escapes(self):
        self.ejecutar("dir_fd")

    @unittest.skipUnless(sys.platform == "linux", "Enlaces simbolicos comprobados en Linux")
    def test_enlaces_simbolicos_no_eluden_el_aislamiento(self):
        self.ejecutar("enlaces")


def comprobar(caso, raiz):
    import shutil
    import sqlite3
    from test_facturas_integracion import instalar_protector

    origen, temporal = raiz / "fuente", raiz / "aislado"
    base = temporal / "instance/prueba.db"
    externo = raiz / "exterior/documento.pdf"
    protegido = origen / "instance/database.db"
    descriptores = []
    if caso == "enlaces":
        (temporal / "enlace-instance").symlink_to(origen / "instance", target_is_directory=True)
        (temporal / "enlace-externo").symlink_to(raiz / "exterior", target_is_directory=True)
    if caso == "dir_fd":
        descriptores = [os.open(ruta, os.O_RDONLY) for ruta in
                        (temporal, origen / "instance", raiz / "exterior")]
    os.chdir(origen)  # Reproduce la colisión con fuente/instance durante rmtree.
    instalar_protector(origen, temporal, base)

    def bloqueado(operacion):
        try:
            operacion()
        except AssertionError:
            return
        raise AssertionError("El protector ha permitido una operación externa")

    def abrir_archivo(ruta, modo):
        with open(ruta, modo) as archivo:
            if modo == "rb":
                return archivo.read()
            archivo.write(b"PRUEBA")

    def abrir_fd(ruta, flags, **kwargs):
        descriptor = os.open(ruta, flags, **kwargs)
        os.close(descriptor)

    try:
        if caso == "permitidos":
            pdf = temporal / "instance/pdfs/nuevo.pdf"
            abrir_archivo(pdf, "wb")
            assert abrir_archivo(pdf, "rb") == b"PRUEBA"
            abrir_fd(os.fsencode(pdf), os.O_RDONLY)
            with sqlite3.connect(str(base)) as conexion:
                conexion.execute("CREATE TABLE ficticio (id INTEGER)")
            assert base.exists()
        elif caso == "instance_sqlite":
            for ruta in (protegido, os.fsencode(protegido), Path("instance/pdfs/documento.pdf")):
                bloqueado(lambda ruta=ruta: abrir_archivo(ruta, "rb"))
                bloqueado(lambda ruta=ruta: abrir_fd(ruta, os.O_RDONLY))
            for ruta in (protegido, temporal / "otra.db", externo, ":memory:",
                         "file:" + base.as_posix() + "?mode=ro"):
                bloqueado(lambda ruta=ruta: sqlite3.connect(str(ruta)))
        elif caso == "escrituras":
            for ruta in (externo, os.fsencode(externo), temporal / "../exterior/documento.pdf",
                         raiz / "aislado-hermano/nuevo.pdf", protegido):
                bloqueado(lambda ruta=ruta: abrir_archivo(ruta, "wb"))
                bloqueado(lambda ruta=ruta: abrir_fd(ruta, os.O_WRONLY | os.O_CREAT | os.O_TRUNC))
        elif caso == "limpieza":
            shutil.rmtree(temporal / "borrar")
            assert not (temporal / "borrar").exists()
            # Incluye la salida del gestor y el borrado de instance/prueba.db.
            sqlite3.connect(str(base)).close()
            shutil.rmtree(temporal)
            assert not temporal.exists()
        elif caso == "borrados":
            bloqueado(lambda: os.remove(externo))
            bloqueado(lambda: os.remove(protegido))
            bloqueado(lambda: os.rmdir(raiz / "exterior"))
            bloqueado(lambda: shutil.rmtree(origen / "instance"))
            bloqueado(lambda: shutil.rmtree(raiz / "exterior"))
        elif caso == "dir_fd":
            fd_temporal, fd_instance, fd_exterior = descriptores
            abrir_fd(b"instance/pdfs/relativo.pdf", os.O_WRONLY | os.O_CREAT, dir_fd=fd_temporal)
            abrir_fd("instance/pdfs/relativo.pdf", os.O_RDONLY, dir_fd=fd_temporal)
            bloqueado(lambda: abrir_fd("database.db", os.O_RDONLY, dir_fd=fd_instance))
            bloqueado(lambda: abrir_fd("documento.pdf", os.O_WRONLY, dir_fd=fd_exterior))
            bloqueado(lambda: abrir_fd("../exterior/documento.pdf", os.O_WRONLY, dir_fd=fd_temporal))
            bloqueado(lambda: abrir_fd(externo, os.O_WRONLY, dir_fd=fd_temporal))
            bloqueado(lambda: os.remove("documento.pdf", dir_fd=fd_exterior))
            bloqueado(lambda: shutil.rmtree("../exterior", dir_fd=fd_temporal))
            abrir_fd(temporal / "instance/pdfs/absoluto.pdf", os.O_WRONLY | os.O_CREAT, dir_fd=fd_exterior)
            shutil.rmtree("borrar", dir_fd=fd_temporal)
            assert not (temporal / "borrar").exists()
            bloqueado(lambda: abrir_fd("fichero", os.O_RDONLY, dir_fd=-123456))
        elif caso == "enlaces":
            bloqueado(lambda: abrir_archivo(temporal / "enlace-instance/database.db", "rb"))
            bloqueado(lambda: abrir_archivo(temporal / "enlace-externo/documento.pdf", "wb"))
            bloqueado(lambda: shutil.rmtree(temporal / "enlace-instance"))
            fd = os.open(temporal, os.O_RDONLY)
            try:
                bloqueado(lambda: abrir_fd("enlace-instance/database.db", os.O_RDONLY, dir_fd=fd))
                bloqueado(lambda: abrir_fd("enlace-externo/documento.pdf", os.O_WRONLY, dir_fd=fd))
            finally:
                os.close(fd)
        else:
            raise AssertionError(caso)
    finally:
        for descriptor in descriptores:
            os.close(descriptor)
        os.chdir(raiz)


if __name__ == "__main__":
    if "--aislado" in sys.argv:
        comprobar(sys.argv[2], Path(sys.argv[3]).resolve())
    else:
        unittest.main()
