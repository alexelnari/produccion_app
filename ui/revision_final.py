import customtkinter as ctk

from ui.toast import mostrar_toast
from ui.icons import cargar_icono
from ui.theme import BG_APP, BG_FRAME, BG_HEADER, BG_LABEL, COLOR_BORDE, COLOR_TEXTO, COLOR_SEC, TINT_PRODUCCION


class VentanaRevisionFinal(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG_APP)
        self.app = app
        self.selected_index = None
        self.entries = {}
        self.txt_incidencias = None
        self.listado = None
        self.lbl_totales = None
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)

        header = ctk.CTkFrame(self, fg_color=BG_HEADER, corner_radius=10, height=52)
        header.grid(row=0, column=0, padx=20, pady=(18, 10), sticky="ew")
        header.grid_propagate(False)
        ctk.CTkFrame(header, fg_color=TINT_PRODUCCION["border"], height=4, corner_radius=0).place(
            relx=0, rely=0, relwidth=1, anchor="nw"
        )
        ctk.CTkLabel(
            header,
            text="Revision Final de Hoja",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#ffffff",
        ).place(relx=0.5, rely=0.5, anchor="center")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=1, column=0, padx=0, pady=(0, 0), sticky="nsew")
        scroll.grid_columnconfigure(0, weight=3)
        scroll.grid_columnconfigure(1, weight=2)

        left = ctk.CTkFrame(scroll, fg_color=BG_FRAME, corner_radius=10, border_width=1, border_color=COLOR_BORDE)
        left.grid(row=1, column=0, padx=(20, 8), pady=8, sticky="nsew")
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            left,
            text="LINEAS DEL DIA",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_SEC,
            fg_color=BG_LABEL,
            corner_radius=6,
            anchor="w",
            padx=10,
        ).grid(row=0, column=0, padx=14, pady=(10, 6), sticky="ew", ipady=4)

        self.listado = ctk.CTkScrollableFrame(left, fg_color="#fbfcfd")
        self.listado.grid(row=1, column=0, padx=14, pady=(0, 10), sticky="nsew")
        self.listado.grid_columnconfigure(0, weight=1)

        self.lbl_totales = ctk.CTkLabel(
            left,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2b6cb0",
            anchor="w",
        )
        self.lbl_totales.grid(row=2, column=0, padx=14, pady=(0, 14), sticky="ew")

        right = ctk.CTkFrame(scroll, fg_color=BG_FRAME, corner_radius=10, border_width=1, border_color=COLOR_BORDE)
        right.grid(row=1, column=1, padx=(8, 20), pady=8, sticky="nsew")
        right.grid_columnconfigure(0, weight=0)
        right.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            right,
            text="EDITAR LINEA",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_SEC,
            fg_color=BG_LABEL,
            corner_radius=6,
            anchor="w",
            padx=10,
        ).grid(row=0, column=0, columnspan=2, padx=14, pady=(10, 6), sticky="ew", ipady=4)

        campos = [
            ("pedido", "Orden:"),
            ("tipo", "Tipo:"),
            ("bobina", "Bobina:"),
            ("etiqueta", "Etiqueta:"),
            ("caja", "Caja:"),
            ("lote", "Lote:"),
            ("producto", "Genero:"),
            ("observaciones", "Observaciones:"),
            ("cantidad", "Cantidad:"),
            ("peso", "Peso Kg:"),
        ]
        for fila, (clave, texto) in enumerate(campos, start=1):
            ctk.CTkLabel(
                right,
                text=texto,
                font=ctk.CTkFont(size=13),
                text_color=COLOR_SEC,
                width=120,
                anchor="w",
            ).grid(row=fila, column=0, padx=(16, 6), pady=4, sticky="w")
            entry = ctk.CTkEntry(right, width=220, height=30, border_color=COLOR_BORDE, font=ctk.CTkFont(size=13))
            entry.grid(row=fila, column=1, padx=(0, 16), pady=4, sticky="ew")
            self.entries[clave] = entry

        ctk.CTkLabel(
            right,
            text="Incidencias:",
            font=ctk.CTkFont(size=13),
            text_color=COLOR_SEC,
            anchor="w",
        ).grid(row=11, column=0, columnspan=2, padx=16, pady=(10, 4), sticky="w")
        self.txt_incidencias = ctk.CTkTextbox(right, height=110, border_width=1, border_color=COLOR_BORDE, font=ctk.CTkFont(size=13))
        self.txt_incidencias.grid(row=12, column=0, columnspan=2, padx=16, pady=(0, 14), sticky="ew")

        acciones_layout = ctk.CTkFrame(self, fg_color="transparent")
        acciones_layout.grid(row=2, column=0, padx=20, pady=(4, 8), sticky="ew")
        acciones_layout.grid_columnconfigure(0, weight=3)
        acciones_layout.grid_columnconfigure(1, weight=2)

        acciones = ctk.CTkFrame(acciones_layout, fg_color="transparent")
        acciones.grid(row=0, column=1, sticky="e")

        botones = [
            ("NUEVA", "#2b6cb0", "#2c5282", "nuevo_dia", self.nueva_linea),
            ("GUARDAR CAMBIOS", BG_HEADER, "#1a202c", "guardar", self.guardar_cambios),
            ("ELIMINAR", "#c53030", "#9b2c2c", "eliminar", self.eliminar_linea),
        ]
        for texto, fg, hover, icono, cmd in botones:
            ctk.CTkButton(
                acciones,
                text=texto,
                image=cargar_icono(f"{icono}_blanco"),
                compound="left",
                width=140,
                height=38,
                corner_radius=8,
                fg_color=fg,
                hover_color=hover,
                text_color="#ffffff",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=cmd,
            ).pack(side="left", padx=(0, 8))

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=3, column=0, padx=20, pady=(4, 18), sticky="w")
        for texto, fg, hover, icono, cmd in [
            ("VOLVER A PRODUCCION", BG_FRAME, BG_APP, "volver", lambda: self.app.show_view("produccion")),
            ("VER HOJA", BG_HEADER, "#1a202c", "documento", lambda: self.app.show_view("hoja_produccion")),
            ("IMPRIMIR", "#2b6cb0", "#2c5282", "imprimir", self._abrir_hoja_para_imprimir),
        ]:
            tono = "gris" if fg == BG_FRAME else "blanco"
            ctk.CTkButton(
                footer,
                text=texto,
                image=cargar_icono(f"{icono}_{tono}"),
                compound="left",
                width=170,
                height=40,
                corner_radius=8,
                fg_color=fg,
                hover_color=hover,
                text_color="#ffffff" if fg != BG_FRAME else COLOR_TEXTO,
                border_width=1 if fg == BG_FRAME else 0,
                border_color=COLOR_BORDE,
                font=ctk.CTkFont(size=13, weight="bold"),
                command=cmd,
            ).pack(side="left", padx=(0, 10))

    def _abrir_hoja_para_imprimir(self):
        self.guardar_cambios(silencioso=True)
        self.app.show_view("hoja_produccion")

    def _set_incidencias(self, texto):
        self.txt_incidencias.delete("1.0", "end")
        self.txt_incidencias.insert("1.0", texto or "")

    def _update_totals_label(self):
        frame_hoja = self.app.frames.get("hoja_produccion")
        filas = self.app.get_lineas_produccion()
        if frame_hoja:
            totales = frame_hoja._calcular_totales(filas)
        else:
            totales = {"cajas": 0, "bobinas": 0, "palets": 0, "kg": 0}
        self.lbl_totales.configure(
            text=f"Totales | Cajas: {totales['cajas']} | Bobinas: {totales['bobinas']} | Palets: {totales['palets']} | Kg: {totales['kg']}"
        )

    def _clear_editor(self):
        self.selected_index = None
        for entry in self.entries.values():
            entry.delete(0, "end")

    def _fill_editor(self, linea, indice):
        self.selected_index = indice
        for clave, entry in self.entries.items():
            entry.delete(0, "end")
            entry.insert(0, str(linea.get(clave, "")))

    def _save_editor_to_state(self):
        if self.selected_index is None:
            return False
        lineas = self.app.get_lineas_produccion()
        if not (0 <= self.selected_index < len(lineas)):
            return False
        linea = lineas[self.selected_index]
        for clave, entry in self.entries.items():
            linea[clave] = entry.get().strip()
        return True

    def _render_lineas(self):
        for child in self.listado.winfo_children():
            child.destroy()

        lineas = self.app.get_lineas_produccion()
        if not lineas:
            ctk.CTkLabel(
                self.listado,
                text="Aun no hay lineas guardadas.",
                text_color=COLOR_SEC,
                anchor="w",
            ).grid(row=0, column=0, padx=8, pady=8, sticky="ew")
            return

        for indice, linea in enumerate(lineas):
            fila = ctk.CTkFrame(self.listado, fg_color="#ffffff", corner_radius=8, border_width=1, border_color=COLOR_BORDE)
            fila.grid(row=indice, column=0, padx=4, pady=4, sticky="ew")
            fila.grid_columnconfigure(0, weight=1)

            resumen = (
                f"{indice + 1}. Orden {linea.get('pedido', '')} | {linea.get('tipo', '')} | "
                f"Etq {linea.get('etiqueta', '')} | Gen {linea.get('producto', '') or linea.get('observaciones', '')} | "
                f"Cant {linea.get('cantidad', '')} | Kg {linea.get('peso', '')}"
            )
            ctk.CTkLabel(
                fila,
                text=resumen,
                font=ctk.CTkFont(size=12),
                text_color=COLOR_TEXTO,
                anchor="w",
                justify="left",
            ).grid(row=0, column=0, padx=10, pady=10, sticky="ew")
            ctk.CTkButton(
                fila,
                text="EDITAR",
                image=cargar_icono("editar_blanco"),
                compound="left",
                width=90,
                height=32,
                corner_radius=8,
                fg_color=BG_HEADER,
                hover_color="#1a202c",
                text_color="#ffffff",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda i=indice: self._fill_editor(self.app.get_lineas_produccion()[i], i),
            ).grid(row=0, column=1, padx=(0, 10), pady=8)

    def nueva_linea(self):
        lineas = self.app.get_lineas_produccion()
        lineas.append(
            {
                "pedido": "",
                "tipo": "PALET",
                "bobina": "",
                "etiqueta": "",
                "caja": "",
                "lote": "",
                "producto": "",
                "observaciones": "",
                "cantidad": "",
                "peso": "",
                "palets": "",
                "fabricacion": "",
                "ultima_hora": "",
                "factor_producto": "",
            }
        )
        self._render_lineas()
        self._fill_editor(lineas[-1], len(lineas) - 1)
        self._update_totals_label()

    def guardar_cambios(self, silencioso=False):
        self._save_editor_to_state()
        self.app.get_detalle_dia()["incidencias"] = self.txt_incidencias.get("1.0", "end").strip()
        self.app.save_current_production()
        self._render_lineas()
        self._update_totals_label()
        if not silencioso:
            mostrar_toast(self, "Cambios guardados correctamente.", tipo="exito")

    def eliminar_linea(self):
        if self.selected_index is None:
            mostrar_toast(self, "Primero selecciona una linea para eliminar.", tipo="advertencia")
            return
        lineas = self.app.get_lineas_produccion()
        if not (0 <= self.selected_index < len(lineas)):
            return
        lineas.pop(self.selected_index)
        self._clear_editor()
        self.app.save_current_production()
        self._render_lineas()
        self._update_totals_label()
        mostrar_toast(self, "Linea eliminada correctamente.", tipo="exito")

    def refresh(self):
        self._render_lineas()
        self._set_incidencias(self.app.get_detalle_dia().get("incidencias", ""))
        self._clear_editor()
        self._update_totals_label()
