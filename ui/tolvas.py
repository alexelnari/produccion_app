import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
import os
import tempfile

from productos import buscar_producto
from tolvas_data import buscar_tolvas, guardar_tolvas_producto, buscar_composiciones_parecidas
from ui.admin_dialog import ask_admin_password, verificar_clave_admin
from ui.detalle_produccion import VALORES_BOBINA, VALORES_MARCA
from ui.toast import mostrar_toast
from ui.icons import cargar_icono
from ui.theme import (
    BG_APP,
    BG_FRAME,
    BG_HEADER,
    BG_HEADER_HOVER,
    BG_LABEL,
    COLOR_BORDE,
    COLOR_TEXTO,
    COLOR_SEC,
    COLOR_READONLY,
    COLOR_DANGER,
    COLOR_DANGER_HOVER,
    COLOR_SUCCESS,
    COLOR_SUCCESS_HOVER,
    COLOR_INFO,
    COLOR_INFO_HOVER,
    COLOR_PURPLE,
    COLOR_PURPLE_HOVER,
    TINT_OPERACION,
)

VALORES_PRECINTO = [
    "",
    "Precinto Azul",
    "Precinto Blanco",
    "Precinto Transparente",
    "Precinto Marron",
    "Precinto Impreso",
    "Sin Precinto",
]


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

    def text(self, x, y, text, size=10, color=COLOR_TEXTO):
        r, g, b = self._rgb(color)
        py = self.height - y
        self.ops.append("BT")
        self.ops.append(f"/F1 {self._fmt(size)} Tf")
        self.ops.append(f"{self._fmt(r)} {self._fmt(g)} {self._fmt(b)} rg")
        self.ops.append(f"1 0 0 1 {self._fmt(x)} {self._fmt(py)} Tm ({self._escape(text)}) Tj")
        self.ops.append("ET")

    def save(self, path):
        content = "\n".join(self.ops).encode("latin-1", errors="replace")
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self._fmt(self.width)} {self._fmt(self.height)}] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>".encode("latin-1"),
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" + content + b"\nendstream",
        ]
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
        pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode("ascii"))
        Path(path).write_bytes(pdf)


