import customtkinter as ctk
from tkinter import messagebox

from ui.toast import mostrar_toast
from ui.icons import cargar_icono
from ui.theme import (
    BG_APP,
    BG_FRAME,
    BG_HEADER,
    BG_LABEL,
    COLOR_BORDE,
    COLOR_TEXTO,
    COLOR_SEC,
    COLOR_READONLY,
    TINT_PRODUCCION,
)

VALORES_BOBINA = ["", "Bob. Ancavico", "Bob. Transparente", "Bob. Rejo", "Bob. Frozzenbox", "Bob. Martinez", "Plastico a Granel"]
VALORES_MARCA = ["", "Ancavico Blanca 6 Kg", "Ancavico Negra 6 Kg", "Blancas 6 Kg", "Top Gel", "Ancavico 10 Kg", "Sopa 5 Kg", "Salpicon 5 Kg", "Blancas 4 Kg", "Ancavico 4 Kg"]


class VentanaDetalleProduccion(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG_APP)
        self.app = app
        self.filas = []
        self.btn_guardar = None
        self.lbl_ultimo_lote_1 = None
        self.lbl_ultimo_lote_2 = None
        self.lbl_ultimo_lote_3 = None
        self._build_ui()
        self._configurar_flujo_teclado()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        header = ctk.CTkFrame(self, fg_color=BG_HEADER, corner_radius=10, height=52)
        header.grid(row=0, column=0, padx=20, pady=(18, 14), sticky="ew")
        header.grid_propagate(False)
        ctk.CTkFrame(header, fg_color=TINT_PRODUCCION["border"], height=4, corner_radius=0).place(
            relx=0, rely=0, relwidth=1, anchor="nw"
        )
        ctk.CTkLabel(
            header,
            text="Detalles de Produccion",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#ffffff",
        ).place(relx=0.5, rely=0.5, anchor="center")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=1, column=0, padx=0, pady=(0, 0), sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        body = ctk.CTkFrame(scroll, fg_color="transparent")
        body.grid(row=1, column=0, padx=20, pady=(0, 14), sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=0)
        body.grid_rowconfigure(0, weight=1)

        contenido = ctk.CTkFrame(body, fg_color="transparent")
        contenido.grid(row=0, column=0, sticky="nsew", padx=(0, 14))

        card_lote = ctk.CTkFrame(
            contenido,
            fg_color=BG_FRAME,
            corner_radius=10,
            border_width=1,
            border_color=COLOR_BORDE,
        )
        card_lote.pack(fill="x", pady=(0, 12))

        self._section_label(card_lote, "Lote de Bobina")

        lote_grid = ctk.CTkFrame(card_lote, fg_color="transparent")
        lote_grid.pack(fill="x", padx=14, pady=(4, 12))

        ctk.CTkLabel(lote_grid, text="Tipo", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_SEC).grid(row=0, column=0, padx=6, pady=(0, 4), sticky="w")
        ctk.CTkLabel(lote_grid, text="Numero de Lote", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_SEC).grid(row=0, column=1, padx=6, pady=(0, 4), sticky="w")

        self.cbo_lote_1 = self._combo_lote(lote_grid, 1, 0, lambda valor: self._on_lote_tipo_change(1, valor))
        self.txt_lote_1 = self._entry_lote(lote_grid, 1, 1)
        self.lbl_ultimo_lote_1 = self._label_ultimo_lote(lote_grid, 1)
        self.cbo_lote_2 = self._combo_lote(lote_grid, 2, 0, lambda valor: self._on_lote_tipo_change(2, valor))
        self.txt_lote_2 = self._entry_lote(lote_grid, 2, 1)
        self.lbl_ultimo_lote_2 = self._label_ultimo_lote(lote_grid, 2)
        self.cbo_lote_3 = self._combo_lote(lote_grid, 3, 0, lambda valor: self._on_lote_tipo_change(3, valor))
        self.txt_lote_3 = self._entry_lote(lote_grid, 3, 1)
        self.lbl_ultimo_lote_3 = self._label_ultimo_lote(lote_grid, 3)
        self._igualar_ancho_combos_lote()

        card_marcas = ctk.CTkFrame(
            contenido,
            fg_color=BG_FRAME,
            corner_radius=10,
            border_width=1,
            border_color=COLOR_BORDE,
        )
        card_marcas.pack(fill="both", expand=True)

        self._section_label(card_marcas, "Marca de Cajas")

        tabla = ctk.CTkFrame(card_marcas, fg_color="transparent")
        tabla.pack(fill="both", expand=True, padx=14, pady=(4, 12))

        cabeceras_tabla = ["Marca de Caja", "Etiqueta", "Cantidad", "Gastado", "Resto Total"]
        anchos = [210, 120, 90, 90, 120]
        for col, (txt, w) in enumerate(zip(cabeceras_tabla, anchos)):
            ctk.CTkLabel(
                tabla,
                text=txt,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=COLOR_SEC,
                width=w,
                anchor="w",
            ).grid(row=0, column=col, padx=4, pady=(4, 2), sticky="w")

        for i in range(6):
            self.filas.append(self._fila_marca(tabla, i + 1, anchos))
        self._igualar_ancho_combos_marca()

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, padx=20, pady=(0, 18), sticky="e")

        self.btn_guardar = ctk.CTkButton(
            footer,
            text="GUARDAR",
            image=cargar_icono("guardar_blanco"),
            compound="left",
            width=140,
            height=46,
            corner_radius=8,
            fg_color=BG_HEADER,
            hover_color="#1a202c",
            text_color="#ffffff",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.guardar,
        )
        self.btn_guardar.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            footer,
            text="VOLVER",
            image=cargar_icono("volver_gris"),
            compound="left",
            width=140,
            height=46,
            corner_radius=8,
            fg_color=BG_FRAME,
            hover_color=BG_APP,
            text_color=COLOR_TEXTO,
            border_width=1,
            border_color=COLOR_BORDE,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=lambda: self.app.show_view("produccion"),
        ).pack(side="left")

    def _section_label(self, parent, texto):
        ctk.CTkLabel(
            parent,
            text=texto.upper(),
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_SEC,
            fg_color=BG_LABEL,
            corner_radius=6,
            anchor="w",
            padx=10,
        ).pack(fill="x", padx=14, pady=(10, 4), ipady=4)

    def _medir_ancho_combo(self, combo, texto, minimo, maximo):
        fuente = combo.cget("font")
        ancho_texto = fuente.measure(texto) if texto else 0
        return max(minimo, min(maximo, ancho_texto + 46))

    def _igualar_ancho_combos(self, combos, minimo, maximo):
        if not combos:
            return
        ancho = max(self._medir_ancho_combo(c, c.get(), minimo, maximo) for c in combos)
        for c in combos:
            c.configure(width=ancho)

    def _igualar_ancho_combos_lote(self):
        self._igualar_ancho_combos([self.cbo_lote_1, self.cbo_lote_2, self.cbo_lote_3], 90, 260)

    def _igualar_ancho_combos_marca(self):
        self._igualar_ancho_combos([fila["marca"] for fila in self.filas], 90, 210)

    def _combo_lote(self, parent, row, col, command=None):
        kwargs = {"width": 260, "values": VALORES_BOBINA, "border_color": COLOR_BORDE}
        if command:
            kwargs["command"] = command
        cbo = ctk.CTkComboBox(parent, **kwargs)
        cbo.grid(row=row, column=col, padx=6, pady=4, sticky="w")
        cbo.set(VALORES_BOBINA[0])
        return cbo

    def _entry_lote(self, parent, row, col):
        entry = ctk.CTkEntry(parent, width=260, height=30, border_color=COLOR_BORDE)
        entry.grid(row=row, column=col, padx=6, pady=4, sticky="w")
        return entry

    def _label_ultimo_lote(self, parent, row):
        label = ctk.CTkLabel(
            parent,
            text="Ultimo lote usado: -",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_SEC,
            anchor="w",
        )
        label.grid(row=row, column=2, padx=(6, 0), pady=4, sticky="w")
        return label

    def _get_lote_widgets(self, indice):
        pares = {
            1: (self.cbo_lote_1, self.txt_lote_1, self.lbl_ultimo_lote_1),
            2: (self.cbo_lote_2, self.txt_lote_2, self.lbl_ultimo_lote_2),
            3: (self.cbo_lote_3, self.txt_lote_3, self.lbl_ultimo_lote_3),
        }
        return pares[indice]

    def _set_ultimo_lote_label(self, label, ultimo_lote):
        texto = ultimo_lote.strip() if str(ultimo_lote).strip() else "-"
        label.configure(text=f"Ultimo lote usado: {texto}")

    def _on_lote_tipo_change(self, indice, tipo_bobina):
        combo, entry, label = self._get_lote_widgets(indice)
        self._igualar_ancho_combos_lote()
        tipo_bobina = (tipo_bobina or combo.get() or "").strip()
        ultimo_lote = self.app.db.get_latest_lote_for_tipo_bobina(tipo_bobina)
        self._set_ultimo_lote_label(label, ultimo_lote)

        valor_actual = entry.get().strip()
        if ultimo_lote and not valor_actual:
            self._set_entry_text(entry, ultimo_lote)

    def _calcular_resto(self, cantidad, gastado):
        try:
            cantidad_num = float(str(cantidad).replace(",", ".") or 0)
        except ValueError:
            cantidad_num = 0.0
        try:
            gastado_num = float(str(gastado).replace(",", ".") or 0)
        except ValueError:
            gastado_num = 0.0

        resto = cantidad_num - gastado_num
        if resto.is_integer():
            return str(int(resto))
        return f"{resto:.2f}".rstrip("0").rstrip(".")

    def _actualizar_resto_fila(self, fila_widgets):
        resto = self._calcular_resto(fila_widgets["cantidad"].get(), fila_widgets["gastado"].get())
        fila_widgets["resto"].configure(state="normal")
        fila_widgets["resto"].delete(0, "end")
        fila_widgets["resto"].insert(0, resto)
        fila_widgets["resto"].configure(state="readonly")

    def _fila_marca(self, parent, row, anchos):
        cbo = ctk.CTkComboBox(parent, width=anchos[0], values=VALORES_MARCA, border_color=COLOR_BORDE, height=28)
        cbo.configure(command=lambda _valor: self._igualar_ancho_combos_marca())
        cbo.grid(row=row, column=0, padx=4, pady=3, sticky="w")
        cbo.set(VALORES_MARCA[0])

        entries = []
        for col, w in enumerate(anchos[1:], start=1):
            entry = ctk.CTkEntry(parent, width=w, height=28, border_color=COLOR_BORDE)
            entry.grid(row=row, column=col, padx=4, pady=3, sticky="w")
            entries.append(entry)

        entries[3].configure(state="readonly", fg_color=COLOR_READONLY)

        fila_widgets = {"marca": cbo, "etiqueta": entries[0], "cantidad": entries[1], "gastado": entries[2], "resto": entries[3]}
        entries[1].bind("<KeyRelease>", lambda _event, fila=fila_widgets: self._actualizar_resto_fila(fila))
        entries[2].bind("<KeyRelease>", lambda _event, fila=fila_widgets: self._actualizar_resto_fila(fila))
        return fila_widgets

    def _configurar_flujo_teclado(self):
        self._bind_combo_shortcuts(
            self.cbo_lote_1,
            {
                "a": "Bob. Ancavico",
                "v": "Bob. Ancavico",
                "t": "Bob. Transparente",
                "r": "Bob. Rejo",
                "f": "Bob. Frozzenbox",
                "m": "Bob. Martinez",
                "p": "Plastico a Granel",
            },
            next_widget=self.txt_lote_1,
            on_change=lambda valor: self._on_lote_tipo_change(1, valor),
        )
        self._bind_combo_shortcuts(
            self.cbo_lote_2,
            {
                "a": "Bob. Ancavico",
                "v": "Bob. Ancavico",
                "t": "Bob. Transparente",
                "r": "Bob. Rejo",
                "f": "Bob. Frozzenbox",
                "m": "Bob. Martinez",
                "p": "Plastico a Granel",
            },
            next_widget=self.txt_lote_2,
            on_change=lambda valor: self._on_lote_tipo_change(2, valor),
        )
        self._bind_combo_shortcuts(
            self.cbo_lote_3,
            {
                "a": "Bob. Ancavico",
                "v": "Bob. Ancavico",
                "t": "Bob. Transparente",
                "r": "Bob. Rejo",
                "f": "Bob. Frozzenbox",
                "m": "Bob. Martinez",
                "p": "Plastico a Granel",
            },
            next_widget=self.txt_lote_3,
            on_change=lambda valor: self._on_lote_tipo_change(3, valor),
        )

        flujo = [
            self.txt_lote_1,
            self.txt_lote_2,
            self.txt_lote_3,
        ]
        for fila in self.filas:
            self._bind_combo_busqueda_inicial(
                fila["marca"],
                VALORES_MARCA,
                next_widget=fila["etiqueta"],
                on_change=lambda _valor: self._igualar_ancho_combos_marca(),
            )
            flujo.extend([fila["etiqueta"], fila["cantidad"], fila["gastado"]])

        for indice, widget in enumerate(flujo):
            siguiente = flujo[indice + 1] if indice + 1 < len(flujo) else self.btn_guardar
            widget.bind("<Return>", lambda event, destino=siguiente: self._move_focus_to(destino))

        if self.btn_guardar is not None:
            self.btn_guardar.bind("<Return>", self._guardar_desde_enter)

    def _move_focus_to(self, widget):
        if widget is None:
            return "break"
        if str(widget.cget("state")) != "disabled":
            widget.focus_set()
        return "break"

    def _guardar_desde_enter(self, _event):
        self.guardar()
        return "break"

    def _bind_combo_shortcuts(self, combo, keymap, next_widget=None, on_change=None):
        objetivo = getattr(combo, "_entry", combo)

        def handler(event):
            keysym = event.keysym.lower()
            char = (event.char or "").lower()
            if keysym in ("return", "kp_enter"):
                return self._move_focus_to(next_widget)
            if keysym in ("tab", "shift_l", "shift_r", "left", "right", "up", "down", "home", "end"):
                return None
            if char in keymap:
                combo.set(keymap[char])
                if on_change:
                    on_change(combo.get())
                if next_widget is not None:
                    self.after_idle(lambda destino=next_widget: self._move_focus_to(destino))
                return "break"
            if char and char.isprintable():
                return "break"
            return None

        combo.bind("<KeyPress>", handler)
        if objetivo is not combo:
            objetivo.bind("<KeyPress>", handler)

    def _bind_combo_busqueda_inicial(self, combo, opciones, next_widget=None, on_change=None):
        objetivo = getattr(combo, "_entry", combo)

        def handler(event):
            keysym = event.keysym.lower()
            char = (event.char or "").lower()
            if keysym in ("return", "kp_enter"):
                return self._move_focus_to(next_widget)
            if keysym in ("tab", "shift_l", "shift_r", "left", "right", "up", "down", "home", "end"):
                return None
            if char and char.isalpha():
                for opcion in opciones:
                    if opcion and opcion.lower().startswith(char):
                        combo.set(opcion)
                        if on_change:
                            on_change(opcion)
                        if next_widget is not None:
                            self.after_idle(lambda: next_widget.focus_set())
                        break
                return "break"
            if char and char.isprintable():
                return "break"
            return None

        combo.bind("<KeyPress>", handler)
        if objetivo is not combo:
            objetivo.bind("<KeyPress>", handler)

    def _set_entry_text(self, entry, value):
        estado = entry.cget("state")
        if estado in ("readonly", "disabled"):
            entry.configure(state="normal")
        entry.delete(0, "end")
        entry.insert(0, value or "")
        if estado in ("readonly", "disabled"):
            entry.configure(state=estado)

    def refresh(self):
        datos = self.app.get_detalle_produccion()
        lote_bobina = datos.get("lote_bobina", [])
        pares_lote = [(self.cbo_lote_1, self.txt_lote_1), (self.cbo_lote_2, self.txt_lote_2), (self.cbo_lote_3, self.txt_lote_3)]

        for index, (combo, entry) in enumerate(pares_lote):
            tipo = lote_bobina[index * 2] if len(lote_bobina) > index * 2 else ""
            numero = lote_bobina[index * 2 + 1] if len(lote_bobina) > index * 2 + 1 else ""
            combo.set(tipo or "")
            self._set_entry_text(entry, numero)
            self._on_lote_tipo_change(index + 1, tipo)

        filas_guardadas = datos.get("filas", [])
        for index, fila_widgets in enumerate(self.filas):
            fila_data = filas_guardadas[index] if index < len(filas_guardadas) else {}
            fila_widgets["marca"].set(fila_data.get("marca", "") or "")
            self._set_entry_text(fila_widgets["etiqueta"], fila_data.get("etiqueta", ""))
            self._set_entry_text(fila_widgets["cantidad"], fila_data.get("cantidad", ""))
            self._set_entry_text(fila_widgets["gastado"], fila_data.get("gastado", ""))
            self._actualizar_resto_fila(fila_widgets)
        self._igualar_ancho_combos_marca()

    def guardar(self):
        datos = {
            "lote_bobina": [
                self.cbo_lote_1.get(), self.txt_lote_1.get(),
                self.cbo_lote_2.get(), self.txt_lote_2.get(),
                self.cbo_lote_3.get(), self.txt_lote_3.get(),
            ],
            "filas": [],
        }
        filas_resto_negativo = []
        for indice, fila in enumerate(self.filas, start=1):
            self._actualizar_resto_fila(fila)
            resto_texto = fila["resto"].get()
            try:
                if float(resto_texto.replace(",", ".") or 0) < 0:
                    filas_resto_negativo.append(indice)
            except ValueError:
                pass
            datos["filas"].append(
                {
                    "marca": fila["marca"].get(),
                    "etiqueta": fila["etiqueta"].get(),
                    "cantidad": fila["cantidad"].get(),
                    "gastado": fila["gastado"].get(),
                    "resto": resto_texto,
                }
            )

        if filas_resto_negativo:
            filas_txt = ", ".join(str(i) for i in filas_resto_negativo)
            continuar = messagebox.askyesno(
                "Resto negativo",
                f"La fila {filas_txt} tiene 'gastado' mayor que 'cantidad', lo que da un resto negativo.\n\n"
                "Quieres guardar igualmente?",
            )
            if not continuar:
                return

        self.app.app_state["detalle_produccion"] = datos
        self.app.save_current_production()
        mostrar_toast(self, "Datos guardados correctamente.", tipo="exito")
