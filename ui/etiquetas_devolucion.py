"""Ventana de "Etiqueta de Devolucion": lista las lineas del dia en curso,
deja marcar cuales se quieren imprimir, muestra una vista previa editable y
abre un PDF con una hoja por etiqueta en el visor del sistema, que es quien
ofrece imprimir o guardar. No se escribe nada fuera del temporal.

El PDF reproduce el marco y el encabezado de la hoja de produccion
(ui/hoja_produccion.py): misma caja exterior, misma barra oscura con el
titulo centrado y las mismas cajas etiqueta/valor, solo que en cuerpo grande
porque esto se lee de lejos. Ademas lleva el logo de Ancavico en la barra.

El generador de PDF vive aqui y no se reutiliza el de ui/hoja_produccion.py
a proposito: cada ventana que imprime ya lleva su propia copia (ver tambien
ui/tolvas.py), y esta necesita tres cosas que las otras no usan (Helvetica
negrita, codificacion WinAnsi para los acentos de las descripciones, e
imagenes para el logo). Tocar la clase compartida habria cambiado la hoja de
produccion sin motivo.
"""

import os
import tempfile
import zlib
from pathlib import Path
from tkinter import TclError, messagebox

import customtkinter as ctk
from PIL import Image

from app_paths import get_bundle_path
from productos import buscar_producto
from tolvas_data import buscar_tolvas
from ui.icons import cargar_icono
from ui.toast import mostrar_toast
from ui.theme import (
    BG_APP,
    BG_FRAME,
    BG_HEADER,
    BG_HEADER_HOVER,
    BG_LABEL,
    COLOR_BORDE,
    COLOR_SEC,
    COLOR_TEXTO,
    TINT_ETIQUETADO,
)

TITULO_ETIQUETA = "ETIQUETAS DEVOLUCION VERTICAL"
LOGO_RELATIVO = "assets/Ancavico_Vertical_Brand.png"

# Igual que la hoja de produccion (ver abrir_para_imprimir en
# ui/hoja_produccion.py): el PDF se escribe en el temporal del sistema y se
# abre con el visor, que es quien ofrece imprimir o guardar.
PDF_TEMPORAL = "ancavico_etiquetas_devolucion.pdf"

# Misma paleta de papel que ui/hoja_produccion.py. Se repite aqui (igual que
# alli) porque no forma parte del tema visual de la app: es el aspecto del
# formulario impreso.
C_BLANCO = BG_FRAME
C_HEADER = BG_HEADER
C_HEADER_TXT = "#ffffff"
C_BORDE = "#94a3b8"
C_BORDE_SUAVE = COLOR_BORDE
C_TEXTO = COLOR_TEXTO
C_TEXTO_SEC = COLOR_SEC
C_ETIQUETA = "#e8ecf0"
C_MELOCOTON = "#fde8d8"

_LOGO_CACHE = {}


def _cargar_logo():
    """Devuelve (bytes RGB comprimidos, ancho, alto) del logo, o None si el
    asset no esta disponible. Se cachea: el mismo logo va en cada etiqueta.
    """
    if "logo" in _LOGO_CACHE:
        return _LOGO_CACHE["logo"]

    datos = None
    try:
        ruta = get_bundle_path(LOGO_RELATIVO)
        if ruta.exists():
            with Image.open(ruta) as imagen:
                # 220 px de lado sobran para los ~28 pt que ocupa impreso y
                # mantienen el PDF por debajo de 100 KB.
                reducida = imagen.convert("RGB").resize((220, 220), Image.LANCZOS)
                datos = (zlib.compress(reducida.tobytes(), 9), 220, 220)
    except (OSError, ValueError):
        datos = None

    _LOGO_CACHE["logo"] = datos
    return datos