class EditorComposicionTolvas(ctk.CTkToplevel):
    def __init__(self, master, codigo, datos, on_save):
        super().__init__(master)
        self.codigo = str(codigo).strip()
        self.master_panel = master
        self.on_save = on_save
        self.title(f"Editar Composicion {self.codigo}")
        self.geometry("860x580")
        self.resizable(False, False)
        self.configure(fg_color=BG_APP)
        self.transient(master.winfo_toplevel())
        self.grab_set()

        self.entries_tolvas = []
        self.lbl_titulo = None
        self._build_ui(datos)

    def _build_ui(self, datos):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color=BG_HEADER, corner_radius=10, height=52)
        header.grid(row=0, column=0, padx=20, pady=(18, 10), sticky="ew")
        header.grid_propagate(False)
        ctk.CTkFrame(header, fg_color=TINT_OPERACION["border"], height=4, corner_radius=0).place(
            relx=0, rely=0, relwidth=1, anchor="nw"
        )
        self.lbl_titulo = ctk.CTkLabel(
            header,
            text=f"Editar Composicion del Articulo {self.codigo}",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#ffffff",
        )
        self.lbl_titulo.place(relx=0.5, rely=0.5, anchor="center")

        main = ctk.CTkFrame(self, fg_color=BG_FRAME, corner_radius=12, border_width=1, border_color=COLOR_BORDE)
        main.grid(row=1, column=0, padx=20, pady=(0, 18), sticky="nsew")
        main.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(main, fg_color="transparent")
        top.grid(row=0, column=0, padx=24, pady=(18, 12), sticky="ew")
        top.grid_columnconfigure(1, weight=1)
        top.grid_columnconfigure(3, weight=1)

        self._label(top, "Articulo:", 0, 0)
        self.txt_codigo = self._entry(top, 0, 1, width=160)
        self.txt_codigo.insert(0, self.codigo)
        self.txt_codigo.bind("<Return>", lambda _event: self._cargar_articulo())

        ctk.CTkButton(
            top,
            text="CARGAR",
            image=cargar_icono("abrir_blanco"),
            compound="left",
            width=110,
            height=30,
            corner_radius=8,
            fg_color=COLOR_INFO,
            hover_color=COLOR_INFO_HOVER,
            text_color="#ffffff",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._cargar_articulo,
        ).grid(row=0, column=2, padx=(0, 10), pady=6, sticky="w")

        self._label(top, "Descripcion:", 1, 0)
        self.txt_descripcion = self._entry(top, 1, 1, width=300)
        self.txt_descripcion.insert(0, datos.get("descripcion", ""))

        self._label(top, "Kg por caja:", 1, 2)
        self.txt_kilos_caja = self._entry(top, 1, 3, width=180)
        self.txt_kilos_caja.insert(0, str(datos.get("kilos_caja", "") or ""))

        self._label(top, "Tipo de caja:", 2, 0)
        self.cbo_tipo_caja = self._combo(top, 2, 1, VALORES_MARCA, width=300)
        self.cbo_tipo_caja.set(datos.get("tipo_caja", "") or "")

        self._label(top, "Plastico/Bobina:", 2, 2)
        self.cbo_tipo_plastico = self._combo(top, 2, 3, VALORES_BOBINA, width=180)
        self.cbo_tipo_plastico.set(datos.get("tipo_plastico", "") or "")

        self._label(top, "Precinto:", 3, 0)
        self.cbo_precinto = self._combo(top, 3, 1, VALORES_PRECINTO, width=300)
        self.cbo_precinto.set(datos.get("precinto", "") or "")

        self._label(top, "Ultima edicion:", 3, 2)
        self.lbl_ultima_edicion = ctk.CTkLabel(
            top,
            text=datos.get("ultima_edicion", "") or "Sin ediciones registradas",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_SEC,
            anchor="w",
        )
        self.lbl_ultima_edicion.grid(row=3, column=3, padx=(0, 18), pady=6, sticky="w")

        self._label(top, "Detalle fabricacion:", 4, 0)
        self.txt_detalle_fabricacion = self._entry(top, 4, 1, width=560)
        self.txt_detalle_fabricacion.grid(columnspan=3, sticky="ew")
        self.txt_detalle_fabricacion.insert(0, datos.get("detalle_fabricacion", "") or "")

        grid = ctk.CTkFrame(main, fg_color="transparent")
        grid.grid(row=1, column=0, padx=24, pady=(0, 12), sticky="ew")
        grid.grid_columnconfigure((1, 3), weight=1)
        tolvas = list(datos.get("tolvas", []))[:8] + [""] * (8 - len(list(datos.get("tolvas", []))[:8]))

        for i in range(8):
            fila = i % 4
            bloque = 0 if i < 4 else 2
            ctk.CTkLabel(
                grid,
                text=f"Tolva {i + 1}:",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=COLOR_TEXTO,
                width=90,
                anchor="w",
            ).grid(row=fila, column=bloque, padx=(0, 10), pady=6, sticky="w")
            entry = ctk.CTkEntry(grid, width=220, height=30, border_color=COLOR_BORDE)
            entry.grid(row=fila, column=bloque + 1, padx=(0, 18), pady=6, sticky="w")
            entry.insert(0, tolvas[i])
            self.entries_tolvas.append(entry)

        footer = ctk.CTkFrame(main, fg_color="transparent")
        footer.grid(row=2, column=0, padx=24, pady=(8, 18), sticky="w")

        ctk.CTkButton(
            footer,
            text="GUARDAR Y SEGUIR",
            image=cargar_icono("guardar_blanco"),
            compound="left",
            width=180,
            height=40,
            corner_radius=8,
            fg_color=BG_HEADER,
            hover_color="#1a202c",
            text_color="#ffffff",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._guardar,
        ).pack(side="left", padx=(0, 10))
        ctk.CTkButton(
            footer,
            text="GUARDAR Y CERRAR",
            image=cargar_icono("guardar_blanco"),
            compound="left",
            width=170,
            height=40,
            corner_radius=8,
            fg_color=COLOR_INFO,
            hover_color=COLOR_INFO_HOVER,
            text_color="#ffffff",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self._guardar(cerrar=True),
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            footer,
            text="CANCELAR",
            image=cargar_icono("cancelar_gris"),
            compound="left",
            width=140,
            height=40,
            corner_radius=8,
            fg_color=BG_FRAME,
            hover_color=BG_LABEL,
            text_color=COLOR_TEXTO,
            border_width=1,
            border_color=COLOR_BORDE,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.destroy,
        ).pack(side="left")

    def _label(self, parent, text, row, col):
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXTO,
        ).grid(row=row, column=col, padx=(0, 10), pady=6, sticky="w")

    def _entry(self, parent, row, col, width=200):
        entry = ctk.CTkEntry(parent, width=width, height=30, border_color=COLOR_BORDE)
        entry.grid(row=row, column=col, padx=(0, 18), pady=6, sticky="w")
        return entry

    def _combo(self, parent, row, col, values, width=200):
        combo = ctk.CTkComboBox(parent, width=width, height=30, values=values, border_color=COLOR_BORDE)
        combo.grid(row=row, column=col, padx=(0, 18), pady=6, sticky="w")
        return combo

    def _set_entry(self, entry, value):
        entry.delete(0, "end")
        entry.insert(0, str(value or ""))

    def _cargar_datos(self, codigo, datos):
        self.codigo = str(codigo).strip()
        self.title(f"Editar Composicion {self.codigo}")
        self.lbl_titulo.configure(text=f"Editar Composicion del Articulo {self.codigo}")
        self._set_entry(self.txt_codigo, self.codigo)
        self._set_entry(self.txt_descripcion, datos.get("descripcion", ""))
        self._set_entry(self.txt_kilos_caja, datos.get("kilos_caja", ""))
        self.cbo_tipo_caja.set(datos.get("tipo_caja", "") or "")
        self.cbo_tipo_plastico.set(datos.get("tipo_plastico", "") or "")
        self.cbo_precinto.set(datos.get("precinto", "") or "")
        self.lbl_ultima_edicion.configure(text=datos.get("ultima_edicion", "") or "Sin ediciones registradas")
        self._set_entry(self.txt_detalle_fabricacion, datos.get("detalle_fabricacion", ""))

        tolvas = list(datos.get("tolvas", []))[:8] + [""] * (8 - len(list(datos.get("tolvas", []))[:8]))
        for entry, value in zip(self.entries_tolvas, tolvas):
            self._set_entry(entry, value)

    def _cargar_articulo(self):
        codigo = self.txt_codigo.get().strip()
        if not codigo:
            mostrar_toast(self, "Escribe un articulo para cargar.", tipo="advertencia")
            self.txt_codigo.focus_set()
            return
        datos = self.master_panel._obtener_datos_actuales_para_edicion(codigo)
        self._cargar_datos(codigo, datos)

    def _guardar(self, cerrar=False):
        codigo = self.txt_codigo.get().strip()
        if not codigo:
            mostrar_toast(self, "Escribe un articulo antes de guardar.", tipo="advertencia")
            self.txt_codigo.focus_set()
            return
        self.codigo = codigo
        datos = {
            "descripcion": self.txt_descripcion.get().strip(),
            "porcentaje": "",
            "pesos": "",
            "kilos_caja": self.txt_kilos_caja.get().strip(),
            "tipo_caja": self.cbo_tipo_caja.get().strip(),
            "tipo_plastico": self.cbo_tipo_plastico.get().strip(),
            "precinto": self.cbo_precinto.get().strip(),
            "detalle_fabricacion": self.txt_detalle_fabricacion.get().strip(),
            "tolvas": [entry.get().strip() for entry in self.entries_tolvas],
        }
        self.on_save(self.codigo, datos)
        datos_actualizados = self.master_panel._obtener_datos_actuales_para_edicion(self.codigo)
        self._cargar_datos(self.codigo, datos_actualizados)
        if cerrar:
            self.destroy()
            mostrar_toast(self.master_panel, f"Articulo {self.codigo} guardado.", tipo="exito")
        else:
            mostrar_toast(self, f"Articulo {self.codigo} guardado. Puedes seguir editando.", tipo="exito")


