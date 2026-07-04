import customtkinter as ctk
from tkinter import Canvas, Scrollbar, filedialog, messagebox
from pathlib import Path
import os
import tempfile

from ui.toast import mostrar_toast
from ui.icons import cargar_icono
from ui.theme import (
    BG_APP as C_FONDO,
    BG_FRAME as C_BLANCO,
    BG_HEADER as C_HEADER,
    COLOR_BORDE as C_BORDE_SUAVE,
    COLOR_TEXTO as C_TEXTO,
    COLOR_SEC as C_TEXTO_SEC,
    TINT_PRODUCCION,
)

# Paleta especifica de la hoja impresa (imita el papel del formulario en
# papel); no forma parte del tema visual de la app, por eso vive aqui.
C_BORDE = "#94a3b8"
C_HEADER_TXT = "#ffffff"
C_TABLA_HEADER = "#e2e8f0"
C_AMARILLO = "#fefce8"
C_MELOCOTON = "#fde8d8"
C_TOTALES = "#eef2f7"
C_TOTALES_STRONG = "#dbe7f3"


class SimplePDF:
    def __init__(self, width, height):
        self.width = width
        self.height = height
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
        py0 = self.height - y0
        py1 = self.height - y1
        self.ops.append(f"{self._fmt(r)} {self._fmt(g)} {self._fmt(b)} RG")
        self.ops.append(f"{self._fmt(line_width)} w")
        self.ops.append(f"{self._fmt(x0)} {self._fmt(py0)} m {self._fmt(x1)} {self._fmt(py1)} l S")

    def text(self, x, y, text, size=10, color=C_TEXTO, max_width=None, align="left", leading=None):
        text = str(text)
        lines = self._wrap_text(text, size, max_width) if max_width else text.split("\n")
        leading = leading or size + 2
        r, g, b = self._rgb(color)
        self.ops.append("BT")
        self.ops.append(f"/F1 {self._fmt(size)} Tf")
        self.ops.append(f"{self._fmt(r)} {self._fmt(g)} {self._fmt(b)} rg")
        for index, line in enumerate(lines):
            line_width = self._text_width(line, size)
            tx = x
            if align == "center" and max_width:
                tx = x + (max_width - line_width) / 2
            elif align == "right" and max_width:
                tx = x + max_width - line_width
            py = self.height - y - index * leading
            self.ops.append(f"1 0 0 1 {self._fmt(tx)} {self._fmt(py)} Tm ({self._escape(line)}) Tj")
        self.ops.append("ET")

    def _text_width(self, text, size):
        return len(str(text)) * size * 0.52

    def _wrap_text(self, text, size, max_width):
        if not text:
            return [""]
        words = str(text).split()
        if not words:
            return [""]
        lines = []
        current = words[0]
        for word in words[1:]:
            test = f"{current} {word}"
            if self._text_width(test, size) <= max_width:
                current = test
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return lines

    def save(self, path):
        content = "\n".join(self.ops).encode("latin-1", errors="replace")
        objects = []
        objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
        objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
        page = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self._fmt(self.width)} {self._fmt(self.height)}] "
            f"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        )
        objects.append(page.encode("latin-1"))
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        stream = b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" + content + b"\nendstream"
        objects.append(stream)

        pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for index, obj in enumerate(objects, start=1):
            offsets.append(len(pdf))
            pdf.extend(f"{index} 0 obj\n".encode("ascii"))
            pdf.extend(obj)
            pdf.extend(b"\nendobj\n")
        xref_pos = len(pdf)
        pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        pdf.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
        pdf.extend(
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode("ascii")
        )
        Path(path).write_bytes(pdf)