class EtiquetaPDF:
    """Escritor PDF minimo de una o varias paginas, con Helvetica normal
    (F1), negrita (F2) e imagenes RGB, todo en WinAnsiEncoding.

    Las etiquetas de una tirada van como paginas de un mismo documento para
    que el visor abra una sola ventana; si fueran ficheros sueltos se
    abririan tantas ventanas como etiquetas.
    """

    # Anchos medios por caracter (fraccion del cuerpo de letra). Son
    # aproximaciones: solo se usan para centrar y para partir lineas largas.
    _ANCHO_CARACTER = {"F1": 0.52, "F2": 0.56}

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.ops = []
        self.paginas = []
        self.imagenes = []
        self._xobjects = {}

    def nueva_pagina(self):
        """Cierra la pagina en curso y empieza otra."""
        self.paginas.append(self.ops)
        self.ops = []

    def _fmt(self, value):
        if isinstance(value, int):
            return str(value)
        return f"{value:.2f}".rstrip("0").rstrip(".")

    def _rgb(self, hex_color):
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))

    def _escape(self, text):
        return str(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    def rect(self, x, y, w, h, fill=None, stroke=None, line_width=1):
        if fill:
            r, g, b = self._rgb(fill)
            self.ops.append(f"{self._fmt(r)} {self._fmt(g)} {self._fmt(b)} rg")
        if stroke:
            r, g, b = self._rgb(stroke)
            self.ops.append(f"{self._fmt(r)} {self._fmt(g)} {self._fmt(b)} RG")
            self.ops.append(f"{self._fmt(line_width)} w")
        py = self.height - y - h
        mode = "B" if fill and stroke else "f" if fill else "S"
        self.ops.append(f"{self._fmt(x)} {self._fmt(py)} {self._fmt(w)} {self._fmt(h)} re {mode}")

    def line(self, x0, y0, x1, y1, color, line_width=1):
        r, g, b = self._rgb(color)
        self.ops.append(f"{self._fmt(r)} {self._fmt(g)} {self._fmt(b)} RG")
        self.ops.append(f"{self._fmt(line_width)} w")
        self.ops.append(
            f"{self._fmt(x0)} {self._fmt(self.height - y0)} m "
            f"{self._fmt(x1)} {self._fmt(self.height - y1)} l S"
        )

    def image(self, x, y, w, h, imagen):
        """Coloca una imagen ya preparada por _cargar_logo().

        El mismo logo se reutiliza en todas las paginas: se registra un unico
        XObject y cada pagina solo lo referencia, para no repetir sus ~18 KB
        por etiqueta.
        """
        if not imagen:
            return
        datos, px, py_alto = imagen
        nombre = self._xobjects.get(datos)
        if nombre is None:
            nombre = f"Im{len(self.imagenes) + 1}"
            self._xobjects[datos] = nombre
            self.imagenes.append((nombre, datos, px, py_alto))
        self.ops.append("q")
        self.ops.append(
            f"{self._fmt(w)} 0 0 {self._fmt(h)} {self._fmt(x)} {self._fmt(self.height - y - h)} cm"
        )
        self.ops.append(f"/{nombre} Do")
        self.ops.append("Q")

    def text(self, x, y, text, size=10, color=C_TEXTO, font="F1", max_width=None, align="left", leading=None):
        """Dibuja texto y devuelve el alto ocupado, para poder encadenar
        bloques sin recalcular a mano cuantas lineas salieron del ajuste.
        """
        lines = self._wrap_text(text, size, font, max_width) if max_width else str(text).split("\n")
        leading = leading or size * 1.25
        r, g, b = self._rgb(color)
        self.ops.append("BT")
        self.ops.append(f"/{font} {self._fmt(size)} Tf")
        self.ops.append(f"{self._fmt(r)} {self._fmt(g)} {self._fmt(b)} rg")
        for index, line in enumerate(lines):
            tx = x
            if max_width and align in ("center", "right"):
                sobrante = max_width - self._text_width(line, size, font)
                tx = x + (sobrante / 2 if align == "center" else sobrante)
            py = self.height - y - index * leading
            self.ops.append(f"1 0 0 1 {self._fmt(tx)} {self._fmt(py)} Tm ({self._escape(line)}) Tj")
        self.ops.append("ET")
        return leading * len(lines)

    def _text_width(self, text, size, font="F1"):
        return len(str(text)) * size * self._ANCHO_CARACTER.get(font, 0.52)

    def _wrap_text(self, text, size, font, max_width):
        palabras = str(text).split()
        if not palabras:
            return [""]
        lineas = []
        actual = palabras[0]
        for palabra in palabras[1:]:
            prueba = f"{actual} {palabra}"
            if self._text_width(prueba, size, font) <= max_width:
                actual = prueba
            else:
                lineas.append(actual)
                actual = palabra
        lineas.append(actual)
        return lineas

    def save(self, path):
        paginas = list(self.paginas)
        if self.ops or not paginas:
            paginas.append(self.ops)

        # Reparto de numeros de objeto:
        #   1            catalogo
        #   2            arbol de paginas
        #   3 .. 2+n     una pagina por etiqueta
        #   3+n, 4+n     fuentes F1 y F2
        #   5+n ..       imagenes (el logo, compartido por todas)
        #   ultimos n    un flujo de contenido por pagina
        n = len(paginas)
        m = len(self.imagenes)
        num_fuente_1 = 3 + n
        num_fuente_2 = 4 + n
        primera_imagen = 5 + n
        primer_contenido = primera_imagen + m

        recursos = f"/Font << /F1 {num_fuente_1} 0 R /F2 {num_fuente_2} 0 R >>"
        if self.imagenes:
            refs = " ".join(
                f"/{nombre} {primera_imagen + indice} 0 R"
                for indice, (nombre, *_) in enumerate(self.imagenes)
            )
            recursos += f" /XObject << {refs} >>"

        kids = " ".join(f"{3 + indice} 0 R" for indice in range(n))
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            f"<< /Type /Pages /Kids [{kids}] /Count {n} >>".encode("ascii"),
        ]
        for indice in range(n):
            objects.append(
                (
                    f"<< /Type /Page /Parent 2 0 R "
                    f"/MediaBox [0 0 {self._fmt(self.width)} {self._fmt(self.height)}] "
                    f"/Resources << {recursos} >> /Contents {primer_contenido + indice} 0 R >>"
                ).encode("ascii")
            )
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
        for _nombre, datos, px, py_alto in self.imagenes:
            objects.append(
                (
                    f"<< /Type /XObject /Subtype /Image /Width {px} /Height {py_alto} "
                    f"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /FlateDecode "
                    f"/Length {len(datos)} >>\nstream\n"
                ).encode("ascii") + datos + b"\nendstream"
            )
        for ops in paginas:
            # cp1252 es justo el juego de caracteres de WinAnsiEncoding, que
            # es el que se declara en los objetos de fuente de arriba.
            content = "\n".join(ops).encode("cp1252", errors="replace")
            objects.append(
                b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" + content + b"\nendstream"
            )

        pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = []
        for index, obj in enumerate(objects, start=1):
            offsets.append(len(pdf))
            pdf.extend(f"{index} 0 obj\n".encode("ascii"))
            pdf.extend(obj)
            pdf.extend(b"\nendobj\n")
        xref_pos = len(pdf)
        pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        pdf.extend(b"0000000000 65535 f \n")
        for offset in offsets:
            pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
        pdf.extend(
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode("ascii")
        )
        Path(path).write_bytes(pdf)


