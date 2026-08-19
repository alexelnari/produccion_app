"""Genera los pictogramas PNG usados en los botones de la pantalla de inicio.

Se dibujan con Pillow (ImageDraw) en vez de partir de SVG: Pillow no sabe
leer SVG por si solo (haria falta una libreria de rasterizado adicional,
mas fragil de empaquetar con PyInstaller) y estos iconos son formas simples
que se dibujan igual de bien con primitivas de dibujo directas.

Se dibuja a 4x el tamano final y se reduce con LANCZOS para conseguir bordes
suaves (Pillow no antialiasa las formas por defecto).

Ejecutar una vez desde la carpeta produccion_app/:
    python scripts/generar_iconos.py
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "assets" / "icons"

TAMANO_FINAL = 96
ESCALA = 4
TAMANO = TAMANO_FINAL * ESCALA
GROSOR = 7 * ESCALA


def _lienzo():
    return Image.new("RGBA", (TAMANO, TAMANO), (0, 0, 0, 0))


def _guardar(img, nombre):
    img = img.resize((TAMANO_FINAL, TAMANO_FINAL), Image.LANCZOS)
    DESTINO.mkdir(parents=True, exist_ok=True)
    ruta = DESTINO / f"{nombre}.png"
    img.save(ruta)
    print(f"  {ruta.relative_to(RAIZ)}")


def icono_nuevo_dia(color):
    img = _lienzo()
    d = ImageDraw.Draw(img)
    m = TAMANO * 0.12
    d.ellipse([m, m, TAMANO - m, TAMANO - m], outline=color, width=GROSOR)
    cx, cy = TAMANO / 2, TAMANO / 2
    brazo = TAMANO * 0.22
    d.line([cx - brazo, cy, cx + brazo, cy], fill=color, width=GROSOR)
    d.line([cx, cy - brazo, cx, cy + brazo], fill=color, width=GROSOR)
    return img


def icono_abrir(color):
    img = _lienzo()
    d = ImageDraw.Draw(img)
    x0, y0 = TAMANO * 0.12, TAMANO * 0.30
    x1, y1 = TAMANO * 0.88, TAMANO * 0.82
    d.rounded_rectangle([x0, y0, x1, y1], radius=TAMANO * 0.04, outline=color, width=GROSOR)
    d.line([x0 + TAMANO * 0.04, y0, x0 + TAMANO * 0.04, y0 - TAMANO * 0.12], fill=color, width=GROSOR)
    d.line(
        [x0 + TAMANO * 0.04, y0 - TAMANO * 0.12, x0 + TAMANO * 0.40, y0 - TAMANO * 0.12],
        fill=color,
        width=GROSOR,
    )
    d.line([x0 + TAMANO * 0.40, y0 - TAMANO * 0.12, x0 + TAMANO * 0.50, y0], fill=color, width=GROSOR)
    return img


def icono_tolvas(color):
    img = _lienzo()
    d = ImageDraw.Draw(img)
    top_izq = (TAMANO * 0.10, TAMANO * 0.16)
    top_der = (TAMANO * 0.90, TAMANO * 0.16)
    medio_izq = (TAMANO * 0.40, TAMANO * 0.58)
    medio_der = (TAMANO * 0.60, TAMANO * 0.58)
    d.polygon([top_izq, top_der, medio_der, medio_izq], outline=color, width=GROSOR)
    d.line([medio_izq[0], medio_izq[1], TAMANO * 0.40, TAMANO * 0.88], fill=color, width=GROSOR)
    d.line([medio_der[0], medio_der[1], TAMANO * 0.60, TAMANO * 0.88], fill=color, width=GROSOR)
    return img


def icono_buscar(color):
    img = _lienzo()
    d = ImageDraw.Draw(img)
    cx, cy, r = TAMANO * 0.42, TAMANO * 0.42, TAMANO * 0.26
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=GROSOR)
    ang = 0.7071
    d.line(
        [cx + r * ang, cy + r * ang, TAMANO * 0.88, TAMANO * 0.88],
        fill=color,
        width=GROSOR,
    )
    return img


def icono_historico(color):
    img = _lienzo()
    d = ImageDraw.Draw(img)
    base = TAMANO * 0.86
    barras = [
        (TAMANO * 0.14, TAMANO * 0.58),
        (TAMANO * 0.42, TAMANO * 0.38),
        (TAMANO * 0.70, TAMANO * 0.18),
    ]
    ancho = TAMANO * 0.18
    for x, y in barras:
        d.rounded_rectangle([x, y, x + ancho, base], radius=TAMANO * 0.03, fill=color)
    return img


def icono_info(color):
    img = _lienzo()
    d = ImageDraw.Draw(img)
    m = TAMANO * 0.12
    d.ellipse([m, m, TAMANO - m, TAMANO - m], outline=color, width=GROSOR)
    cx = TAMANO / 2
    r_punto = TAMANO * 0.045
    cy_punto = TAMANO * 0.32
    d.ellipse(
        [cx - r_punto, cy_punto - r_punto, cx + r_punto, cy_punto + r_punto],
        fill=color,
    )
    d.line([cx, TAMANO * 0.46, cx, TAMANO * 0.74], fill=color, width=GROSOR)
    return img


def icono_guardar(color):
    img = _lienzo()
    d = ImageDraw.Draw(img)
    m = TAMANO * 0.14
    d.rounded_rectangle([m, m, TAMANO - m, TAMANO - m], radius=TAMANO * 0.06, outline=color, width=GROSOR)
    d.rectangle([TAMANO * 0.30, m, TAMANO * 0.70, TAMANO * 0.34], outline=color, width=GROSOR)
    d.line([TAMANO * 0.26, TAMANO * 0.62, TAMANO * 0.74, TAMANO * 0.62], fill=color, width=GROSOR)
    d.line([TAMANO * 0.26, TAMANO * 0.78, TAMANO * 0.74, TAMANO * 0.78], fill=color, width=GROSOR)
    return img


def icono_eliminar(color):
    img = _lienzo()
    d = ImageDraw.Draw(img)
    d.line([TAMANO * 0.20, TAMANO * 0.28, TAMANO * 0.80, TAMANO * 0.28], fill=color, width=GROSOR)
    d.line([TAMANO * 0.38, TAMANO * 0.28, TAMANO * 0.42, TAMANO * 0.16], fill=color, width=GROSOR)
    d.line([TAMANO * 0.42, TAMANO * 0.16, TAMANO * 0.58, TAMANO * 0.16], fill=color, width=GROSOR)
    d.line([TAMANO * 0.58, TAMANO * 0.16, TAMANO * 0.62, TAMANO * 0.28], fill=color, width=GROSOR)
    d.polygon(
        [
            (TAMANO * 0.26, TAMANO * 0.28), (TAMANO * 0.74, TAMANO * 0.28),
            (TAMANO * 0.68, TAMANO * 0.86), (TAMANO * 0.32, TAMANO * 0.86),
        ],
        outline=color, width=GROSOR,
    )
    d.line([TAMANO * 0.42, TAMANO * 0.40, TAMANO * 0.44, TAMANO * 0.76], fill=color, width=GROSOR)
    d.line([TAMANO * 0.58, TAMANO * 0.40, TAMANO * 0.56, TAMANO * 0.76], fill=color, width=GROSOR)
    return img


def icono_volver(color):
    img = _lienzo()
    d = ImageDraw.Draw(img)
    cy = TAMANO / 2
    d.line([TAMANO * 0.78, cy, TAMANO * 0.20, cy], fill=color, width=GROSOR)
    d.line([TAMANO * 0.20, cy, TAMANO * 0.42, TAMANO * 0.30], fill=color, width=GROSOR)
    d.line([TAMANO * 0.20, cy, TAMANO * 0.42, TAMANO * 0.70], fill=color, width=GROSOR)
    return img


def icono_documento(color):
    img = _lienzo()
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = TAMANO * 0.24, TAMANO * 0.12, TAMANO * 0.76, TAMANO * 0.88
    esquina = TAMANO * 0.16
    d.polygon(
        [(x0, y0), (x1 - esquina, y0), (x1, y0 + esquina), (x1, y1), (x0, y1)],
        outline=color, width=GROSOR,
    )
    d.line([(x1 - esquina, y0), (x1 - esquina, y0 + esquina), (x1, y0 + esquina)], fill=color, width=GROSOR)
    for i in range(3):
        yy = TAMANO * 0.44 + i * TAMANO * 0.14
        d.line([x0 + TAMANO * 0.10, yy, x1 - TAMANO * 0.10, yy], fill=color, width=int(GROSOR * 0.7))
    return img


def icono_aceptar(color):
    img = _lienzo()
    d = ImageDraw.Draw(img)
    d.line([TAMANO * 0.20, TAMANO * 0.52, TAMANO * 0.42, TAMANO * 0.74], fill=color, width=GROSOR)
    d.line([TAMANO * 0.42, TAMANO * 0.74, TAMANO * 0.82, TAMANO * 0.26], fill=color, width=GROSOR)
    return img


def icono_cancelar(color):
    img = _lienzo()
    d = ImageDraw.Draw(img)
    m = TAMANO * 0.24
    d.line([m, m, TAMANO - m, TAMANO - m], fill=color, width=GROSOR)
    d.line([TAMANO - m, m, m, TAMANO - m], fill=color, width=GROSOR)
    return img


def icono_exportar(color):
    img = _lienzo()
    d = ImageDraw.Draw(img)
    cx = TAMANO / 2
    d.line([cx, TAMANO * 0.14, cx, TAMANO * 0.58], fill=color, width=GROSOR)
    d.line([cx, TAMANO * 0.58, TAMANO * 0.34, TAMANO * 0.40], fill=color, width=GROSOR)
    d.line([cx, TAMANO * 0.58, TAMANO * 0.66, TAMANO * 0.40], fill=color, width=GROSOR)
    d.line([TAMANO * 0.18, TAMANO * 0.78, TAMANO * 0.82, TAMANO * 0.78], fill=color, width=GROSOR)
    return img


def icono_imprimir(color):
    img = _lienzo()
    d = ImageDraw.Draw(img)
    d.rectangle([TAMANO * 0.32, TAMANO * 0.10, TAMANO * 0.68, TAMANO * 0.32], outline=color, width=GROSOR)
    d.rounded_rectangle(
        [TAMANO * 0.16, TAMANO * 0.32, TAMANO * 0.84, TAMANO * 0.66], radius=TAMANO * 0.04,
        outline=color, width=GROSOR,
    )
    d.rectangle([TAMANO * 0.30, TAMANO * 0.60, TAMANO * 0.70, TAMANO * 0.88], outline=color, width=GROSOR)
    return img


def icono_filtro(color):
    img = _lienzo()
    d = ImageDraw.Draw(img)
    filas = [TAMANO * 0.26, TAMANO * 0.50, TAMANO * 0.74]
    knobs = [TAMANO * 0.36, TAMANO * 0.64, TAMANO * 0.46]
    r = TAMANO * 0.06
    for y, kx in zip(filas, knobs):
        d.line([TAMANO * 0.14, y, TAMANO * 0.86, y], fill=color, width=int(GROSOR * 0.7))
        d.ellipse([kx - r, y - r, kx + r, y + r], fill=color)
    return img


def icono_limpiar(color):
    img = _lienzo()
    d = ImageDraw.Draw(img)
    d.polygon(
        [
            (TAMANO * 0.30, TAMANO * 0.70), (TAMANO * 0.58, TAMANO * 0.20),
            (TAMANO * 0.80, TAMANO * 0.32), (TAMANO * 0.52, TAMANO * 0.82),
        ],
        outline=color, width=GROSOR,
    )
    d.line([TAMANO * 0.40, TAMANO * 0.55, TAMANO * 0.66, TAMANO * 0.68], fill=color, width=int(GROSOR * 0.7))
    d.line([TAMANO * 0.20, TAMANO * 0.82, TAMANO * 0.60, TAMANO * 0.82], fill=color, width=GROSOR)
    return img


def icono_recuperar(color):
    img = _lienzo()
    d = ImageDraw.Draw(img)
    m = TAMANO * 0.16
    d.arc([m, m, TAMANO - m, TAMANO - m], start=30, end=300, fill=color, width=GROSOR)
    px, py = TAMANO * 0.86, TAMANO * 0.30
    d.line([px, py, px - TAMANO * 0.16, py - TAMANO * 0.02], fill=color, width=GROSOR)
    d.line([px, py, px - TAMANO * 0.06, py + TAMANO * 0.14], fill=color, width=GROSOR)
    return img


def icono_backup(color):
    img = _lienzo()
    d = ImageDraw.Draw(img)
    d.rectangle([TAMANO * 0.14, TAMANO * 0.18, TAMANO * 0.86, TAMANO * 0.34], outline=color, width=GROSOR)
    d.rectangle([TAMANO * 0.14, TAMANO * 0.34, TAMANO * 0.86, TAMANO * 0.84], outline=color, width=GROSOR)
    d.line([TAMANO * 0.40, TAMANO * 0.52, TAMANO * 0.60, TAMANO * 0.52], fill=color, width=GROSOR)
    return img


def icono_mostrar(color):
    img = _lienzo()
    d = ImageDraw.Draw(img)
    d.ellipse([TAMANO * 0.08, TAMANO * 0.30, TAMANO * 0.92, TAMANO * 0.70], outline=color, width=GROSOR)
    r = TAMANO * 0.11
    cx, cy = TAMANO / 2, TAMANO / 2
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    return img


def icono_etiqueta(color):
    img = _lienzo()
    d = ImageDraw.Draw(img)
    d.polygon(
        [
            (TAMANO * 0.14, TAMANO * 0.14), (TAMANO * 0.58, TAMANO * 0.14),
            (TAMANO * 0.88, TAMANO * 0.44), (TAMANO * 0.44, TAMANO * 0.88),
            (TAMANO * 0.14, TAMANO * 0.58),
        ],
        outline=color, width=GROSOR,
    )
    r = TAMANO * 0.07
    cx, cy = TAMANO * 0.34, TAMANO * 0.34
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=GROSOR)
    return img


def icono_editar(color):
    img = _lienzo()
    d = ImageDraw.Draw(img)
    d.line([TAMANO * 0.24, TAMANO * 0.82, TAMANO * 0.68, TAMANO * 0.38], fill=color, width=GROSOR * 2)
    d.polygon(
        [
            (TAMANO * 0.68, TAMANO * 0.38), (TAMANO * 0.80, TAMANO * 0.26),
            (TAMANO * 0.86, TAMANO * 0.32), (TAMANO * 0.74, TAMANO * 0.44),
        ],
        outline=color, width=GROSOR,
    )
    d.line([TAMANO * 0.20, TAMANO * 0.86, TAMANO * 0.30, TAMANO * 0.78], fill=color, width=int(GROSOR * 0.8))
    return img


ICONOS = {
    "nuevo_dia": icono_nuevo_dia,
    "abrir": icono_abrir,
    "tolvas": icono_tolvas,
    "buscar": icono_buscar,
    "historico": icono_historico,
    "info": icono_info,
    "etiqueta": icono_etiqueta,
    "imprimir": icono_imprimir,
}

# Cada icono "de seccion" se genera ya en el color de su seccion
# (ver TINT_* en ui/theme.py), para las tarjetas de la pantalla de inicio.
COLOR_POR_ICONO = {
    "nuevo_dia": "#2b6cb0",
    "abrir": "#2b6cb0",
    "tolvas": "#276749",
    "buscar": "#276749",
    "historico": "#4a5568",
    "info": "#4a5568",
    "etiqueta": "#6b46c1",
    "imprimir": "#6b46c1",
}

# Iconos de accion (botones del resto de ventanas): se generan en dos tonos
# neutros -- blanco para botones de fondo solido, gris para botones en
# blanco/outline -- en vez de un color fijo, porque se reusan sobre botones
# de distintos colores en toda la app.
ICONOS_ACCION = {
    "guardar": icono_guardar,
    "eliminar": icono_eliminar,
    "volver": icono_volver,
    "documento": icono_documento,
    "aceptar": icono_aceptar,
    "cancelar": icono_cancelar,
    "exportar": icono_exportar,
    "imprimir": icono_imprimir,
    "filtro": icono_filtro,
    "limpiar": icono_limpiar,
    "recuperar": icono_recuperar,
    "backup": icono_backup,
    "mostrar": icono_mostrar,
    "editar": icono_editar,
    "buscar": icono_buscar,
    "abrir": icono_abrir,
    "info": icono_info,
    "nuevo_dia": icono_nuevo_dia,
}

TONOS_ACCION = {
    "blanco": "#ffffff",
    "gris": "#4a5568",
}


def main():
    sys.path.insert(0, str(RAIZ))
    print(f"Generando iconos en {DESTINO}")
    for nombre, funcion in ICONOS.items():
        color = COLOR_POR_ICONO[nombre]
        img = funcion(color)
        _guardar(img, nombre)

    for nombre, funcion in ICONOS_ACCION.items():
        for tono, color in TONOS_ACCION.items():
            img = funcion(color)
            _guardar(img, f"{nombre}_{tono}")
    print("Listo.")


if __name__ == "__main__":
    main()
