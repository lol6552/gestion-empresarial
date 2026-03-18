import os
from playwright.sync_api import sync_playwright
from flask import render_template
import tempfile
from pathlib import Path

def setup_playwright():
    """
    Instala los navegadores necesarios si no existen.
    Esto idealmente debería correrse en el build/setup, no en cada ejecución,
    pero lo incluimos aquí por seguridad en este entorno dev.
    """
    # En producción, esto se maneja externamente.
    pass

def html_to_pdf(html_content, output_path):
    """
    Genera un PDF a partir de contenido HTML usando Playwright.
    
    Parámetros:
        html_content (str): String con el HTML completo a renderizar
        output_path (str): Ruta donde guardar el PDF final
    """
    with sync_playwright() as p:
        # Lanzamos navegador (chromium es ligero y standard)
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Establecemos el contenido
        #waitUntil='networkidle' asegura que se carguen recursos externos si los hay
        page.set_content(html_content, wait_until='networkidle')
        
        # Opcional: inyectar CSS específico para impresión si no está en el HTML
        # page.add_style_tag(content="@page { size: A4; margin: 0; }")
        
        # Generar PDF
        # format='A4' y print_background=True son estándar para facturas
        page.pdf(
            path=output_path,
            format='A4',
            print_background=True,
            margin={'top': '0px', 'bottom': '0px', 'left': '0px', 'right': '0px'}
        )
        
        browser.close()
    
    return output_path