def descripcion_de_linea(linea):
    """Nombre del producto de una linea. "fabricacion" lo rellena la pantalla
    de produccion al guardar; "observaciones" guarda lo mismo (o el tipo de
    bobina, en lineas de BOBINA). El ultimo recurso es volver a buscar el
    codigo en los maestros, por si la linea se guardo con una version antigua
    que aun no escribia esos campos.
    """
    descripcion = str(linea.get("fabricacion", "") or "").strip()
    if descripcion:
        return descripcion
    descripcion = str(linea.get("observaciones", "") or "").strip()
    if descripcion:
        return descripcion

    codigo = str(linea.get("producto", "") or "").strip()
    if not codigo:
        return ""
    info = buscar_tolvas(codigo) or buscar_producto(codigo) or {}
    return str(info.get("descripcion", "") or "").strip()


def _render_etiqueta(pdf, orden, referencia, descripcion):
    """Dibuja una etiqueta (una hoja A4) con el marco y el encabezado de la
    hoja de produccion y los tres datos en letra grande.
    """
    ancho = pdf.width

    # Mismas medidas de marco que _render_pdf_compacto() en hoja_produccion.
    mx = 10
    my = 26
    width = ancho - mx * 2
    alto_caja = 800
    alto_cabecera = 30

    pdf.rect(mx, my, width, alto_caja, fill=C_BLANCO, stroke=C_BORDE, line_width=1.4)
    pdf.rect(mx, my, width, alto_cabecera, fill=C_HEADER)
    pdf.image(mx + 4, my + 2, 26, 26, _cargar_logo())
    pdf.text(mx, my + 20, TITULO_ETIQUETA, size=17, color=C_HEADER_TXT, font="F2", max_width=width, align="center")
    pdf.line(mx, my + alto_cabecera, mx + width, my + alto_cabecera, C_BORDE, 1.2)

    x0 = mx + 8
    bw = width - 16
    ancho_label = 232
    ancho_valor = bw - ancho_label
    alto_fila = 88
    y = my + alto_cabecera + 30

    for label, valor, relleno in (
        ("Numero de orden:", orden, C_MELOCOTON),
        ("REF:", referencia, C_BLANCO),
    ):
        pdf.rect(x0, y, ancho_label, alto_fila, fill=C_ETIQUETA, stroke=C_BORDE_SUAVE)
        pdf.text(x0 + 12, y + alto_fila / 2 + 6, label, size=17, color=C_TEXTO_SEC)
        pdf.rect(x0 + ancho_label, y, ancho_valor, alto_fila, fill=relleno, stroke=C_BORDE_SUAVE)
        pdf.text(
            x0 + ancho_label + 14, y + alto_fila / 2 + 11, valor,
            size=32, font="F2", max_width=ancho_valor - 28,
        )
        y += alto_fila

    y += 22
    pdf.rect(x0, y, bw, 26, fill=C_ETIQUETA, stroke=C_BORDE_SUAVE)
    pdf.text(x0 + 8, y + 18, "ARTICULO", size=13, color=C_TEXTO_SEC)
    y += 26
    pdf.rect(x0, y, bw, 190, fill=C_BLANCO, stroke=C_BORDE_SUAVE)
    pdf.text(x0 + 14, y + 48, descripcion, size=28, font="F2", max_width=bw - 28, leading=40)