class VentanaTolvas(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG_APP)
        self.app = app
        self.tolva_entries = []
        self.lbl_comp_principal = None
        self.lbl_comp_detalle = None
        self.lbl_comp_lista = None
        self.recientes_frame = None
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        header = ctk.CTkFrame(self, fg_color=BG_HEADER, corner_radius=10, height=52)
        header.grid(row=0, column=0, padx=20, pady=(18, 10), sticky="ew")
        header.grid_propagate(False)
        ctk.CTkFrame(header, fg_color=TINT_OPERACION["border"], height=4, corner_radius=0).place(
            relx=0, rely=0, relwidth=1, anchor="nw"
        )
        ctk.CTkLabel(
            header,
            text="Tolvas Vertical",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#ffffff",
        ).place(relx=0.5, rely=0.5, anchor="center")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=1, column=0, padx=0, pady=(0, 0), sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        main = ctk.CTkFrame(scroll, fg_color=BG_FRAME, corner_radius=12, border_width=1, border_color=COLOR_BORDE)
        main.grid(row=1, column=0, padx=20, pady=(0, 18), sticky="nsew")
        main.grid_columnconfigure(0, weight=2)
        main.grid_columnconfigure(1, weight=2)
        main.grid_columnconfigure(2, weight=1)
        main.grid_rowconfigure(1, weight=1)
        main.grid_rowconfigure(2, weight=0)

        top = ctk.CTkFrame(main, fg_color="transparent")
        top.grid(row=0, column=0, columnspan=3, padx=24, pady=(18, 8), sticky="ew")
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            top,
            text="Ingresar Numero de Produccion:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLOR_TEXTO,
        ).grid(row=0, column=0, padx=(0, 12), sticky="w")

        self.txt_articulo = ctk.CTkEntry(top, width=180, height=32, border_color=COLOR_BORDE)
        self.txt_articulo.grid(row=0, column=1, sticky="ew")
        self.txt_articulo.bind("<Return>", lambda _e: self.mostrar())

        self.lbl_descripcion = ctk.CTkLabel(
            top,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_SEC,
            justify="left",
            anchor="w",
        )
        self.lbl_descripcion.grid(row=1, column=0, columnspan=2, pady=(6, 0), sticky="ew")

        left = ctk.CTkFrame(main, fg_color="#f7f9fb", corner_radius=10, border_width=1, border_color=COLOR_BORDE)
        left.grid(row=1, column=0, padx=(24, 12), pady=(10, 14), sticky="nsew")
        left.grid_columnconfigure(1, weight=1)
        left.grid_rowconfigure(1, weight=1)
        for fila in range(8):
            left.grid_rowconfigure(fila, weight=1)

        ctk.CTkLabel(
            left,
            text="TOLVAS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_SEC,
            fg_color=BG_LABEL,
            corner_radius=6,
            anchor="w",
            padx=10,
        ).grid(row=0, column=0, columnspan=2, padx=12, pady=(12, 8), sticky="ew", ipady=4)

        tolvas_grid = ctk.CTkFrame(left, fg_color="transparent")
        tolvas_grid.grid(row=1, column=0, columnspan=2, padx=14, pady=(0, 12), sticky="nsew")
        tolvas_grid.grid_columnconfigure(1, weight=1)
        for fila in range(8):
            tolvas_grid.grid_rowconfigure(fila, weight=1)

        for i in range(8):
            ctk.CTkLabel(
                tolvas_grid,
                text=f"Tolva {i + 1}:",
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color=COLOR_TEXTO,
                width=96,
                anchor="w",
            ).grid(row=i, column=0, padx=(0, 10), pady=3, sticky="w")
            entry = ctk.CTkEntry(tolvas_grid, width=190, height=36, border_color=COLOR_BORDE, fg_color=COLOR_READONLY, font=ctk.CTkFont(size=14, weight="bold"))
            entry.grid(row=i, column=1, padx=(0, 6), pady=3, sticky="ew")
            entry.configure(state="readonly")
            self.tolva_entries.append(entry)

        center = ctk.CTkFrame(main, fg_color="#f7f9fb", corner_radius=10, border_width=1, border_color=COLOR_BORDE)
        center.grid(row=1, column=1, padx=(0, 12), pady=(10, 14), sticky="nsew")
        center.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            center,
            text="INFORMACION DEL ARTICULO",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_SEC,
            fg_color=BG_LABEL,
            corner_radius=6,
            anchor="w",
            padx=10,
        ).grid(row=0, column=0, padx=12, pady=(12, 8), sticky="ew", ipady=4)

        ficha = ctk.CTkFrame(center, fg_color="transparent")
        ficha.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="ew")
        ficha.grid_columnconfigure(0, weight=1)
        ficha.grid_columnconfigure(1, weight=1)

        self.lbl_tipo_caja = self._label_ficha(ficha, 0, 0, "Tipo de caja")
        self.lbl_tipo_plastico = self._label_ficha(ficha, 0, 1, "Plastico/Bobina")
        self.lbl_precinto = self._label_ficha(ficha, 1, 0, "Precinto")
        self.lbl_ultima_edicion = self._label_ficha(ficha, 1, 1, "Ultima edicion")
        self.lbl_detalle_fabricacion = self._label_ficha_ancha(ficha, 2, "Detalle fabricacion")
        self.lbl_comp_principal = self._label_ficha_ancha(ficha, 3, "Composicion relacionada")
        self.lbl_comp_detalle = self._label_ficha_ancha(ficha, 4, "Ingredientes compartidos")
        self.lbl_comp_lista = self._label_ficha_ancha(ficha, 5, "Otras composiciones parecidas")
        self.recientes_frame = self._crear_panel_recientes(ficha, 6)

        right = ctk.CTkFrame(main, fg_color="#f7f9fb", corner_radius=10, border_width=1, border_color=COLOR_BORDE)
        right.grid(row=1, column=2, padx=(0, 24), pady=(10, 14), sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            right,
            text="ACCIONES",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_SEC,
            fg_color=BG_LABEL,
            corner_radius=6,
            anchor="w",
            padx=10,
        ).grid(row=0, column=0, padx=12, pady=(12, 8), sticky="ew", ipady=4)

        actions = ctk.CTkFrame(right, fg_color="transparent")
        actions.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")
        actions.grid_columnconfigure(0, weight=1)

        for indice, (texto, color, hover, command) in enumerate([
            ("MOSTRAR", BG_HEADER, BG_HEADER_HOVER, self.mostrar),
            ("AÑADIR COMP.", COLOR_SUCCESS, COLOR_SUCCESS_HOVER, self.solicitar_alta_composicion),
            ("EDITAR COMP.", COLOR_PURPLE, COLOR_PURPLE_HOVER, self.solicitar_edicion_composicion),
            ("IMPRIMIR", COLOR_INFO, COLOR_INFO_HOVER, self.imprimir),
            ("LIMPIAR", BG_FRAME, BG_LABEL, self.limpiar),
            ("VOLVER", BG_FRAME, BG_LABEL, lambda: self.app.show_view("inicio")),
            ("SALIR", COLOR_DANGER, COLOR_DANGER_HOVER, self.app.destroy),
        ]):
            ctk.CTkButton(
                actions,
                text=texto,
                height=42,
                corner_radius=8,
                fg_color=color,
                hover_color=hover,
                text_color="#ffffff" if texto in ("SALIR", "MOSTRAR", "IMPRIMIR", "EDITAR COMP.", "AÑADIR COMP.") else COLOR_TEXTO,
                border_width=0 if texto in ("MOSTRAR", "SALIR", "IMPRIMIR", "EDITAR COMP.", "AÑADIR COMP.") else 1,
                border_color=COLOR_BORDE,
                font=ctk.CTkFont(size=14, weight="bold"),
                command=command,
            ).grid(row=indice, column=0, pady=(0, 8), sticky="ew")

        bottom = ctk.CTkFrame(main, fg_color="#f7f9fb", corner_radius=10, border_width=1, border_color=COLOR_BORDE)
        bottom.grid(row=2, column=0, columnspan=3, padx=24, pady=(0, 14), sticky="ew")
        bottom.grid_columnconfigure(0, weight=0)
        bottom.grid_columnconfigure(1, weight=1)

        self.txt_porcentaje = self._campo_inferior(bottom, 0, "Ingrese linea del producto:", sufijo="%")
        self.txt_peso = self._campo_inferior(bottom, 1, "Ingrese cantidad total del producto:", sufijo="Kg")
        self.txt_uno_por_cinco = self._campo_inferior(bottom, 2, "1 x 5 kilogramos en palets de 117 cajas:", ancho=300, readonly=True)
        self.txt_seis_por_uno = self._campo_inferior(bottom, 3, "6 x 1 kilogramo en palets de 108 cajas:", ancho=300, readonly=True)
        self.txt_tres_por_uno = self._campo_inferior(bottom, 4, "3 x 1 kilogramo en palets de 162 cajas:", ancho=300, readonly=True)

        self.txt_peso.bind("<KeyRelease>", lambda _e: self._actualizar_calculos())
        self.txt_porcentaje.bind("<KeyRelease>", lambda _e: self._actualizar_calculos())

        # Acciones fijas: el contenido central puede desplazarse, pero los
        # botones operativos quedan siempre disponibles.
        right.grid_remove()
        main.grid_columnconfigure(2, weight=0)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, padx=20, pady=(4, 18), sticky="ew")
        for column in range(7):
            footer.grid_columnconfigure(column, weight=1)

        acciones_fijas = [
            ("MOSTRAR", BG_HEADER, BG_HEADER_HOVER, "#ffffff", "mostrar", self.mostrar),
            ("ANADIR COMP.", COLOR_SUCCESS, COLOR_SUCCESS_HOVER, "#ffffff", "nuevo_dia", self.solicitar_alta_composicion),
            ("EDITAR COMP.", COLOR_PURPLE, COLOR_PURPLE_HOVER, "#ffffff", "editar", self.solicitar_edicion_composicion),
            ("IMPRIMIR", COLOR_INFO, COLOR_INFO_HOVER, "#ffffff", "imprimir", self.imprimir),
            ("LIMPIAR", BG_FRAME, BG_LABEL, COLOR_TEXTO, "limpiar", self.limpiar),
            ("VOLVER", BG_FRAME, BG_LABEL, COLOR_TEXTO, "volver", lambda: self.app.show_view("inicio")),
            ("SALIR", COLOR_DANGER, COLOR_DANGER_HOVER, "#ffffff", None, self.app.destroy),
        ]
        for column, (texto, color, hover, text_color, icono, command) in enumerate(acciones_fijas):
            tono = "gris" if color == BG_FRAME else "blanco"
            ctk.CTkButton(
                footer,
                text=texto,
                image=cargar_icono(f"{icono}_{tono}") if icono else None,
                compound="left",
                height=38,
                corner_radius=8,
                fg_color=color,
                hover_color=hover,
                text_color=text_color,
                border_width=1 if color == BG_FRAME else 0,
                border_color=COLOR_BORDE,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=command,
            ).grid(row=0, column=column, padx=4, sticky="ew")

        self._actualizar_articulos_recientes()

    def _campo_inferior(self, parent, row, texto, ancho=150, sufijo="", readonly=False):
        ctk.CTkLabel(parent, text=texto, font=ctk.CTkFont(size=13, weight="bold"), text_color=COLOR_TEXTO).grid(
            row=row, column=0, padx=(14, 12), pady=6, sticky="w"
        )
        campo = ctk.CTkFrame(parent, fg_color="transparent")
        campo.grid(row=row, column=1, padx=(0, 14), pady=6, sticky="w")

        entry = ctk.CTkEntry(campo, width=ancho, height=28, border_color=COLOR_BORDE, fg_color=COLOR_READONLY if readonly else BG_FRAME)
        entry.pack(side="left")
        if readonly:
            entry.configure(state="readonly")
        if sufijo:
            ctk.CTkLabel(
                campo,
                text=sufijo,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COLOR_TEXTO,
            ).pack(side="left", padx=(6, 0))
        return entry

    def _label_ficha(self, parent, row, col, titulo):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, padx=12, pady=8, sticky="ew")
        ctk.CTkLabel(
            frame,
            text=titulo.upper(),
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_SEC,
            anchor="w",
        ).pack(anchor="w")
        valor = ctk.CTkLabel(
            frame,
            text="-",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXTO,
            anchor="w",
            justify="left",
        )
        valor.pack(anchor="w", pady=(2, 0))
        return valor

    def _label_ficha_ancha(self, parent, row, titulo):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=0, columnspan=2, padx=12, pady=8, sticky="ew")
        ctk.CTkLabel(
            frame,
            text=titulo.upper(),
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_SEC,
            anchor="w",
        ).pack(anchor="w")
        valor = ctk.CTkLabel(
            frame,
            text="-",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXTO,
            anchor="w",
            justify="left",
            wraplength=430,
        )
        valor.pack(anchor="w", pady=(2, 0), fill="x")
        return valor

    def _crear_panel_recientes(self, parent, row):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=0, columnspan=2, padx=12, pady=8, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            frame,
            text="ULTIMOS ARTICULOS CONSULTADOS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_SEC,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        body = ctk.CTkFrame(frame, fg_color="#f8fafc", corner_radius=8, border_width=1, border_color=COLOR_BORDE)
        body.grid(row=1, column=0, pady=(6, 0), sticky="ew")
        body.grid_columnconfigure(0, weight=1)
        return body

    def _usar_articulo_reciente(self, codigo):
        self.txt_articulo.delete(0, "end")
        self.txt_articulo.insert(0, codigo)
        self.mostrar()

    def _actualizar_articulos_recientes(self):
        if self.recientes_frame is None:
            return

        for child in self.recientes_frame.winfo_children():
            child.destroy()

        recientes = self.app.get_tolvas_recientes()
        if not recientes:
            ctk.CTkLabel(
                self.recientes_frame,
                text="Todavia no has consultado articulos en esta sesion.",
                font=ctk.CTkFont(size=12),
                text_color=COLOR_SEC,
                anchor="w",
                justify="left",
            ).grid(row=0, column=0, padx=10, pady=10, sticky="ew")
            return

        for row, item in enumerate(recientes):
            codigo = str(item.get("codigo", "")).strip()
            descripcion = str(item.get("descripcion", "")).strip() or "Sin descripcion"
            texto = f"{codigo} - {descripcion}"
            ctk.CTkButton(
                self.recientes_frame,
                text=texto,
                height=32,
                corner_radius=8,
                fg_color=BG_FRAME,
                hover_color=BG_LABEL,
                text_color=COLOR_TEXTO,
                border_width=1,
                border_color=COLOR_BORDE,
                anchor="w",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda cod=codigo: self._usar_articulo_reciente(cod),
            ).grid(row=row, column=0, padx=10, pady=(10 if row == 0 else 0, 6), sticky="ew")

    def _set_label(self, label, prefix, value):
        label.configure(text=value if str(value).strip() else "-")

    def _formatear_ingredientes(self, ingredientes):
        if not ingredientes:
            return ""
        return ", ".join(ing.title() for ing in ingredientes)

    def _actualizar_composiciones_parecidas(self, codigo):
        parecidas = buscar_composiciones_parecidas(codigo, limite=4)
        if not parecidas:
            self._set_label(self.lbl_comp_principal, "Composicion relacionada", "No se han encontrado composiciones parecidas.")
            self._set_label(self.lbl_comp_detalle, "Ingredientes compartidos", "")
            self._set_label(self.lbl_comp_lista, "Otras composiciones parecidas", "")
            return

        principal = parecidas[0]
        descripcion = f"{principal['codigo']} - {principal['descripcion'] or 'Sin descripcion'}"
        self._set_label(self.lbl_comp_principal, "Composicion relacionada", descripcion)

        detalle = f"Comparten {principal['total_compartidos']} ingredientes: {self._formatear_ingredientes(principal['compartidos'])}"
        if principal["solo_actual"]:
            detalle += f"\nEste articulo ademas lleva: {self._formatear_ingredientes(principal['solo_actual'])}"
        if principal["solo_otro"]:
            detalle += f"\nEl relacionado ademas lleva: {self._formatear_ingredientes(principal['solo_otro'])}"
        self._set_label(self.lbl_comp_detalle, "Ingredientes compartidos", detalle)

        resto = []
        for item in parecidas[1:]:
            resto.append(
                f"{item['codigo']} - {item['descripcion'] or 'Sin descripcion'} "
                f"({item['total_compartidos']} en comun)"
            )
        self._set_label(self.lbl_comp_lista, "Otras composiciones parecidas", "\n".join(resto))

    def _set_entry(self, entry, value):
        estado = entry.cget("state")
        if estado == "readonly":
            entry.configure(state="normal")
        entry.delete(0, "end")
        entry.insert(0, value)
        if estado == "readonly":
            entry.configure(state="readonly")

    def _to_float(self, value):
        try:
            return float(str(value).replace(",", ".") or 0)
        except ValueError:
            return 0.0

    def _formatear_palets_cajas(self, valor_base, cajas_por_palet):
        if valor_base <= 0 or cajas_por_palet <= 0:
            return ""
        palets = int(valor_base // cajas_por_palet)
        resto = valor_base % cajas_por_palet
        cajas = int(resto) if resto.is_integer() else int(resto) + 1
        return f"{palets} PALETS Y {cajas} CAJAS"

    def _actualizar_calculos(self):
        cantidad_total = self._to_float(self.txt_peso.get())
        porcentaje_raw = self.txt_porcentaje.get().replace("%", "").strip()
        porcentaje = self._to_float(porcentaje_raw)
        if cantidad_total <= 0 or porcentaje <= 0:
            self._set_entry(self.txt_uno_por_cinco, "")
            self._set_entry(self.txt_seis_por_uno, "")
            self._set_entry(self.txt_tres_por_uno, "")
            return
        base = cantidad_total * 100 / porcentaje
        self._set_entry(self.txt_uno_por_cinco, self._formatear_palets_cajas(base / 5, 117))
        self._set_entry(self.txt_seis_por_uno, self._formatear_palets_cajas(base / 6, 108))
        self._set_entry(self.txt_tres_por_uno, self._formatear_palets_cajas(base / 3, 162))

    def _rellenar_tolvas(self, tolvas):
        tolvas = list(tolvas[:8]) + [""] * (8 - len(tolvas))
        for entry, valor in zip(self.tolva_entries, tolvas):
            self._set_entry(entry, valor if valor else "Vacia")

    def _obtener_datos_actuales_para_edicion(self, codigo):
        datos_tolvas = buscar_tolvas(codigo) or {}
        producto = buscar_producto(codigo) or {}
        return {
            "descripcion": datos_tolvas.get("descripcion", "") or producto.get("descripcion", ""),
            "kilos_caja": datos_tolvas.get("kilos_caja", "") or str(producto.get("factor", "") or ""),
            "tipo_caja": datos_tolvas.get("tipo_caja", ""),
            "tipo_plastico": datos_tolvas.get("tipo_plastico", ""),
            "precinto": datos_tolvas.get("precinto", ""),
            "detalle_fabricacion": datos_tolvas.get("detalle_fabricacion", ""),
            "ultima_edicion": datos_tolvas.get("ultima_edicion", ""),
            "tolvas": list(datos_tolvas.get("tolvas", []))[:8] if datos_tolvas else list((producto.get("tolvas", []) or [])[:8]),
        }

    def _solicitar_clave_admin(self):
        clave = ask_admin_password(self, title="Acceso protegido", prompt="Introduce la clave de administrador:")
        if clave is None:
            return False
        if not verificar_clave_admin(clave):
            messagebox.showerror("Acceso denegado", "La clave introducida no es correcta.")
            return False
        return True

    def solicitar_alta_composicion(self):
        codigo = self.txt_articulo.get().strip()
        if not codigo:
            mostrar_toast(self, "Primero escribe el articulo que quieres añadir.", tipo="advertencia")
            self.txt_articulo.focus_set()
            return

        if not self._solicitar_clave_admin():
            return

        if buscar_tolvas(codigo):
            mostrar_toast(self, f"El articulo {codigo} ya tiene una composicion guardada. Usa 'EDITAR COMP.'.", tipo="advertencia")
            return

        datos = self._obtener_datos_actuales_para_edicion(codigo)
        editor = EditorComposicionTolvas(self, codigo, datos, self._guardar_composicion)
        editor.focus_set()

    def solicitar_edicion_composicion(self):
        codigo = self.txt_articulo.get().strip()
        if not codigo:
            mostrar_toast(self, "Primero escribe el articulo que quieres editar.", tipo="advertencia")
            self.txt_articulo.focus_set()
            return

        if not self._solicitar_clave_admin():
            return

        datos = self._obtener_datos_actuales_para_edicion(codigo)
        editor = EditorComposicionTolvas(self, codigo, datos, self._guardar_composicion)
        editor.focus_set()

    def _guardar_composicion(self, codigo, datos):
        guardar_tolvas_producto(codigo, datos)
        if self.txt_articulo.get().strip() == str(codigo).strip():
            self.mostrar()

    def mostrar(self):
        codigo = self.txt_articulo.get().strip()
        if not codigo:
            mostrar_toast(self, "Debes introducir un articulo de produccion.", tipo="advertencia")
            self.txt_articulo.focus_set()
            return

        datos_tolvas = buscar_tolvas(codigo)
        producto = buscar_producto(codigo)

        if datos_tolvas:
            tolvas = datos_tolvas.get("tolvas", [])
            descripcion = datos_tolvas.get("descripcion", "") or (producto or {}).get("descripcion", "")
            porcentaje = datos_tolvas.get("porcentaje", "")
            tipo_caja = datos_tolvas.get("tipo_caja", "")
            tipo_plastico = datos_tolvas.get("tipo_plastico", "")
            precinto = datos_tolvas.get("precinto", "")
            detalle_fabricacion = datos_tolvas.get("detalle_fabricacion", "")
            ultima_edicion = datos_tolvas.get("ultima_edicion", "")
        elif producto:
            lista = producto.get("tolvas", []) or []
            tolvas = list(lista[:8]) + [""] * (8 - len(lista))
            descripcion = producto.get("descripcion", "")
            porcentaje = ""
            tipo_caja = ""
            tipo_plastico = ""
            precinto = ""
            detalle_fabricacion = ""
            ultima_edicion = ""
        else:
            mostrar_toast(self, f"No se encontro el articulo {codigo}.", tipo="advertencia")
            self.limpiar(mantener_codigo=True)
            return

        self._rellenar_tolvas(tolvas)
        self.lbl_descripcion.configure(text=descripcion)
        self._set_label(self.lbl_tipo_caja, "Tipo de caja", tipo_caja)
        self._set_label(self.lbl_tipo_plastico, "Plastico/Bobina", tipo_plastico)
        self._set_label(self.lbl_precinto, "Precinto", precinto)
        self._set_label(self.lbl_detalle_fabricacion, "Detalle fabricacion", detalle_fabricacion)
        self._set_label(self.lbl_ultima_edicion, "Ultima edicion", ultima_edicion)
        self._actualizar_composiciones_parecidas(codigo)
        self._set_entry(self.txt_porcentaje, str(porcentaje))
        self._set_entry(self.txt_peso, "")
        self._actualizar_calculos()
        self.app.registrar_tolvas_reciente(codigo, descripcion)
        self._actualizar_articulos_recientes()

    def limpiar(self, mantener_codigo=False):
        if not mantener_codigo:
            self.txt_articulo.delete(0, "end")
        self.lbl_descripcion.configure(text="")
        self._set_label(self.lbl_tipo_caja, "Tipo de caja", "")
        self._set_label(self.lbl_tipo_plastico, "Plastico/Bobina", "")
        self._set_label(self.lbl_precinto, "Precinto", "")
        self._set_label(self.lbl_detalle_fabricacion, "Detalle fabricacion", "")
        self._set_label(self.lbl_ultima_edicion, "Ultima edicion", "")
        self._set_label(self.lbl_comp_principal, "Composicion relacionada", "")
        self._set_label(self.lbl_comp_detalle, "Ingredientes compartidos", "")
        self._set_label(self.lbl_comp_lista, "Otras composiciones parecidas", "")
        self._rellenar_tolvas([""] * 8)
        self._set_entry(self.txt_porcentaje, "")
        self._set_entry(self.txt_peso, "")
        self._set_entry(self.txt_uno_por_cinco, "")
        self._set_entry(self.txt_seis_por_uno, "")
        self._set_entry(self.txt_tres_por_uno, "")
        self.txt_articulo.focus_set()

    def refresh(self):
        if not self.txt_articulo.get().strip():
            self.limpiar()
        self._actualizar_articulos_recientes()

    def imprimir(self):
        codigo = self.txt_articulo.get().strip()
        if not codigo:
            mostrar_toast(self, "Primero debes mostrar un articulo para imprimir.", tipo="advertencia")
            self.txt_articulo.focus_set()
            return

        try:
            ruta_temporal = Path(tempfile.gettempdir()) / "ancavico_tolvas.pdf"
            pdf = SimplePDF(620, 760)
            pdf.rect(30, 30, 560, 690, fill=BG_FRAME, stroke=COLOR_BORDE, line_width=1)
            pdf.rect(30, 30, 560, 46, fill=BG_HEADER)
            pdf.text(205, 58, "TOLVAS VERTICAL", size=18, color="#ffffff")
            pdf.text(50, 100, f"Articulo: {codigo}", size=12)
            pdf.text(50, 122, f"Descripcion: {self.lbl_descripcion.cget('text')}", size=10)
            pdf.text(50, 142, f"Tipo de caja: {self.lbl_tipo_caja.cget('text')}", size=10)
            pdf.text(300, 142, f"Bobina: {self.lbl_tipo_plastico.cget('text')}", size=10)
            pdf.text(50, 160, f"Precinto: {self.lbl_precinto.cget('text')}", size=10)
            pdf.text(300, 160, f"Ultima edicion: {self.lbl_ultima_edicion.cget('text')}", size=10)
            pdf.text(50, 180, f"Detalle fabricacion: {self.lbl_detalle_fabricacion.cget('text')}", size=10)

            y = 218
            for indice, entry in enumerate(self.tolva_entries, start=1):
                pdf.rect(50, y - 16, 500, 22, fill="#f8fafc", stroke=COLOR_BORDE, line_width=1)
                pdf.text(60, y, f"Tolva {indice}: {entry.get()}", size=11)
                y += 28

            y += 8
            extras = [
                f"Porcentaje: {self.txt_porcentaje.get()}",
                f"Cantidad Total: {self.txt_peso.get()} Kg",
                f"1 por 5 Kilogramos: {self.txt_uno_por_cinco.get()}",
                f"6 por 1 Kilogramo: {self.txt_seis_por_uno.get()}",
                f"3 por 1 Kilogramos: {self.txt_tres_por_uno.get()}",
            ]
            for texto in extras:
                pdf.text(50, y, texto, size=11)
                y += 22

            pdf.save(ruta_temporal)
            os.startfile(str(ruta_temporal))
        except Exception as error:
            messagebox.showerror(
                "No se pudo abrir el PDF",
                f"No fue posible generar o abrir el PDF de tolvas.\n\nDetalle: {error}",
            )