class VentanaHojaProduccion(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C_FONDO)
        self.app = app
        self.cbo_font_pdf = None
        self.cbo_incidencias_pdf = None
        self.cbo_margen_pdf = None
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color=C_HEADER, corner_radius=10, height=52)
        header.grid(row=0, column=0, padx=20, pady=(18, 10), sticky="ew")
        header.grid_propagate(False)
        ctk.CTkFrame(header, fg_color=TINT_PRODUCCION["border"], height=4, corner_radius=0).place(
            relx=0, rely=0, relwidth=1, anchor="nw"
        )
        self.lbl_header = ctk.CTkLabel(
            header,
            text="Hoja de Produccion",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#ffffff",
        )
        self.lbl_header.place(relx=0.5, rely=0.5, anchor="center")

        self.lbl_contexto = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#1f2937",
            fg_color="#d9edf7",
            corner_radius=8,
            anchor="w",
            padx=12,
        )
        self.lbl_contexto.grid(row=0, column=0, padx=20, pady=(78, 0), sticky="ew")

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=2, column=0, padx=20, pady=(8, 4), sticky="w")
        self.btn_volver_produccion = ctk.CTkButton(
            toolbar,
            text="VOLVER A PRODUCCION",
            image=cargar_icono("volver_gris"),
            compound="left",
            width=200,
            height=40,
            corner_radius=8,
            fg_color=C_BLANCO,
            hover_color="#e2e8f0",
            text_color=C_TEXTO,
            border_width=1,
            border_color=C_BORDE_SUAVE,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.app.show_view("produccion"),
        )
        self.btn_volver_produccion.pack(side="left", padx=(0, 10))
        self.btn_volver_buscar = ctk.CTkButton(
            toolbar,
            text="VOLVER A BUSCAR",
            image=cargar_icono("volver_gris"),
            compound="left",
            width=170,
            height=40,
            corner_radius=8,
            fg_color=C_BLANCO,
            hover_color="#e2e8f0",
            text_color=C_TEXTO,
            border_width=1,
            border_color=C_BORDE_SUAVE,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.app.show_view("buscar"),
        )
        self.btn_volver_buscar.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            toolbar,
            text="EXPORTAR PDF",
            image=cargar_icono("exportar_blanco"),
            compound="left",
            width=170,
            height=40,
            corner_radius=8,
            fg_color=C_HEADER,
            hover_color="#1f2937",
            text_color="#ffffff",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.exportar_pdf,
        ).pack(side="left", padx=(10, 10))
        ctk.CTkButton(
            toolbar,
            text="ABRIR PARA IMPRIMIR",
            image=cargar_icono("imprimir_blanco"),
            compound="left",
            width=190,
            height=40,
            corner_radius=8,
            fg_color="#2b6cb0",
            hover_color="#2c5282",
            text_color="#ffffff",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.abrir_para_imprimir,
        ).pack(side="left")

        opciones_pdf = ctk.CTkFrame(self, fg_color="transparent")
        opciones_pdf.grid(row=3, column=0, padx=20, pady=(0, 18), sticky="w")

        ctk.CTkLabel(
            opciones_pdf,
            text="Letra PDF:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=C_TEXTO,
        ).pack(side="left", padx=(0, 6))
        self.cbo_font_pdf = ctk.CTkComboBox(
            opciones_pdf,
            values=["Normal", "Grande", "Muy grande"],
            width=110,
            border_color=C_BORDE_SUAVE,
            command=lambda _value: self.refresh(),
        )
        self.cbo_font_pdf.pack(side="left", padx=(0, 8))
        self.cbo_font_pdf.set("Normal")

        ctk.CTkLabel(
            opciones_pdf,
            text="Incidencias:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=C_TEXTO,
        ).pack(side="left", padx=(0, 6))
        self.cbo_incidencias_pdf = ctk.CTkComboBox(
            opciones_pdf,
            values=["Normal", "Alta"],
            width=95,
            border_color=C_BORDE_SUAVE,
            command=lambda _value: self.refresh(),
        )
        self.cbo_incidencias_pdf.pack(side="left", padx=(0, 8))
        self.cbo_incidencias_pdf.set("Normal")

        ctk.CTkLabel(
            opciones_pdf,
            text="Margen PDF:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=C_TEXTO,
        ).pack(side="left", padx=(0, 6))
        self.cbo_margen_pdf = ctk.CTkComboBox(
            opciones_pdf,
            values=["Normal", "Estrecho"],
            width=100,
            border_color=C_BORDE_SUAVE,
            command=lambda _value: self.refresh(),
        )
        self.cbo_margen_pdf.pack(side="left")
        self.cbo_margen_pdf.set("Normal")

        frame_canvas = ctk.CTkFrame(self, fg_color="transparent")
        frame_canvas.grid(row=1, column=0, padx=14, pady=(28, 0), sticky="nsew")
        frame_canvas.grid_columnconfigure(0, weight=1)
        frame_canvas.grid_rowconfigure(0, weight=1)

        self.canvas = Canvas(frame_canvas, bg=C_FONDO, highlightthickness=0)
        self.scrollbar_y = Scrollbar(frame_canvas, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar_y.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar_y.grid(row=0, column=1, sticky="ns")
        # "add='+'" es imprescindible: un bind_all sin el "+" reemplaza TODOS
        # los manejadores de rueda del raton ya registrados en la app,
        # incluidos los que CTkScrollableFrame instala en otras ventanas.
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel, add="+")

    def _widget_pertenece_al_canvas(self, widget):
        while widget is not None:
            if widget == self.canvas:
                return True
            widget = getattr(widget, "master", None)
        return False

    def _to_float(self, valor):
        try:
            return float(str(valor).replace(",", ".").strip() or 0)
        except ValueError:
            return 0.0

    def _to_int(self, valor):
        try:
            return int(str(valor).strip() or 0)
        except ValueError:
            return 0

    def _calcular_totales(self, filas):
        total_cajas = 0
        total_bobinas = 0.0
        total_palets = 0
        total_kg = 0.0
        for fila in filas:
            tipo = str(fila.get("tipo", "")).strip().upper()
            cantidad = self._to_float(fila.get("cantidad", 0))
            peso = self._to_float(fila.get("peso", 0))
            etiqueta = str(fila.get("etiqueta", "")).strip()
            producto = str(fila.get("producto", "")).strip()
            if tipo == "PALET":
                total_cajas += self._to_int(fila.get("cantidad", 0))
            total_kg += peso
            if tipo == "BOBINA":
                total_bobinas += cantidad
            if tipo == "PALET" and (cantidad > 0 or peso > 0 or etiqueta or producto):
                total_palets += 1
        return {"cajas": total_cajas, "bobinas": round(total_bobinas, 2), "palets": total_palets, "kg": round(total_kg, 2)}

    def _on_mousewheel(self, event):
        if not self._widget_pertenece_al_canvas(event.widget):
            return
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _dato_dia(self, detalle_dia, clave):
        if clave == "operarios":
            return detalle_dia.get("operarios", detalle_dia.get("Operarios", ""))
        return detalle_dia.get(clave, "")

    def _num_filas_visibles(self, filas, minimo=18):
        return max(minimo, len(filas))

    def _rect(self, x0, y0, x1, y1, fill=C_BLANCO, outline=C_BORDE_SUAVE, width=1):
        self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline=outline, width=width)

    def _txt(self, x, y, text, font=("Helvetica", 10), anchor="w", fill=C_TEXTO, width=None):
        kwargs = dict(text=text, font=font, fill=fill, anchor=anchor)
        if width:
            kwargs["width"] = width
        self.canvas.create_text(x, y, **kwargs)

    def _linea(self, x0, y0, x1, y1, fill=C_BORDE_SUAVE, width=1):
        self.canvas.create_line(x0, y0, x1, y1, fill=fill, width=width)

    def _get_print_settings(self):
        font_map = {"Normal": 0, "Grande": 1, "Muy grande": 2}
        incidencia_map = {"Normal": 0, "Alta": 18}
        margen_map = {"Normal": 10, "Estrecho": 6}
        return {
            "font_delta": font_map.get(self.cbo_font_pdf.get() if self.cbo_font_pdf else "Normal", 0),
            "incidencias_extra": incidencia_map.get(self.cbo_incidencias_pdf.get() if self.cbo_incidencias_pdf else "Normal", 0),
            "pdf_margin_x": margen_map.get(self.cbo_margen_pdf.get() if self.cbo_margen_pdf else "Normal", 10),
        }

    def refresh(self):
        if hasattr(self, "lbl_header"):
            titulo = "Hoja de Produccion - Consulta historica" if getattr(self.app, "is_hoja_preview", lambda: False)() else "Hoja de Produccion"
            self.lbl_header.configure(text=titulo)
        es_preview = getattr(self.app, "is_hoja_preview", lambda: False)()
        origen_preview = getattr(self.app, "hoja_preview_origin", None)
        if hasattr(self, "lbl_contexto"):
            self.lbl_contexto.configure(
                text="MODO CONSULTA HISTORICA: esta hoja es solo de lectura" if es_preview else "MODO PRODUCCION ACTIVA: vista previa de la produccion en curso",
                fg_color="#fde68a" if es_preview else "#c6f6d5",
            )
        if hasattr(self, "btn_volver_produccion"):
            self.btn_volver_produccion.configure(
                text=(
                    "VOLVER A HISTORICO" if origen_preview == "historico"
                    else "VOLVER A BUSCAR" if origen_preview == "buscar"
                    else "VOLVER A CONSULTA" if es_preview
                    else "VOLVER A PRODUCCION"
                ),
                command=(
                    lambda: self.app.show_view("historico")
                ) if origen_preview == "historico" else (
                    lambda: self.app.show_view("buscar")
                ) if origen_preview == "buscar" else (
                    lambda: self.app.show_view("inicio")
                ) if es_preview else (
                    lambda: self.app.show_view("produccion")
                )
            )
        if hasattr(self, "btn_volver_buscar"):
            self.btn_volver_buscar.configure(text="VOLVER AL INICIO")
            self.btn_volver_buscar.configure(command=lambda: self.app.show_view("inicio"))
        self._dibujar_hoja()

    def _build_layout(self):
        state = self.app.get_hoja_state() if hasattr(self.app, "get_hoja_state") else self.app.app_state
        detalle_dia = state["detalle_dia"]
        detalle_produccion = state["detalle_produccion"]
        filas = state["lineas_produccion"]
        totales = self._calcular_totales(filas)
        return {
            "detalle_dia": detalle_dia,
            "detalle_produccion": detalle_produccion,
            "filas": filas,
            "totales": totales,
            "mx": 40,
            "my": 36,
            "width": 980,
            "print_settings": self._get_print_settings(),
        }

    def _dibujar_hoja(self):
        layout = self._build_layout()
        self._render_canvas(layout)

    def _render_canvas(self, layout):
        detalle_dia = layout["detalle_dia"]
        detalle_produccion = layout["detalle_produccion"]
        filas = layout["filas"]
        totales = layout["totales"]
        c = self.canvas
        c.delete("all")
        mx = layout["mx"]
        my = layout["my"]
        width = layout["width"]
        font_titulo = ("Helvetica", 18, "bold")
        font_delta = layout.get("print_settings", {}).get("font_delta", 0)
        font_label = ("Helvetica", 12 + font_delta, "bold")
        font_valor = ("Helvetica", 12 + font_delta)
        font_tabla_h = ("Helvetica", 11 + font_delta, "bold")
        font_dato = ("Helvetica", 11 + font_delta)
        num_filas = self._num_filas_visibles(filas)
        page_height = 1010 + max(0, num_filas - 18) * 32
        self._rect(mx, my, mx + width, my + page_height, fill=C_BLANCO, outline=C_BORDE, width=2)
        c.create_rectangle(mx, my, mx + width, my + 52, fill=C_HEADER, outline=C_HEADER, width=0)
        self._txt(mx + width / 2, my + 26, "HOJA DE PRODUCCION", font=font_titulo, anchor="center", fill=C_HEADER_TXT)
        self._linea(mx, my + 52, mx + width, my + 52, fill=C_BORDE, width=2)
        x0 = mx + 24
        y0 = my + 72
        h_campo = 30
        left_label_w = 110
        left_value_w = 210
        right_label_x = x0 + 330
        right_label_w = 150
        right_value_x = right_label_x + right_label_w
        right_value_w = mx + width - 24 - right_value_x
        campos = [
            ("Fecha:", "fecha", x0, x0 + left_label_w, left_value_w, 0),
            ("Jefe de Maquina:", "encargado", right_label_x, right_value_x, right_value_w, 0),
            ("Operarios:", "operarios", x0, x0 + left_label_w, 430, 1),
        ]
        for label, clave, xl, xv, ancho_valor, row in campos:
            yy = y0 + row * h_campo
            self._rect(xl, yy, xv, yy + h_campo, fill="#e8ecf0", outline=C_BORDE_SUAVE)
            self._txt(xl + 8, yy + h_campo / 2, label, font=font_label, anchor="w")
            self._rect(xv, yy, xv + ancho_valor, yy + h_campo, fill=C_BLANCO, outline=C_BORDE_SUAVE)
            self._txt(xv + 8, yy + h_campo / 2, str(self._dato_dia(detalle_dia, clave)), font=font_valor, anchor="w")
        bx = x0
        by = y0 + 2 * h_campo + 18
        bw = width - 60
        fh = 26
        self.canvas.create_rectangle(bx, by, bx + bw, by + 26, fill="#e8ecf0", outline=C_BORDE_SUAVE)
        self._txt(bx + 10, by + 13, "LOTE DE BOBINA", font=("Helvetica", 11, "bold"), fill=C_TEXTO_SEC, anchor="w")
        lote_bobina = detalle_produccion.get("lote_bobina", ["", "", "", "", "", ""])
        filas_lote = []
        for index in range(0, 6, 2):
            tipo = lote_bobina[index] if len(lote_bobina) > index else ""
            numero = lote_bobina[index + 1] if len(lote_bobina) > index + 1 else ""
            filas_lote.append((tipo, numero))
        tipo_ancho = 280
        lote_ancho = 220
        for index, (tipo, numero) in enumerate(filas_lote):
            yy = by + 26 + index * fh
            self._rect(bx, yy, bx + tipo_ancho, yy + fh, fill=C_MELOCOTON, outline=C_BORDE_SUAVE)
            self._txt(bx + 8, yy + fh / 2, str(tipo), font=font_dato, anchor="w")
            self._rect(bx + tipo_ancho, yy, bx + tipo_ancho + lote_ancho, yy + fh, fill=C_AMARILLO, outline=C_BORDE_SUAVE)
            self._txt(bx + tipo_ancho + 8, yy + fh / 2, str(numero), font=font_dato, anchor="w")
            self._rect(bx + tipo_ancho + lote_ancho, yy, bx + bw, yy + fh, fill=C_BLANCO, outline=C_BORDE_SUAVE)
        inicio_x = x0
        inicio_y = by + 26 + len(filas_lote) * fh + 16
        fila_h = 32
        num_filas = self._num_filas_visibles(filas)
        columnas = [("pedido", "ORDEN", 98, C_MELOCOTON), ("etiqueta", "N ETIQUETA", 120, C_AMARILLO), ("caja", "CAJA", 50, C_AMARILLO), ("lote", "LOTE", 60, C_AMARILLO), ("producto", "GENERO", 110, C_BLANCO), ("observaciones", "OBSERVACIONES", 235, C_BLANCO), ("cantidad", "CANT.", 75, C_BLANCO), ("peso", "KG", 92, C_BLANCO)]
        x = inicio_x
        for _, titulo, ancho, _ in columnas:
            c.create_rectangle(x, inicio_y, x + ancho, inicio_y + fila_h, fill=C_TABLA_HEADER, outline=C_BORDE_SUAVE, width=1)
            c.create_text(x + ancho / 2, inicio_y + fila_h / 2, text=titulo, font=font_tabla_h, fill=C_TEXTO_SEC, anchor="center")
            x += ancho
        self._linea(inicio_x, inicio_y + fila_h, inicio_x + sum(col[2] for col in columnas), inicio_y + fila_h, fill=C_BORDE, width=1)
        for i in range(num_filas):
            y1 = inicio_y + fila_h * (i + 1)
            y_txt = y1 + fila_h / 2
            x = inicio_x
            fila = filas[i] if i < len(filas) else {}
            bg_alt = "#f8fafc" if i % 2 == 0 else C_BLANCO
            for clave, _, ancho, color_base in columnas:
                fill = color_base if fila else bg_alt
                c.create_rectangle(x, y1, x + ancho, y1 + fila_h, outline=C_BORDE_SUAVE, width=1, fill=fill)
                valor = str(fila.get(clave, ""))
                if clave == "observaciones":
                    c.create_text(x + 6, y1 + 6, text=valor, font=font_dato, fill=C_TEXTO, anchor="nw", width=ancho - 12)
                elif clave in ("cantidad", "peso"):
                    c.create_text(x + ancho / 2, y_txt, text=valor, font=font_dato, fill=C_TEXTO)
                else:
                    c.create_text(x + 6, y_txt, text=valor, font=font_dato, fill=C_TEXTO, anchor="w")
                x += ancho
        base_x = inicio_x + 690
        base_y = inicio_y + fila_h * (num_filas + 1) + 14
        aw_label = 130
        aw_valor = 90
        ah = 32
        c.create_rectangle(base_x, base_y - 26, base_x + aw_label + aw_valor, base_y, fill="#e8ecf0", outline=C_BORDE_SUAVE)
        c.create_text(base_x + (aw_label + aw_valor) / 2, base_y - 13, text="TOTALES", font=("Helvetica", 9, "bold"), fill=C_TEXTO_SEC, anchor="center")
        filas_totales = [("CAJAS", totales["cajas"], False), ("BOBINAS", totales["bobinas"], False), ("PALETS", totales["palets"], False), ("KG", f"{totales['kg']:.1f}", True)]
        for index, (txt, valor, grande) in enumerate(filas_totales):
            y = base_y + index * ah
            self._rect(base_x, y, base_x + aw_label, y + ah, fill=C_TOTALES, outline=C_BORDE_SUAVE)
            self._txt(base_x + 12, y + ah / 2, txt, font=("Helvetica", 11, "bold"), anchor="w", fill=C_TEXTO_SEC)
            self._rect(base_x + aw_label, y, base_x + aw_label + aw_valor, y + ah, fill=C_BLANCO, outline=C_BORDE_SUAVE)
            self._txt(base_x + aw_label + aw_valor / 2, y + ah / 2, str(valor), font=("Helvetica", 18, "bold") if grande else ("Helvetica", 13, "bold"), anchor="center")
        inc_x = x0
        inc_y = base_y + 4 * ah + 16
        inc_w = width - 60
        inc_h = 84 + layout.get("print_settings", {}).get("incidencias_extra", 0)
        c.create_rectangle(inc_x, inc_y, inc_x + 140, inc_y + 26, fill="#e8ecf0", outline=C_BORDE_SUAVE)
        self._txt(inc_x + 10, inc_y + 13, "INCIDENCIAS", font=("Helvetica", 11, "bold"), fill=C_TEXTO_SEC, anchor="w")
        self._rect(inc_x, inc_y + 26, inc_x + inc_w, inc_y + inc_h, fill=C_BLANCO, outline=C_BORDE_SUAVE)
        self._txt(inc_x + 10, inc_y + 40, str(detalle_dia.get("incidencias", "")), font=font_dato, anchor="nw", width=inc_w - 24)
        sub_y = inc_y + inc_h + 24
        det_h = 30
        det_filas = 6
        filas_det = detalle_produccion.get("filas", [])
        marca_ancho = 220
        etiqueta_ancho = 170
        cantidad_ancho = 120
        gastado_ancho = 120
        resto_ancho = bw - marca_ancho - etiqueta_ancho - cantidad_ancho - gastado_ancho
        c.create_rectangle(x0, sub_y, x0 + bw, sub_y + 26, fill="#e8ecf0", outline=C_BORDE_SUAVE)
        self._txt(x0 + 10, sub_y + 13, "ETIQUETAS PALET CAJAS", font=("Helvetica", 11, "bold"), fill=C_TEXTO_SEC, anchor="w")
        ref_y = sub_y + 26
        cabeceras_det = [("Marca de Caja", marca_ancho), ("Etiqueta", etiqueta_ancho), ("Cantidad", cantidad_ancho), ("Gastado", gastado_ancho), ("Resto Total", resto_ancho)]
        x = x0
        for titulo, ancho in cabeceras_det:
            self._rect(x, ref_y, x + ancho, ref_y + det_h, fill=C_TABLA_HEADER, outline=C_BORDE_SUAVE)
            self._txt(x + ancho / 2, ref_y + det_h / 2, titulo, font=font_tabla_h, anchor="center", fill=C_TEXTO_SEC)
            x += ancho
        for index in range(det_filas):
            yy = ref_y + det_h + index * det_h
            fila = filas_det[index] if index < len(filas_det) else {}
            self._rect(x0, yy, x0 + marca_ancho, yy + det_h, fill=C_MELOCOTON, outline=C_BORDE_SUAVE)
            self._rect(x0 + marca_ancho, yy, x0 + marca_ancho + etiqueta_ancho, yy + det_h, fill=C_AMARILLO, outline=C_BORDE_SUAVE)
            self._rect(x0 + marca_ancho + etiqueta_ancho, yy, x0 + marca_ancho + etiqueta_ancho + cantidad_ancho, yy + det_h, fill=C_BLANCO, outline=C_BORDE_SUAVE)
            self._rect(x0 + marca_ancho + etiqueta_ancho + cantidad_ancho, yy, x0 + marca_ancho + etiqueta_ancho + cantidad_ancho + gastado_ancho, yy + det_h, fill=C_BLANCO, outline=C_BORDE_SUAVE)
            self._rect(x0 + marca_ancho + etiqueta_ancho + cantidad_ancho + gastado_ancho, yy, x0 + bw, yy + det_h, fill=C_BLANCO, outline=C_BORDE_SUAVE)
            self._txt(x0 + 8, yy + det_h / 2, str(fila.get("marca", "")), font=font_dato, anchor="w", width=marca_ancho - 16)
            self._txt(x0 + marca_ancho + 8, yy + det_h / 2, str(fila.get("etiqueta", "")), font=font_dato, anchor="w", width=etiqueta_ancho - 16)
            self._txt(x0 + marca_ancho + etiqueta_ancho + 8, yy + det_h / 2, str(fila.get("cantidad", "")), font=font_dato, anchor="w", width=cantidad_ancho - 16)
            self._txt(x0 + marca_ancho + etiqueta_ancho + cantidad_ancho + 8, yy + det_h / 2, str(fila.get("gastado", "")), font=font_dato, anchor="w", width=gastado_ancho - 16)
            self._txt(x0 + marca_ancho + etiqueta_ancho + cantidad_ancho + gastado_ancho + 8, yy + det_h / 2, str(fila.get("resto", "")), font=font_dato, anchor="w", width=resto_ancho - 16)
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def exportar_pdf(self):
        ruta = filedialog.asksaveasfilename(
            title="Guardar hoja de produccion en PDF",
            defaultextension=".pdf",
            filetypes=[("Archivo PDF", "*.pdf")],
            initialfile="hoja_produccion.pdf",
        )
        if not ruta:
            return
        layout = self._build_layout()
        pdf = SimplePDF(595, 842)
        self._render_pdf_compacto(pdf, layout)
        pdf.save(ruta)
        mostrar_toast(self, f"PDF generado en:\n{ruta}", tipo="exito", duracion_ms=4000)

    def abrir_para_imprimir(self):
        try:
            ruta_temporal = Path(tempfile.gettempdir()) / "ancavico_hoja_produccion.pdf"
            layout = self._build_layout()
            pdf = SimplePDF(595, 842)
            self._render_pdf_compacto(pdf, layout)
            pdf.save(ruta_temporal)
            os.startfile(str(ruta_temporal))
        except Exception as error:
            messagebox.showerror(
                "No se pudo abrir el PDF",
                f"No fue posible abrir la hoja para imprimir.\n\nDetalle: {error}",
            )

    def _render_pdf_compacto(self, pdf, layout):
        detalle_dia = layout["detalle_dia"]
        detalle_produccion = layout["detalle_produccion"]
        filas = layout["filas"]
        totales = layout["totales"]
        settings = layout.get("print_settings", {})
        font_delta = settings.get("font_delta", 0)

        mx = settings.get("pdf_margin_x", 10)
        my = 26
        width = 595 - (mx * 2)
        alto_pagina = 800
        pdf.rect(mx, my, width, alto_pagina, fill=C_BLANCO, stroke=C_BORDE, line_width=1.4)
        pdf.rect(mx, my, width, 30, fill=C_HEADER)
        pdf.text(mx, my + 20, "HOJA DE PRODUCCION", size=17 + font_delta, color=C_HEADER_TXT, max_width=width, align="center")
        pdf.line(mx, my + 30, mx + width, my + 30, C_BORDE, 1.2)

        x0 = mx + 8
        y0 = my + 54
        h_campo = 21
        campos = [
            ("Fecha:", self._dato_dia(detalle_dia, "fecha"), x0, 74, 124, 0),
            ("Jefe de Maquina:", self._dato_dia(detalle_dia, "encargado"), x0 + 190, 122, 249, 0),
            ("Operarios:", self._dato_dia(detalle_dia, "operarios"), x0, 84, 250, 1),
        ]
        for label, valor, xl, wl, wv, row in campos:
            yy = y0 + row * h_campo
            pdf.rect(xl, yy, wl, h_campo, fill="#e8ecf0", stroke=C_BORDE_SUAVE)
            pdf.text(xl + 5, yy + 13.8, label, size=11.8 + font_delta)
            pdf.rect(xl + wl, yy, wv, h_campo, fill=C_BLANCO, stroke=C_BORDE_SUAVE)
            pdf.text(xl + wl + 5, yy + 13.8, str(valor), size=11.7 + font_delta, max_width=wv - 10)

        by = y0 + 2 * h_campo + 10
        bw = width - 16
        fh = 15
        pdf.rect(x0, by, bw, 18, fill="#e8ecf0", stroke=C_BORDE_SUAVE)
        pdf.text(x0 + 6, by + 12.5, "LOTE DE BOBINA", size=11.6 + font_delta, color=C_TEXTO_SEC)
        lote_bobina = detalle_produccion.get("lote_bobina", ["", "", "", "", "", ""])
        filas_lote = []
        for index in range(0, 6, 2):
            filas_lote.append((lote_bobina[index] if len(lote_bobina) > index else "", lote_bobina[index + 1] if len(lote_bobina) > index + 1 else ""))
        tipo_ancho = 214
        lote_ancho = 132
        for index, (tipo, numero) in enumerate(filas_lote):
            yy = by + 18 + index * fh
            pdf.rect(x0, yy, tipo_ancho, fh, fill=C_MELOCOTON, stroke=C_BORDE_SUAVE)
            pdf.text(x0 + 4, yy + 11.5, str(tipo), size=10.4 + font_delta)
            pdf.rect(x0 + tipo_ancho, yy, lote_ancho, fh, fill=C_AMARILLO, stroke=C_BORDE_SUAVE)
            pdf.text(x0 + tipo_ancho + 4, yy + 11.5, str(numero), size=10.4 + font_delta)
            pdf.rect(x0 + tipo_ancho + lote_ancho, yy, bw - tipo_ancho - lote_ancho, fh, fill=C_BLANCO, stroke=C_BORDE_SUAVE)
        pdf.line(x0, by + 18, x0 + bw, by + 18, C_BORDE_SUAVE, 1)

        inicio_x = x0
        inicio_y = by + 18 + len(filas_lote) * fh + 9
        fila_h = 12.1
        num_filas = self._num_filas_visibles(filas)
        columnas = [
            ("pedido", "ORD", 56, C_MELOCOTON),
            ("etiqueta", "ETQ", 68, C_AMARILLO),
            ("caja", "CAJA", 30, C_AMARILLO),
            ("lote", "LOTE", 38, C_AMARILLO),
            ("producto", "GEN", 50, C_BLANCO),
            ("observaciones", "OBS.", 216, C_BLANCO),
            ("cantidad", "CANT", 44, C_BLANCO),
            ("peso", "KG", 48, C_BLANCO),
        ]
        x = inicio_x
        for _, titulo, ancho, _ in columnas:
            pdf.rect(x, inicio_y, ancho, fila_h, fill=C_TABLA_HEADER, stroke=C_BORDE_SUAVE)
            pdf.text(x, inicio_y + 9.0, titulo, size=10.6 + font_delta, color=C_TEXTO_SEC, max_width=ancho, align="center")
            x += ancho
        pdf.line(inicio_x, inicio_y + fila_h, inicio_x + sum(col[2] for col in columnas), inicio_y + fila_h, C_BORDE, 1.1)
        for i in range(num_filas):
            y1 = inicio_y + fila_h * (i + 1)
            x = inicio_x
            fila = filas[i] if i < len(filas) else {}
            bg_alt = "#f8fafc" if i % 2 == 0 else C_BLANCO
            for clave, _, ancho, color_base in columnas:
                fill = color_base if fila else bg_alt
                pdf.rect(x, y1, ancho, fila_h, fill=fill, stroke=C_BORDE_SUAVE)
                valor = str(fila.get(clave, ""))
                if clave == "observaciones":
                    pdf.text(x + 3, y1 + 8.9, valor, size=10.5 + font_delta, max_width=ancho - 6, leading=10.9 + font_delta)
                elif clave in ("cantidad", "peso"):
                    pdf.text(x, y1 + 8.9, valor, size=10.5 + font_delta, max_width=ancho, align="center")
                else:
                    pdf.text(x + 3, y1 + 8.9, valor, size=10.5 + font_delta, max_width=ancho - 6)
                x += ancho

        base_y = inicio_y + fila_h * (num_filas + 1) + 7
        inc_x = x0
        inc_w = 360
        total_x = inc_x + inc_w + 10
        aw_label = 82
        aw_valor = 50
        ah = 12
        filas_totales = [("CAJAS", totales["cajas"]), ("BOBINAS", totales["bobinas"]), ("PALETS", totales["palets"]), ("KG", f"{totales['kg']:.1f}")]

        det_h = 11
        det_filas = 6
        bloque_detalle_h = 15 + det_h + det_filas * det_h
        incidencias_texto = str(detalle_dia.get("incidencias", ""))
        incidencias_font = 10.8 + font_delta
        incidencias_leading = 12.0 + font_delta
        incidencias_lines = pdf._wrap_text(incidencias_texto, incidencias_font, inc_w - 10)
        inc_h = max(48, min(86, len(incidencias_lines) * incidencias_leading + 10 + settings.get("incidencias_extra", 0)))
        bloque_incidencias_h = 15 + inc_h
        sub_y = max(base_y + bloque_incidencias_h + 12, my + alto_pagina - 16 - bloque_detalle_h)
        base_y = sub_y - bloque_incidencias_h - 12

        pdf.rect(inc_x, base_y, 96, 15, fill="#e8ecf0", stroke=C_BORDE_SUAVE)
        pdf.text(inc_x + 4, base_y + 11, "INCIDENCIAS", size=11.1 + font_delta, color=C_TEXTO_SEC)
        pdf.rect(inc_x, base_y + 15, inc_w, inc_h, fill=C_BLANCO, stroke=C_BORDE_SUAVE)
        pdf.text(inc_x + 4, base_y + 24, incidencias_texto, size=incidencias_font, max_width=inc_w - 10, leading=incidencias_leading)

        pdf.rect(total_x, base_y, aw_label + aw_valor, 15, fill=C_TOTALES_STRONG, stroke=C_BORDE, line_width=1.1)
        pdf.text(total_x, base_y + 11, "TOTALES", size=10.9 + font_delta, color=C_TEXTO_SEC, max_width=aw_label + aw_valor, align="center")
        for index, (txt, valor) in enumerate(filas_totales):
            y = base_y + 15 + index * ah
            pdf.rect(total_x, y, aw_label, ah, fill=C_TOTALES_STRONG if txt == "KG" else C_TOTALES, stroke=C_BORDE, line_width=0.9)
            pdf.text(total_x + 4, y + 8.5, txt, size=(9.7 if txt != "KG" else 10.1) + font_delta, color=C_TEXTO_SEC)
            pdf.rect(total_x + aw_label, y, aw_valor, ah, fill=C_BLANCO, stroke=C_BORDE, line_width=0.9)
            pdf.text(
                total_x + aw_label,
                y + 8.5,
                str(valor),
                size=(9.7 if txt != "KG" else 10.4) + font_delta,
                max_width=aw_valor,
                align="center",
            )

        filas_det = detalle_produccion.get("filas", [])
        marca_ancho = 194
        etiqueta_ancho = 118
        cantidad_ancho = 60
        gastado_ancho = 60
        resto_ancho = bw - marca_ancho - etiqueta_ancho - cantidad_ancho - gastado_ancho
        pdf.rect(x0, sub_y, bw, 15, fill="#e8ecf0", stroke=C_BORDE_SUAVE)
        pdf.text(x0 + 6, sub_y + 10.5, "ETIQUETAS PALET CAJAS", size=10.2 + font_delta, color=C_TEXTO_SEC)
        ref_y = sub_y + 15
        cabeceras_det = [("Marca", marca_ancho), ("Etiqueta", etiqueta_ancho), ("Cantidad", cantidad_ancho), ("Gastado", gastado_ancho), ("Resto", resto_ancho)]
        x = x0
        for titulo, ancho in cabeceras_det:
            pdf.rect(x, ref_y, ancho, det_h, fill=C_TABLA_HEADER, stroke=C_BORDE_SUAVE)
            pdf.text(x, ref_y + 7.8, titulo, size=9.8 + font_delta, color=C_TEXTO_SEC, max_width=ancho, align="center")
            x += ancho
        pdf.line(x0, ref_y + det_h, x0 + bw, ref_y + det_h, C_BORDE, 1.0)
        for index in range(det_filas):
            yy = ref_y + det_h + index * det_h
            fila = filas_det[index] if index < len(filas_det) else {}
            valores = [str(fila.get("marca", "")), str(fila.get("etiqueta", "")), str(fila.get("cantidad", "")), str(fila.get("gastado", "")), str(fila.get("resto", ""))]
            x = x0
            anchos = [marca_ancho, etiqueta_ancho, cantidad_ancho, gastado_ancho, resto_ancho]
            fills = [C_MELOCOTON, C_AMARILLO, C_BLANCO, C_BLANCO, C_BLANCO]
            for valor, ancho, fill in zip(valores, anchos, fills):
                pdf.rect(x, yy, ancho, det_h, fill=fill, stroke=C_BORDE_SUAVE)
                pdf.text(x + 2, yy + 7.8, valor, size=10.2 + font_delta, max_width=ancho - 4)
                x += ancho

    def _render_pdf(self, pdf, layout):
        detalle_dia = layout["detalle_dia"]
        detalle_produccion = layout["detalle_produccion"]
        filas = layout["filas"]
        totales = layout["totales"]
        mx = layout["mx"]
        my = layout["my"]
        width = layout["width"]
        pdf.rect(mx, my, width, 1080, fill=C_BLANCO, stroke=C_BORDE, line_width=2)
        pdf.rect(mx, my, width, 52, fill=C_HEADER)
        pdf.text(mx, my + 34, "HOJA DE PRODUCCION", size=18, color=C_HEADER_TXT, max_width=width, align="center")
        pdf.line(mx, my + 52, mx + width, my + 52, C_BORDE, 2)
        x0 = mx + 30
        y0 = my + 68
        h_campo = 28
        campos = [("Fecha:", "fecha", x0, x0 + 100, 270, 0), ("Jefe de Maquina:", "encargado", x0 + 500, x0 + 640, 280, 0), ("Operarios:", "operarios", x0, x0 + 100, 270, 1)]
        for label, clave, xl, xv, ancho_valor, row in campos:
            yy = y0 + row * h_campo
            pdf.rect(xl, yy, 95, h_campo, fill="#e8ecf0", stroke=C_BORDE_SUAVE)
            pdf.text(xl + 8, yy + 18, label, size=10)
            pdf.rect(xv, yy, ancho_valor, h_campo, fill=C_BLANCO, stroke=C_BORDE_SUAVE)
            pdf.text(xv + 8, yy + 18, str(self._dato_dia(detalle_dia, clave)), size=10)
        bx = x0
        by = y0 + 2 * h_campo + 14
        bw = width - 60
        fh = 24
        pdf.rect(bx, by, bw, 26, fill="#e8ecf0", stroke=C_BORDE_SUAVE)
        pdf.text(bx + 10, by + 17, "LOTE DE BOBINA", size=10, color=C_TEXTO_SEC)
        lote_bobina = detalle_produccion.get("lote_bobina", ["", "", "", "", "", ""])
        filas_lote = []
        for index in range(0, 6, 2):
            tipo = lote_bobina[index] if len(lote_bobina) > index else ""
            numero = lote_bobina[index + 1] if len(lote_bobina) > index + 1 else ""
            filas_lote.append((tipo, numero))
        tipo_ancho = 280
        lote_ancho = 220
        for index, (tipo, numero) in enumerate(filas_lote):
            yy = by + 26 + index * fh
            pdf.rect(bx, yy, tipo_ancho, fh, fill=C_MELOCOTON, stroke=C_BORDE_SUAVE)
            pdf.text(bx + 8, yy + 16, str(tipo), size=9)
            pdf.rect(bx + tipo_ancho, yy, lote_ancho, fh, fill=C_AMARILLO, stroke=C_BORDE_SUAVE)
            pdf.text(bx + tipo_ancho + 8, yy + 16, str(numero), size=9)
            pdf.rect(bx + tipo_ancho + lote_ancho, yy, bw - tipo_ancho - lote_ancho, fh, fill=C_BLANCO, stroke=C_BORDE_SUAVE)
        inicio_x = x0
        inicio_y = by + 26 + len(filas_lote) * fh + 16
        fila_h = 30
        num_filas = self._num_filas_visibles(filas)
        columnas = [("pedido", "ORDEN", 95, C_MELOCOTON), ("etiqueta", "N ETIQUETA", 125, C_AMARILLO), ("caja", "CAJA", 55, C_AMARILLO), ("lote", "LOTE", 65, C_AMARILLO), ("producto", "GENERO", 95, C_BLANCO), ("observaciones", "OBSERVACIONES", 255, C_BLANCO), ("cantidad", "CANT.", 70, C_BLANCO), ("peso", "PESO KG", 90, C_BLANCO)]
        x = inicio_x
        for _, titulo, ancho, _ in columnas:
            pdf.rect(x, inicio_y, ancho, fila_h, fill=C_TABLA_HEADER, stroke=C_BORDE_SUAVE)
            pdf.text(x, inicio_y + 19, titulo, size=9, color=C_TEXTO_SEC, max_width=ancho, align="center")
            x += ancho
        pdf.line(inicio_x, inicio_y + fila_h, inicio_x + sum(col[2] for col in columnas), inicio_y + fila_h, C_BORDE, 1)
        for i in range(num_filas):
            y1 = inicio_y + fila_h * (i + 1)
            x = inicio_x
            fila = filas[i] if i < len(filas) else {}
            bg_alt = "#f8fafc" if i % 2 == 0 else C_BLANCO
            for clave, _, ancho, color_base in columnas:
                fill = color_base if fila else bg_alt
                pdf.rect(x, y1, ancho, fila_h, fill=fill, stroke=C_BORDE_SUAVE)
                valor = str(fila.get(clave, ""))
                if clave == "observaciones":
                    pdf.text(x + 5, y1 + 13, valor, size=9, max_width=ancho - 10)
                elif clave in ("cantidad", "peso"):
                    pdf.text(x, y1 + 18, valor, size=9, max_width=ancho, align="center")
                else:
                    pdf.text(x + 5, y1 + 18, valor, size=9)
                x += ancho
        base_x = inicio_x + 690
        base_y = inicio_y + fila_h * (num_filas + 1) + 14
        aw_label = 130
        aw_valor = 90
        ah = 32
        pdf.rect(base_x, base_y - 26, aw_label + aw_valor, 26, fill="#e8ecf0", stroke=C_BORDE_SUAVE)
        pdf.text(base_x, base_y - 8, "TOTALES", size=9, color=C_TEXTO_SEC, max_width=aw_label + aw_valor, align="center")
        filas_totales = [("CAJAS", totales["cajas"], 12), ("BOBINAS", totales["bobinas"], 12), ("PALETS", totales["palets"], 12), ("KG", f"{totales['kg']:.1f}", 18)]
        for index, (txt, valor, size) in enumerate(filas_totales):
            y = base_y + index * ah
            pdf.rect(base_x, y, aw_label, ah, fill=C_TOTALES, stroke=C_BORDE_SUAVE)
            pdf.text(base_x + 12, y + 20, txt, size=10, color=C_TEXTO_SEC)
            pdf.rect(base_x + aw_label, y, aw_valor, ah, fill=C_BLANCO, stroke=C_BORDE_SUAVE)
            pdf.text(base_x + aw_label, y + 22, str(valor), size=size, max_width=aw_valor, align="center")
        inc_x = x0
        inc_y = base_y + 4 * ah + 16
        inc_w = width - 60
        inc_h = 72
        pdf.rect(inc_x, inc_y, 140, 26, fill="#e8ecf0", stroke=C_BORDE_SUAVE)
        pdf.text(inc_x + 10, inc_y + 17, "INCIDENCIAS", size=10, color=C_TEXTO_SEC)
        pdf.rect(inc_x, inc_y + 26, inc_w, inc_h, fill=C_BLANCO, stroke=C_BORDE_SUAVE)
        pdf.text(inc_x + 10, inc_y + 40, str(detalle_dia.get("incidencias", "")), size=9, max_width=inc_w - 20)
        sub_y = inc_y + inc_h + 24
        det_h = 28
        det_filas = 6
        filas_det = detalle_produccion.get("filas", [])
        marca_ancho = 220
        etiqueta_ancho = 170
        cantidad_ancho = 120
        gastado_ancho = 120
        resto_ancho = bw - marca_ancho - etiqueta_ancho - cantidad_ancho - gastado_ancho
        pdf.rect(x0, sub_y, bw, 26, fill="#e8ecf0", stroke=C_BORDE_SUAVE)
        pdf.text(x0 + 10, sub_y + 17, "ETIQUETAS PALET CAJAS", size=10, color=C_TEXTO_SEC)
        ref_y = sub_y + 26
        cabeceras_det = [("Marca de Caja", marca_ancho), ("Etiqueta", etiqueta_ancho), ("Cantidad", cantidad_ancho), ("Gastado", gastado_ancho), ("Resto Total", resto_ancho)]
        x = x0
        for titulo, ancho in cabeceras_det:
            pdf.rect(x, ref_y, ancho, det_h, fill=C_TABLA_HEADER, stroke=C_BORDE_SUAVE)
            pdf.text(x, ref_y + 18, titulo, size=9, color=C_TEXTO_SEC, max_width=ancho, align="center")
            x += ancho
        for index in range(det_filas):
            yy = ref_y + det_h + index * det_h
            fila = filas_det[index] if index < len(filas_det) else {}
            pdf.rect(x0, yy, marca_ancho, det_h, fill=C_MELOCOTON, stroke=C_BORDE_SUAVE)
            pdf.rect(x0 + marca_ancho, yy, etiqueta_ancho, det_h, fill=C_AMARILLO, stroke=C_BORDE_SUAVE)
            pdf.rect(x0 + marca_ancho + etiqueta_ancho, yy, cantidad_ancho, det_h, fill=C_BLANCO, stroke=C_BORDE_SUAVE)
            pdf.rect(x0 + marca_ancho + etiqueta_ancho + cantidad_ancho, yy, gastado_ancho, det_h, fill=C_BLANCO, stroke=C_BORDE_SUAVE)
            pdf.rect(x0 + marca_ancho + etiqueta_ancho + cantidad_ancho + gastado_ancho, yy, resto_ancho, det_h, fill=C_BLANCO, stroke=C_BORDE_SUAVE)
            pdf.text(x0 + 8, yy + 18, str(fila.get("marca", "")), size=9, max_width=marca_ancho - 16)
            pdf.text(x0 + marca_ancho + 8, yy + 18, str(fila.get("etiqueta", "")), size=9, max_width=etiqueta_ancho - 16)
            pdf.text(x0 + marca_ancho + etiqueta_ancho + 8, yy + 18, str(fila.get("cantidad", "")), size=9, max_width=cantidad_ancho - 16)
            pdf.text(x0 + marca_ancho + etiqueta_ancho + cantidad_ancho + 8, yy + 18, str(fila.get("gastado", "")), size=9, max_width=gastado_ancho - 16)
            pdf.text(x0 + marca_ancho + etiqueta_ancho + cantidad_ancho + gastado_ancho + 8, yy + 18, str(fila.get("resto", "")), size=9, max_width=resto_ancho - 16)