def generar_pdf_devoluciones(ruta, etiquetas):
    """Escribe un unico PDF con una hoja por etiqueta.

    "etiquetas" es una secuencia de (orden, referencia, descripcion).
    """
    pdf = EtiquetaPDF(595, 842)
    for indice, (orden, referencia, descripcion) in enumerate(etiquetas):
        if indice:
            pdf.nueva_pagina()
        _render_etiqueta(pdf, orden or "-", referencia or "-", descripcion or "-")
    pdf.save(ruta)
    return ruta


class _FilaEtiqueta:
    """Los tres datos de una etiqueta, ya resueltos desde la linea."""

    def __init__(self, linea):
        self.orden = str(linea.get("pedido", "") or "").strip()
        self.referencia = str(linea.get("producto", "") or "").strip()
        self.descripcion = descripcion_de_linea(linea)


class VentanaPreviaDevolucion(ctk.CTkToplevel):
    """Vista previa editable: una tarjeta por etiqueta con los tres campos
    corregibles antes de generar los PDF.
    """

    ANCHO = 880
    ALTO = 700

    def __init__(self, master, etiquetas, al_imprimir):
        super().__init__(master)
        self.etiquetas = list(etiquetas)
        self.al_imprimir = al_imprimir
        self.campos = []

        self.title("Vista previa de etiquetas de devolucion")
        self.geometry(f"{self.ANCHO}x{self.ALTO}")
        self.minsize(680, 480)
        self.configure(fg_color=BG_APP)
        self.transient(master.winfo_toplevel())
        self.grab_set()
        self._build_ui()
        self._centrar_sobre_padre(master)

    def _centrar_sobre_padre(self, master):
        self.update_idletasks()
        parent = master.winfo_toplevel()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (self.ANCHO // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (self.ALTO // 2)
        self.geometry(f"{self.ANCHO}x{self.ALTO}+{max(x, 0)}+{max(y, 0)}")

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(self, fg_color=BG_HEADER, corner_radius=10, height=56)
        header.grid(row=0, column=0, padx=20, pady=(18, 6), sticky="ew")
        header.grid_propagate(False)
        ctk.CTkFrame(header, fg_color=TINT_ETIQUETADO["border"], height=4, corner_radius=0).place(
            relx=0, rely=0, relwidth=1, anchor="nw"
        )
        ctk.CTkLabel(
            header,
            text="Vista previa de etiquetas",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#ffffff",
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            self,
            text=(
                f"Revisa las {len(self.etiquetas)} etiqueta(s) antes de imprimir. "
                "Puedes corregir cualquier dato aqui mismo: se imprimira lo que veas."
            ),
            font=ctk.CTkFont(size=12),
            text_color=COLOR_SEC,
            anchor="w",
        ).grid(row=1, column=0, padx=22, pady=(0, 8), sticky="ew")

        self.listado = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.listado.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="nsew")
        self.listado.grid_columnconfigure(0, weight=1)

        for indice, etiqueta in enumerate(self.etiquetas):
            self._crear_tarjeta(indice, etiqueta)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=3, column=0, padx=20, pady=(0, 18), sticky="ew")
        footer.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            footer,
            text="IMPRIMIR",
            image=cargar_icono("imprimir_blanco"),
            compound="left",
            height=44,
            corner_radius=8,
            fg_color=BG_HEADER,
            hover_color=BG_HEADER_HOVER,
            text_color="#ffffff",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._imprimir,
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkButton(
            footer,
            text="VOLVER",
            image=cargar_icono("volver_gris"),
            compound="left",
            height=44,
            corner_radius=8,
            fg_color=BG_FRAME,
            hover_color=BG_LABEL,
            text_color=COLOR_TEXTO,
            border_width=1,
            border_color=COLOR_BORDE,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.destroy,
        ).grid(row=0, column=1, padx=(8, 0), sticky="ew")

    def _crear_tarjeta(self, indice, etiqueta):
        """Cada tarjeta imita la hoja impresa: barra oscura con el titulo y
        debajo las cajas etiqueta/valor, solo que el valor es editable.
        """
        tarjeta = ctk.CTkFrame(
            self.listado, fg_color=BG_FRAME, corner_radius=10, border_width=1, border_color=COLOR_BORDE,
        )
        tarjeta.grid(row=indice, column=0, padx=4, pady=(0, 14), sticky="ew")
        tarjeta.grid_columnconfigure(1, weight=1)

        barra = ctk.CTkFrame(tarjeta, fg_color=BG_HEADER, corner_radius=6, height=34)
        barra.grid(row=0, column=0, columnspan=2, padx=12, pady=(12, 10), sticky="ew")
        barra.grid_propagate(False)
        ctk.CTkLabel(
            barra,
            text=TITULO_ETIQUETA,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#ffffff",
        ).place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(
            barra,
            text=f"{indice + 1}/{len(self.etiquetas)}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#cbd5e0",
        ).place(relx=0.985, rely=0.5, anchor="e")

        entradas = {}
        for fila, (clave, titulo, valor, tamano) in enumerate(
            (
                ("orden", "Numero de orden:", etiqueta.orden, 20),
                ("referencia", "REF:", etiqueta.referencia, 20),
                ("descripcion", "Articulo:", etiqueta.descripcion, 16),
            ),
            start=1,
        ):
            ctk.CTkLabel(
                tarjeta,
                text=titulo,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=COLOR_SEC,
                fg_color=BG_LABEL,
                corner_radius=6,
                width=150,
                anchor="w",
                padx=10,
            ).grid(row=fila, column=0, padx=(12, 8), pady=(0, 8), sticky="ew", ipady=8)

            entrada = ctk.CTkEntry(
                tarjeta,
                height=42,
                border_color=COLOR_BORDE,
                fg_color=BG_FRAME,
                # Explicito porque el fondo tambien lo es: sin esto el color
                # de texto lo decide el modo claro/oscuro del sistema y sobre
                # blanco se vuelve ilegible.
                text_color=COLOR_TEXTO,
                font=ctk.CTkFont(size=tamano, weight="bold"),
            )
            entrada.grid(row=fila, column=1, padx=(0, 12), pady=(0, 8), sticky="ew")
            entrada.insert(0, valor)
            entradas[clave] = entrada

        # El numero de orden se escribe en mayusculas tambien al corregirlo
        # aqui, igual que en el campo Orden de la pantalla de produccion.
        self._forzar_mayusculas(entradas["orden"])
        self.campos.append(entradas)

    def _forzar_mayusculas(self, entrada):
        variable = ctk.StringVar(value=entrada.get())

        def al_escribir(*_):
            texto = variable.get()
            if texto != texto.upper():
                variable.set(texto.upper())

        variable.trace_add("write", al_escribir)
        entrada.configure(textvariable=variable)

    def _valores_actuales(self):
        return [
            (
                entradas["orden"].get().strip(),
                entradas["referencia"].get().strip(),
                entradas["descripcion"].get().strip(),
            )
            for entradas in self.campos
        ]

    def _imprimir(self):
        self.al_imprimir(self, self._valores_actuales())


class VentanaEtiquetasDevolucion(ctk.CTkToplevel):
    ANCHO = 820
    ALTO = 640

    def __init__(self, master, lineas):
        super().__init__(master)
        self._master_widget = master
        self.lineas = list(lineas or [])
        self.selecciones = []

        self.title("Etiquetas de Devolucion")
        self.geometry(f"{self.ANCHO}x{self.ALTO}")
        self.minsize(640, 460)
        self.configure(fg_color=BG_APP)
        self.transient(master.winfo_toplevel())
        self.grab_set()
        self._build_ui()
        self._centrar_sobre_padre(master)

    def _centrar_sobre_padre(self, master):
        self.update_idletasks()
        parent = master.winfo_toplevel()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (self.ANCHO // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (self.ALTO // 2)
        self.geometry(f"{self.ANCHO}x{self.ALTO}+{max(x, 0)}+{max(y, 0)}")

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(self, fg_color=BG_HEADER, corner_radius=10, height=56)
        header.grid(row=0, column=0, padx=20, pady=(18, 10), sticky="ew")
        header.grid_propagate(False)
        ctk.CTkFrame(header, fg_color=TINT_ETIQUETADO["border"], height=4, corner_radius=0).place(
            relx=0, rely=0, relwidth=1, anchor="nw"
        )
        ctk.CTkLabel(
            header,
            text="Etiquetas de Devolucion",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#ffffff",
        ).place(relx=0.5, rely=0.5, anchor="center")

        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=1, column=0, padx=20, pady=(0, 8), sticky="ew")
        barra.grid_columnconfigure(2, weight=1)

        estilo_secundario = dict(
            height=32,
            corner_radius=8,
            fg_color=BG_FRAME,
            hover_color=BG_LABEL,
            text_color=COLOR_TEXTO,
            border_width=1,
            border_color=COLOR_BORDE,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        ctk.CTkButton(
            barra, text="SELECCIONAR TODO", image=cargar_icono("aceptar_gris"), compound="left",
            command=lambda: self._marcar_todas(True), **estilo_secundario,
        ).grid(row=0, column=0, padx=(0, 8))
        ctk.CTkButton(
            barra, text="QUITAR SELECCION", image=cargar_icono("limpiar_gris"), compound="left",
            command=lambda: self._marcar_todas(False), **estilo_secundario,
        ).grid(row=0, column=1, padx=(0, 8))

        self.lbl_contador = ctk.CTkLabel(
            barra,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_SEC,
            anchor="e",
        )
        self.lbl_contador.grid(row=0, column=2, sticky="e")

        lista_card = ctk.CTkFrame(
            self, fg_color=BG_FRAME, corner_radius=10, border_width=1, border_color=COLOR_BORDE,
        )
        lista_card.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="nsew")
        lista_card.grid_columnconfigure(0, weight=1)
        lista_card.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            lista_card,
            text="LINEAS DEL DIA",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_SEC,
            fg_color=BG_LABEL,
            corner_radius=6,
            anchor="w",
            padx=10,
        ).grid(row=0, column=0, padx=14, pady=(10, 6), sticky="ew", ipady=4)

        cabecera = ctk.CTkFrame(lista_card, fg_color="transparent")
        cabecera.grid(row=1, column=0, padx=(48, 20), pady=(0, 2), sticky="ew")
        cabecera.grid_columnconfigure(0, minsize=120)
        cabecera.grid_columnconfigure(1, minsize=90)
        cabecera.grid_columnconfigure(2, weight=1)
        for columna, titulo in enumerate(("N ORDEN", "REFERENCIA", "NOMBRE DEL PRODUCTO")):
            ctk.CTkLabel(
                cabecera,
                text=titulo,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=COLOR_SEC,
                anchor="w",
            ).grid(row=0, column=columna, sticky="w", padx=(0, 10))

        self.listado = ctk.CTkScrollableFrame(lista_card, fg_color="#fbfcfd")
        self.listado.grid(row=2, column=0, padx=14, pady=(0, 14), sticky="nsew")
        self.listado.grid_columnconfigure(0, weight=1)

        self._poblar_listado()

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=3, column=0, padx=20, pady=(0, 18), sticky="ew")
        footer.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            footer,
            text="VISTA PREVIA",
            image=cargar_icono("mostrar_blanco"),
            compound="left",
            height=44,
            corner_radius=8,
            fg_color=BG_HEADER,
            hover_color=BG_HEADER_HOVER,
            text_color="#ffffff",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.abrir_vista_previa,
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkButton(
            footer,
            text="CANCELAR",
            image=cargar_icono("cancelar_gris"),
            compound="left",
            height=44,
            corner_radius=8,
            fg_color=BG_FRAME,
            hover_color=BG_LABEL,
            text_color=COLOR_TEXTO,
            border_width=1,
            border_color=COLOR_BORDE,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.destroy,
        ).grid(row=0, column=1, padx=(8, 0), sticky="ew")

    def _poblar_listado(self):
        if not self.lineas:
            ctk.CTkLabel(
                self.listado,
                text="Aun no hay lineas guardadas en la produccion de hoy.",
                font=ctk.CTkFont(size=13),
                text_color=COLOR_SEC,
                anchor="w",
            ).grid(row=0, column=0, padx=12, pady=14, sticky="ew")
            self._actualizar_contador()
            return

        for indice, linea in enumerate(self.lineas):
            etiqueta = _FilaEtiqueta(linea)

            fila = ctk.CTkFrame(
                self.listado,
                fg_color=BG_FRAME if indice % 2 == 0 else "#f4f7fa",
                corner_radius=6,
            )
            fila.grid(row=indice, column=0, padx=4, pady=2, sticky="ew")
            fila.grid_columnconfigure(3, weight=1)

            variable = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(
                fila,
                text=f"{indice + 1:>2}",
                variable=variable,
                width=56,
                checkbox_width=20,
                checkbox_height=20,
                font=ctk.CTkFont(family="Consolas", size=13),
                text_color=COLOR_SEC,
                border_color=COLOR_BORDE,
                fg_color=BG_HEADER,
                hover_color=BG_HEADER_HOVER,
                command=self._actualizar_contador,
            ).grid(row=0, column=0, padx=(10, 8), pady=8, sticky="w")

            for columna, (texto, minimo, negrita) in enumerate(
                (
                    (etiqueta.orden or "-", 120, True),
                    (etiqueta.referencia or "-", 90, False),
                    (etiqueta.descripcion or "-", 0, False),
                ),
                start=1,
            ):
                ctk.CTkLabel(
                    fila,
                    text=texto,
                    font=ctk.CTkFont(size=13, weight="bold" if negrita else "normal"),
                    text_color=COLOR_TEXTO,
                    anchor="w",
                    justify="left",
                ).grid(row=0, column=columna, padx=(0, 10), pady=8, sticky="ew")
                if minimo:
                    fila.grid_columnconfigure(columna, minsize=minimo)

            self.selecciones.append((variable, etiqueta))

        self._actualizar_contador()

    def _marcar_todas(self, valor):
        for variable, _etiqueta in self.selecciones:
            variable.set(valor)
        self._actualizar_contador()

    def _actualizar_contador(self):
        marcadas = sum(1 for variable, _etiqueta in self.selecciones if variable.get())
        self.lbl_contador.configure(
            text=f"Seleccionadas: {marcadas} de {len(self.selecciones)}"
        )

    def _lineas_marcadas(self):
        return [etiqueta for variable, etiqueta in self.selecciones if variable.get()]

    def abrir_vista_previa(self):
        marcadas = self._lineas_marcadas()
        if not marcadas:
            mostrar_toast(self, "Marca al menos una linea para imprimir.", tipo="advertencia")
            return

        # Mientras la vista previa esta encima, el modal es ella; al cerrarse
        # hay que recuperar el grab o esta ventana se queda sin recibir clics.
        self.grab_release()
        previa = VentanaPreviaDevolucion(self, marcadas, self._generar_desde_previa)
        previa.wait_window()
        try:
            if self.winfo_exists():
                self.grab_set()
        except TclError:
            # Si la app entera se cierra mientras la previa estaba abierta,
            # al volver de wait_window ya no queda interprete al que pedirle
            # el grab. No hay nada que recuperar.
            pass

    def _generar_desde_previa(self, previa, valores):
        """Abre las etiquetas en el visor de PDF del sistema, igual que
        "Vista Previa Hoja" con la hoja de produccion: nada se guarda en
        ninguna carpeta: es el visor el que ofrece imprimir o guardar.

        Las ventanas se quedan abiertas detras para poder corregir un dato y
        volver a abrir el PDF sin empezar de cero.
        """
        try:
            ruta = Path(tempfile.gettempdir()) / PDF_TEMPORAL
            generar_pdf_devoluciones(ruta, valores)
            os.startfile(str(ruta))
        except Exception as error:
            messagebox.showerror(
                "No se pudieron abrir las etiquetas",
                f"No fue posible generar o abrir el PDF de devolucion.\n\nDetalle: {error}",
            )
            return

        destino = previa if previa.winfo_exists() else self._master_widget
        mostrar_toast(
            destino,
            f"{len(valores)} etiqueta(s) abiertas en el visor de PDF.",
            tipo="exito",
            duracion_ms=3000,
        )


def abrir_etiquetas_devolucion(master, lineas):
    ventana = VentanaEtiquetasDevolucion(master, lineas)
    ventana.wait_window()
    return ventana
