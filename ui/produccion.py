import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

from productos import buscar_producto
from tolvas_data import buscar_tolvas
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
    COLOR_WARNING,
    COLOR_WARNING_HOVER,
    COLOR_INFO,
    COLOR_INFO_HOVER,
    TINT_PRODUCCION,
)

ANCHO_CAMPO = 110


class VentanaProduccion(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG_APP)
        self.app = app
        self._crear_variables()
        self._build_ui()
        self._configurar_enter_como_tab()
        self._aplicar_modo()

    def _crear_variables(self):
        self.txt_pedido = None
        self.cbo_tipo = None
        self.cbo_bobina = None
        self.txt_etiqueta_bobina = None
        self.txt_etiqueta_palet = None
        self.txt_caja = None
        self.txt_lote = None
        self.txt_producto = None
        self.txt_cantidad = None
        self.txt_fabricacion = None
        self.txt_peso = None
        self.txt_palets = None
        self.txt_ultima_hora = None
        self.banner_modo = None
        self.lbl_total_lineas = None
        self.lbl_modo_edicion = None
        self.lbl_guardado = None
        self.txt_resumen_lineas = None
        self.resumen_indices = []
        self.editing_index = None
        self.btn_guardar = None
        self.btn_eliminar = None
        self.btn_inicio = None
        self.btn_recuperar = None

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        header = ctk.CTkFrame(self, fg_color=BG_HEADER, corner_radius=10, height=52)
        header.grid(row=0, column=0, padx=20, pady=(18, 10), sticky="ew")
        header.grid_propagate(False)
        ctk.CTkFrame(header, fg_color=TINT_PRODUCCION["border"], height=4, corner_radius=0).place(
            relx=0, rely=0, relwidth=1, anchor="nw"
        )
        ctk.CTkLabel(
            header,
            text="Produccion - Nuevo Dia",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#ffffff",
        ).place(relx=0.5, rely=0.5, anchor="center")

        self.banner_modo = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#1f2937",
            fg_color="#d9edf7",
            corner_radius=8,
            anchor="w",
            padx=12,
        )
        self.banner_modo.grid(row=0, column=0, padx=20, pady=(78, 0), sticky="ew")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=1, column=0, padx=0, pady=(28, 0), sticky="nsew")
        scroll.grid_columnconfigure(0, weight=3)
        scroll.grid_columnconfigure(1, weight=2)
        scroll.grid_rowconfigure(1, weight=1)
        scroll.grid_rowconfigure(2, weight=1)

        form_card = ctk.CTkFrame(
            scroll,
            fg_color=BG_FRAME,
            corner_radius=10,
            border_width=1,
            border_color=COLOR_BORDE,
        )
        form_card.grid(row=1, column=0, padx=(20, 8), pady=8, sticky="nsew")
        form_card.grid_columnconfigure(1, weight=1)

        lbl_sec = ctk.CTkLabel(
            form_card,
            text="DATOS DE LINEA",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_SEC,
            fg_color=BG_LABEL,
            corner_radius=6,
            anchor="w",
            padx=10,
        )
        lbl_sec.grid(row=0, column=0, columnspan=2, padx=14, pady=(10, 6), sticky="ew", ipady=4)

        self.txt_pedido = self._entry(form_card, "Orden:", 1, width=ANCHO_CAMPO, solo_numero=True)
        self.cbo_tipo = self._combo(
            form_card, "Tipo de Etiqueta:", 2, ["PALET", "BOBINA"],
            width=ANCHO_CAMPO, minimo=ANCHO_CAMPO, command=self._on_tipo_change,
        )
        self._ancho_bobina = max(ANCHO_CAMPO, ctk.CTkFont(size=13).measure("Bob. Transparente") + 46)
        self.cbo_bobina = self._combo(
            form_card,
            "Tipo de Bobina:",
            3,
            ["Bob. Ancavico", "Bob. Transparente", "Bob. Rejo", "Bob. Frozzenbox", "Bob. Martinez"],
            width=self._ancho_bobina,
            minimo=self._ancho_bobina,
            command=self._on_bobina_change,
        )
        self.txt_etiqueta_bobina = self._entry(form_card, "Etiqueta de Bobina:", 4, width=ANCHO_CAMPO)
        self.lbl_ultima_etiqueta_bobina = self._hint_label(form_card, 4)
        self.txt_etiqueta_palet = self._entry(form_card, "Etiqueta de Palet:", 5, width=ANCHO_CAMPO)
        self.lbl_ultima_etiqueta_palet = self._hint_label(form_card, 5)
        self.txt_producto = self._entry(form_card, "Genero:", 6, width=ANCHO_CAMPO)
        self.txt_caja = self._entry(form_card, "Caja:", 7, width=ANCHO_CAMPO, solo_numero=True)
        self.lbl_ultima_caja = self._hint_label(form_card, 7)
        self.txt_lote = self._entry(form_card, "Lote:", 8, width=ANCHO_CAMPO, solo_numero=True)
        self.lbl_ultimo_lote = self._hint_label(form_card, 8)
        self.txt_cantidad = self._entry(form_card, "Cantidad de Cajas:", 9, width=ANCHO_CAMPO, solo_numero=True, permitir_decimal=True)
        self.txt_fabricacion = self._entry(form_card, "Articulo fabricado:", 10, width=240, readonly=True)
        self.txt_peso = self._entry(form_card, "Peso Calculado Kg:", 11, width=ANCHO_CAMPO, readonly=True)
        self.txt_palets = self._entry(form_card, "Palets:", 12, width=ANCHO_CAMPO, readonly=True)
        self.txt_ultima_hora = self._entry(form_card, "Ult. Hora de Fabricacion:", 13, width=ANCHO_CAMPO, readonly=True)

        right_card = ctk.CTkFrame(
            scroll,
            fg_color=BG_FRAME,
            corner_radius=10,
            border_width=1,
            border_color=COLOR_BORDE,
        )
        right_card.grid(row=1, column=1, padx=(8, 20), pady=8, sticky="nsew")
        right_card.grid_columnconfigure(0, weight=1)
        right_card.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            right_card,
            text="ACCIONES",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_SEC,
            fg_color=BG_LABEL,
            corner_radius=6,
            anchor="w",
            padx=10,
        ).grid(row=0, column=0, padx=14, pady=(10, 6), sticky="ew", ipady=4)

        actions = ctk.CTkFrame(right_card, fg_color="transparent")
        actions.grid(row=1, column=0, padx=16, pady=(4, 8), sticky="nsew")
        actions.grid_columnconfigure(0, weight=1)

        ESTILO_ACCION = {
            "fg_color": BG_APP, "hover_color": COLOR_BORDE,
            "text_color": COLOR_TEXTO, "border_color": COLOR_BORDE, "border_width": 1,
        }
        # Detalle del Dia / Detalle de Produccion no son acciones de revision,
        # son datos pendientes de completar. Mismo fondo/texto neutro que el
        # resto de botones de la lista (un tinte de color completo quedaba
        # fuera de lugar); solo un borde de acento mas grueso los diferencia.
        ESTILO_DATOS = {
            "fg_color": BG_APP, "hover_color": COLOR_BORDE,
            "text_color": COLOR_TEXTO, "border_color": COLOR_WARNING, "border_width": 2,
        }
        # Vista Previa Hoja es la unica que abre una vista de solo consulta
        # antes de imprimir: se resalta en azul para diferenciarla del resto
        # de acciones de la lista.
        ESTILO_PREVIA = {
            "fg_color": COLOR_INFO, "hover_color": COLOR_INFO_HOVER,
            "text_color": "#ffffff", "border_color": COLOR_INFO, "border_width": 1,
        }

        for txt, cmd, estilo, icono in [
            ("Detalle del Dia", lambda: self.app.show_view("detalle_dia"), ESTILO_DATOS, None),
            ("Detalle de Produccion", lambda: self.app.show_view("detalle_produccion"), ESTILO_DATOS, None),
            ("Revision Final", lambda: self.app.show_view("revision_final"), ESTILO_ACCION, None),
            ("Vista Previa Hoja", self.imprimir_hoja, ESTILO_PREVIA, None),
            ("Nueva linea similar", self.nueva_linea_similar, ESTILO_ACCION, None),
            ("Duplicar ultima", self.duplicar_ultima_linea, ESTILO_ACCION, None),
        ]:
            ctk.CTkButton(
                actions,
                text=txt,
                image=cargar_icono(icono) if icono else None,
                compound="left",
                height=56,
                corner_radius=8,
                font=ctk.CTkFont(size=13, weight="bold"),
                command=cmd,
                **estilo,
            ).grid(row=len(actions.grid_slaves(column=0)), column=0, pady=(6, 6), sticky="ew")

        status_card = ctk.CTkFrame(right_card, fg_color="#f7f9fb", corner_radius=10, border_width=1, border_color=COLOR_BORDE)
        status_card.grid(row=2, column=0, padx=16, pady=(8, 16), sticky="sew")
        status_card.grid_columnconfigure(0, weight=1)

        self.lbl_total_lineas = ctk.CTkLabel(
            status_card,
            text="Total lineas guardadas: 0",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_SEC,
            anchor="w",
        )
        self.lbl_total_lineas.grid(row=0, column=0, padx=14, pady=(14, 8), sticky="ew")

        self.lbl_modo_edicion = ctk.CTkLabel(
            status_card,
            text="Modo: nueva linea",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2b6cb0",
            anchor="w",
        )
        self.lbl_modo_edicion.grid(row=1, column=0, padx=14, pady=(0, 14), sticky="ew")

        self.lbl_guardado = ctk.CTkLabel(
            status_card,
            text="Estado: listo",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2f855a",
            anchor="w",
        )
        self.lbl_guardado.grid(row=2, column=0, padx=14, pady=(0, 8), sticky="ew")

        self.btn_recuperar = ctk.CTkButton(
            status_card,
            text="RECUPERAR ULTIMA GUARDADA",
            image=cargar_icono("recuperar_gris"),
            compound="left",
            height=34,
            corner_radius=8,
            fg_color=BG_FRAME,
            hover_color=BG_LABEL,
            text_color=COLOR_TEXTO,
            border_width=1,
            border_color=COLOR_BORDE,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.recuperar_ultima_guardada,
        )
        self.btn_recuperar.grid(row=3, column=0, padx=14, pady=(0, 14), sticky="ew")

        ctk.CTkButton(
            status_card,
            text="COPIAS DE SEGURIDAD",
            image=cargar_icono("backup_gris"),
            compound="left",
            height=34,
            corner_radius=8,
            fg_color=BG_FRAME,
            hover_color=BG_LABEL,
            text_color=COLOR_TEXTO,
            border_width=1,
            border_color=COLOR_BORDE,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.app.abrir_gestor_copias,
        ).grid(row=4, column=0, padx=14, pady=(0, 14), sticky="ew")

        resumen_card = ctk.CTkFrame(
            scroll,
            fg_color=BG_FRAME,
            corner_radius=10,
            border_width=1,
            border_color=COLOR_BORDE,
        )
        resumen_card.grid(row=2, column=0, columnspan=2, padx=20, pady=(4, 8), sticky="nsew")
        resumen_card.grid_columnconfigure(0, weight=1)
        resumen_card.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            resumen_card,
            text="ULTIMAS LINEAS GUARDADAS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_SEC,
            fg_color=BG_LABEL,
            corner_radius=6,
            anchor="w",
            padx=10,
        ).grid(row=0, column=0, padx=14, pady=(10, 6), sticky="ew", ipady=4)

        self.txt_resumen_lineas = ctk.CTkTextbox(
            resumen_card,
            height=190,
            border_width=1,
            border_color=COLOR_BORDE,
            fg_color="#fbfcfd",
            font=ctk.CTkFont(family="Consolas", size=14),
        )
        self.txt_resumen_lineas.grid(row=1, column=0, padx=14, pady=(0, 14), sticky="nsew")
        self.txt_resumen_lineas.configure(state="disabled", wrap="none")
        self.txt_resumen_lineas.bind("<Double-Button-1>", self._editar_desde_resumen)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, padx=20, pady=(4, 18), sticky="ew")
        for column in range(3):
            footer.grid_columnconfigure(column, weight=1)

        botones = [
            ("GUARDAR", BG_HEADER, BG_HEADER_HOVER, "#ffffff", "guardar", self.guardar),
            ("ELIMINAR ULTIMA", COLOR_WARNING, COLOR_WARNING_HOVER, "#ffffff", "eliminar", self.eliminar_ultima_linea),
            ("INICIO", BG_FRAME, BG_APP, COLOR_TEXTO, "volver", lambda: self.app.show_view("inicio")),
        ]
        botones_creados = []
        for index, (txt, fg, hover, tc, icono, cmd) in enumerate(botones):
            tono = "gris" if fg == BG_FRAME else "blanco"
            boton = ctk.CTkButton(
                footer,
                text=txt,
                image=cargar_icono(f"{icono}_{tono}"),
                compound="left",
                height=42,
                corner_radius=8,
                fg_color=fg,
                hover_color=hover,
                text_color=tc,
                border_width=1 if fg == BG_FRAME else 0,
                border_color=COLOR_BORDE,
                font=ctk.CTkFont(size=14, weight="bold"),
                command=cmd,
            )
            boton.grid(row=0, column=index, padx=10, sticky="ew")
            botones_creados.append(boton)
        self.btn_guardar, self.btn_eliminar, self.btn_inicio = botones_creados

    def _label(self, parent, texto, fila):
        lbl = ctk.CTkLabel(
            parent,
            text=texto,
            font=ctk.CTkFont(size=13),
            text_color=COLOR_SEC,
            width=230,
            anchor="w",
        )
        lbl.grid(row=fila, column=0, padx=(16, 6), pady=5, sticky="w")
        return lbl

    def _entry(self, parent, texto, fila, width=160, readonly=False, solo_numero=False, permitir_decimal=False):
        self._label(parent, texto, fila)
        entry = ctk.CTkEntry(
            parent,
            width=width,
            height=30,
            border_color=COLOR_BORDE,
            fg_color=COLOR_READONLY if readonly else BG_FRAME,
            font=ctk.CTkFont(size=13),
        )
        entry.grid(row=fila, column=1, padx=(0, 16), pady=5, sticky="w")
        if readonly:
            entry.configure(state="disabled")
        elif solo_numero:
            self._configurar_validacion_numerica(entry, permitir_decimal)
        return entry

    def _hint_label(self, parent, fila):
        lbl = ctk.CTkLabel(
            parent,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_SEC,
            anchor="w",
        )
        lbl.grid(row=fila, column=2, padx=(0, 16), pady=5, sticky="w")
        return lbl

    def _es_numero_valido(self, texto, permitir_decimal):
        if texto == "":
            return True
        if permitir_decimal:
            candidato = texto.replace(",", ".", 1)
            if candidato.count(".") > 1:
                return False
            return candidato.replace(".", "", 1).isdigit()
        return texto.isdigit()

    def _configurar_validacion_numerica(self, entry, permitir_decimal):
        def validar(texto_propuesto):
            valido = self._es_numero_valido(texto_propuesto, permitir_decimal)
            if not valido:
                self.bell()
            return valido

        vcmd = (self.register(validar), "%P")
        entry.configure(validate="key", validatecommand=vcmd)

    def _set_texto_forzado(self, entry, value):
        validacion_previa = entry.cget("validate")
        if validacion_previa != "none":
            entry.configure(validate="none")
        entry.delete(0, "end")
        entry.insert(0, str(value))
        if validacion_previa != "none":
            entry.configure(validate=validacion_previa)

    def _medir_ancho_combo(self, combo, texto, minimo, maximo):
        fuente = combo.cget("font")
        ancho_texto = fuente.measure(texto) if texto else 0
        return max(minimo, min(maximo, ancho_texto + 46))

    def _ajustar_ancho_combo(self, combo, minimo, maximo):
        combo.configure(width=self._medir_ancho_combo(combo, combo.get(), minimo, maximo))

    def _combo(self, parent, texto, fila, valores, width=200, command=None, minimo=90):
        self._label(parent, texto, fila)
        kwargs = dict(values=valores, width=width, border_color=COLOR_BORDE, font=ctk.CTkFont(size=13))
        if command:
            kwargs["command"] = command
        combo = ctk.CTkComboBox(parent, **kwargs)
        combo.grid(row=fila, column=1, padx=(0, 16), pady=5, sticky="w")
        combo.set(valores[0])
        self._ajustar_ancho_combo(combo, minimo, width)
        return combo

    def _set_enabled(self, widget, enabled=True):
        widget.configure(state="normal" if enabled else "disabled")

    def _focus_next_widget(self, event):
        siguiente = event.widget.tk_focusNext()
        while siguiente is not None and str(siguiente.cget("state")) == "disabled":
            siguiente = siguiente.tk_focusNext()
        if siguiente is not None:
            siguiente.focus_set()
        return "break"

    def _configurar_enter_como_tab(self):
        self._bind_combo_shortcuts(
            self.cbo_tipo,
            {"p": "PALET", "b": "BOBINA"},
            next_widget=self._siguiente_widget_tipo,
            on_change=self._on_tipo_change,
        )
        self._bind_combo_shortcuts(
            self.cbo_bobina,
            {
                "a": "Bob. Ancavico",
                "v": "Bob. Ancavico",
                "t": "Bob. Transparente",
                "r": "Bob. Rejo",
                "f": "Bob. Frozzenbox",
                "m": "Bob. Martinez",
            },
            next_widget=self.txt_etiqueta_bobina,
            on_change=self._on_bobina_change,
        )
        widgets = [
            self.txt_pedido,
            self.txt_etiqueta_bobina,
            self.txt_etiqueta_palet,
            self.txt_caja,
            self.txt_lote,
            self.txt_producto,
        ]
        for widget in widgets:
            widget.bind("<Return>", self._focus_next_widget)
        self.txt_producto.bind("<KeyRelease>", self._actualizar_preview_producto)
        self.txt_producto.bind("<FocusOut>", self._actualizar_preview_producto)
        # FocusOut cubre tanto Tab (mueve el foco de forma nativa) como Enter
        # (el binding de arriba mueve el foco con focus_set(), lo que dispara
        # FocusOut igual que Tab), asi que no hace falta un binding aparte
        # para cada tecla.
        self.txt_producto.bind("<FocusOut>", self._autocompletar_caja_lote_desde_historial, add="+")
        self.txt_cantidad.bind("<KeyRelease>", self._actualizar_preview_producto)
        self.txt_cantidad.bind("<FocusOut>", self._actualizar_preview_producto)
        self.txt_cantidad.bind("<Return>", self._guardar_desde_enter)
        self._registrar_widgets_con_cambios()

    def _registrar_widgets_con_cambios(self):
        widgets = [
            self.txt_pedido,
            self.txt_etiqueta_bobina,
            self.txt_etiqueta_palet,
            self.txt_caja,
            self.txt_lote,
            self.txt_producto,
            self.txt_cantidad,
        ]
        for widget in widgets:
            widget.bind("<KeyRelease>", self._marcar_cambios_pendientes, add="+")

        self.cbo_tipo.bind("<<ComboboxSelected>>", self._marcar_cambios_pendientes, add="+")
        self.cbo_bobina.bind("<<ComboboxSelected>>", self._marcar_cambios_pendientes, add="+")

    def _marcar_cambios_pendientes(self, _event=None):
        self.app.mark_unsaved_changes()
        self._actualizar_estado_guardado()

    def _move_focus_to(self, widget):
        if callable(widget):
            widget = widget()
        if widget is None:
            return "break"
        if str(widget.cget("state")) != "disabled":
            widget.focus_set()
        return "break"

    def _siguiente_widget_tipo(self):
        if self.cbo_tipo.get().strip().upper() == "BOBINA":
            return self.cbo_bobina
        return self.txt_etiqueta_palet

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

    def _set_entry_value(self, entry, value):
        entry.configure(state="normal")
        entry.delete(0, "end")
        entry.insert(0, str(value))
        entry.configure(state="disabled")

    def _on_tipo_change(self, _value):
        self._marcar_cambios_pendientes()
        self._ajustar_ancho_combo(self.cbo_tipo, ANCHO_CAMPO, ANCHO_CAMPO)
        self._aplicar_modo()

    def _on_bobina_change(self, _value=None):
        self._marcar_cambios_pendientes()
        self._ajustar_ancho_combo(self.cbo_bobina, self._ancho_bobina, self._ancho_bobina)

    def _aplicar_modo(self):
        tipo = self.cbo_tipo.get()
        es_bobina = tipo == "BOBINA"

        self._set_enabled(self.cbo_bobina, es_bobina)
        self._set_enabled(self.txt_etiqueta_bobina, es_bobina)
        self._set_enabled(self.txt_etiqueta_palet, not es_bobina)
        self._set_enabled(self.txt_caja, not es_bobina)
        self._set_enabled(self.txt_lote, not es_bobina)
        self._set_enabled(self.txt_producto, not es_bobina)
        self._actualizar_preview_producto()

    def _safe_float(self, value):
        try:
            return float(str(value).replace(",", ".") or 0)
        except ValueError:
            return 0.0

    def _obtener_info_genero(self, codigo):
        codigo = str(codigo).strip()
        if not codigo:
            return {"encontrado": False, "descripcion": "", "factor": 0.0}

        producto_info = buscar_producto(codigo) or {}
        composicion_info = buscar_tolvas(codigo) or {}
        descripcion = str(
            composicion_info.get("descripcion")
            or producto_info.get("descripcion")
            or ""
        ).strip()

        factor = 0.0
        for valor in (
            composicion_info.get("kilos_caja", ""),
            composicion_info.get("pesos", ""),
            producto_info.get("factor", 0),
        ):
            try:
                factor = float(str(valor).replace(",", ".") or 0)
            except ValueError:
                factor = 0.0
            if factor > 0:
                break

        return {
            "encontrado": bool(producto_info or composicion_info),
            "descripcion": descripcion,
            "factor": factor,
            "kilos_caja": composicion_info.get("kilos_caja", ""),
        }

    def _actualizar_preview_producto(self, _event=None):
        if self.cbo_tipo.get().strip().upper() != "PALET":
            self._set_entry_value(self.txt_fabricacion, "")
            self._set_entry_value(self.txt_peso, "")
            return

        info = self._obtener_info_genero(self.txt_producto.get().strip())
        self._set_entry_value(self.txt_fabricacion, info.get("descripcion", ""))

        cantidad_txt = self.txt_cantidad.get().strip()
        try:
            cantidad = float(cantidad_txt.replace(",", ".")) if cantidad_txt else 0
        except ValueError:
            cantidad = 0

        peso = round(cantidad * info.get("factor", 0), 2) if cantidad > 0 and info.get("factor", 0) > 0 else ""
        self._set_entry_value(self.txt_peso, peso)

    def _autocompletar_caja_lote_desde_historial(self, _event=None):
        """Al confirmar el codigo de Genero (Enter o Tab), busca en el
        historial de producciones guardadas la ultima Caja y Lote usados
        para ese codigo y los rellena, sin pisar valores que el usuario ya
        haya escrito a mano en esos campos.
        """
        codigo = self.txt_producto.get().strip()
        if not codigo:
            self.lbl_ultima_caja.configure(text="")
            self.lbl_ultimo_lote.configure(text="")
            return

        ultimos = self.app.db.get_ultimos_caja_lote_por_producto(codigo)
        ultima_caja = ultimos.get("caja", "")
        ultimo_lote = ultimos.get("lote", "")

        self.lbl_ultima_caja.configure(text=f"Ultima usada: {ultima_caja}" if ultima_caja else "")
        self.lbl_ultimo_lote.configure(text=f"Ultimo usado: {ultimo_lote}" if ultimo_lote else "")

        cambios = False
        if ultima_caja and not self.txt_caja.get().strip():
            self._set_texto_forzado(self.txt_caja, ultima_caja)
            cambios = True
        if ultimo_lote and not self.txt_lote.get().strip():
            self._set_texto_forzado(self.txt_lote, ultimo_lote)
            cambios = True
        if cambios:
            self._marcar_cambios_pendientes()

    def _actualizar_resumen(self):
        total = len(self.app.get_lineas_produccion())
        self.lbl_total_lineas.configure(text=f"Total lineas guardadas: {total}")
        texto_modo = "Modo: nueva linea" if self.editing_index is None else f"Modo: editando linea {self.editing_index + 1}"
        self.lbl_modo_edicion.configure(text=texto_modo)
        self._actualizar_estado_guardado()
        self._actualizar_banner_modo()
        self._actualizar_resumen_lineas()
        self._actualizar_ultimas_etiquetas()

    def _actualizar_ultimas_etiquetas(self):
        ultima_bobina = self.app.db.get_latest_etiqueta_por_tipo("BOBINA")
        ultima_palet = self.app.db.get_latest_etiqueta_por_tipo("PALET")
        self.lbl_ultima_etiqueta_bobina.configure(
            text=f"Ultima usada: {ultima_bobina}" if ultima_bobina else ""
        )
        self.lbl_ultima_etiqueta_palet.configure(
            text=f"Ultima usada: {ultima_palet}" if ultima_palet else ""
        )

    def _actualizar_banner_modo(self):
        contexto = self.app.get_active_production_context()
        modo = contexto.get("mode", "nueva")
        source_id = contexto.get("source_id")
        textos = {
            "nueva": "MODO PRODUCCION ACTIVA: nuevo dia en curso",
            "continuada": "MODO PRODUCCION ACTIVA: continuando produccion guardada",
            "abierta": "MODO PRODUCCION ACTIVA: produccion abierta desde historial",
            "copia": f"MODO PRODUCCION ACTIVA: copia nueva basada en produccion #{source_id}" if source_id else "MODO PRODUCCION ACTIVA: copia nueva",
        }
        colores = {
            "nueva": "#d9edf7",
            "continuada": "#feebc8",
            "abierta": "#e9d8fd",
            "copia": "#c6f6d5",
        }
        self.banner_modo.configure(
            text=textos.get(modo, "MODO PRODUCCION ACTIVA"),
            fg_color=colores.get(modo, "#d9edf7"),
        )

    def _actualizar_estado_guardado(self):
        contexto = self.app.get_active_production_context()
        if contexto.get("has_unsaved_changes"):
            self.lbl_guardado.configure(text="Estado: cambios pendientes de guardar", text_color="#c05621")
        elif contexto.get("last_saved_at"):
            self.lbl_guardado.configure(text=f"Guardado: {contexto['last_saved_at']}", text_color="#2f855a")
        else:
            self.lbl_guardado.configure(text="Estado: aun sin guardado", text_color=COLOR_SEC)

    def _actualizar_resumen_lineas(self):
        todas = self.app.get_lineas_produccion()
        inicio = max(0, len(todas) - 8)
        lineas = todas[inicio:]
        encabezado = (
            f"{'N':^4} {'ORDEN':^10} {'TIPO':^8} {'ETIQUETA':^14} "
            f"{'HORA':^7} {'DIF':^8} {'GENERO / BOBINA':<28} {'CANT':^8} {'KG':^10}"
        )
        separador = "-" * len(encabezado)
        filas = [encabezado, separador]
        self.resumen_indices = []

        if not lineas:
            filas.append("Aun no hay lineas guardadas.")
        else:
            for indice_real, linea in enumerate(lineas, start=inicio):
                producto_o_bobina = linea.get("producto") or linea.get("observaciones") or linea.get("bobina") or ""
                hora = str(linea.get("ultima_hora", "") or "")
                diferencia = self._diferencia_con_linea_anterior(todas, indice_real)
                self.resumen_indices.append(indice_real)
                filas.append(
                    f"{str(indice_real + 1):^4} "
                    f"{str(linea.get('pedido', ''))[:10]:^10} "
                    f"{str(linea.get('tipo', ''))[:8]:^8} "
                    f"{str(linea.get('etiqueta', ''))[:14]:^14} "
                    f"{hora[:7]:^7} "
                    f"{diferencia:^8} "
                    f"{str(producto_o_bobina)[:28]:<28} "
                    f"{str(linea.get('cantidad', ''))[:8]:^8} "
                    f"{str(linea.get('peso', ''))[:10]:^10}"
                )

        self.txt_resumen_lineas.configure(state="normal")
        self.txt_resumen_lineas.delete("1.0", "end")
        self.txt_resumen_lineas.insert("1.0", "\n".join(filas))
        self.txt_resumen_lineas.configure(state="disabled")

    def _diferencia_con_linea_anterior(self, lineas, indice):
        if indice <= 0 or indice >= len(lineas):
            return "-"
        hora_actual = self._hora_a_minutos(lineas[indice].get("ultima_hora", ""))
        hora_anterior = self._hora_a_minutos(lineas[indice - 1].get("ultima_hora", ""))
        if hora_actual is None or hora_anterior is None:
            return "-"
        diferencia = hora_actual - hora_anterior
        if diferencia < 0:
            diferencia += 24 * 60
        if diferencia < 60:
            return f"{diferencia}m"
        horas = diferencia // 60
        minutos = diferencia % 60
        return f"{horas}h{minutos:02d}"

    def _hora_a_minutos(self, value):
        partes = str(value or "").strip().split(":")
        if len(partes) != 2:
            return None
        try:
            horas = int(partes[0])
            minutos = int(partes[1])
        except ValueError:
            return None
        if not (0 <= horas <= 23 and 0 <= minutos <= 59):
            return None
        return horas * 60 + minutos

    def _cargar_linea_en_formulario(self, indice):
        lineas = self.app.get_lineas_produccion()
        if indice < 0 or indice >= len(lineas):
            return

        linea = lineas[indice]
        self.editing_index = indice
        self._aplicar_linea_al_formulario(linea)
        self._actualizar_resumen()
        self._actualizar_preview_producto()
        self.txt_cantidad.focus_set()

    def _aplicar_linea_al_formulario(self, linea, mantener_edicion=True, limpiar_metricas=False):
        if not mantener_edicion:
            self.editing_index = None
        self._set_texto_forzado(self.txt_pedido, linea.get("pedido", ""))
        self.cbo_tipo.set(linea.get("tipo", "PALET") or "PALET")
        self._ajustar_ancho_combo(self.cbo_tipo, ANCHO_CAMPO, ANCHO_CAMPO)
        self._aplicar_modo()
        self.cbo_bobina.set(linea.get("bobina", "Bob. Ancavico") or "Bob. Ancavico")
        self._ajustar_ancho_combo(self.cbo_bobina, self._ancho_bobina, self._ancho_bobina)
        self.txt_etiqueta_bobina.delete(0, "end")
        self.txt_etiqueta_bobina.insert(0, linea.get("etiqueta", "") if linea.get("tipo") == "BOBINA" else "")
        self.txt_etiqueta_palet.delete(0, "end")
        self.txt_etiqueta_palet.insert(0, linea.get("etiqueta", "") if linea.get("tipo") == "PALET" else "")
        self._set_texto_forzado(self.txt_caja, linea.get("caja", ""))
        self._set_texto_forzado(self.txt_lote, linea.get("lote", ""))
        self.txt_producto.delete(0, "end")
        self.txt_producto.insert(0, linea.get("producto", ""))
        self._set_texto_forzado(self.txt_cantidad, linea.get("cantidad", ""))
        if limpiar_metricas:
            self._set_entry_value(self.txt_fabricacion, "")
            self._set_entry_value(self.txt_peso, "")
            self._set_entry_value(self.txt_palets, "")
            self._set_entry_value(self.txt_ultima_hora, "")
        else:
            self._set_entry_value(self.txt_fabricacion, linea.get("fabricacion", ""))
            self._set_entry_value(self.txt_peso, linea.get("peso", ""))
            self._set_entry_value(self.txt_palets, linea.get("palets", ""))
            self._set_entry_value(self.txt_ultima_hora, linea.get("ultima_hora", ""))

    def _editar_desde_resumen(self, event):
        indice_texto = self.txt_resumen_lineas.index(f"@{event.x},{event.y}")
        numero_linea = int(indice_texto.split(".")[0])
        posicion_resumen = numero_linea - 3
        if 0 <= posicion_resumen < len(self.resumen_indices):
            self._cargar_linea_en_formulario(self.resumen_indices[posicion_resumen])

    def eliminar_ultima_linea(self):
        lineas = self.app.get_lineas_produccion()
        if not lineas:
            mostrar_toast(self, "No hay lineas para eliminar.", tipo="advertencia")
            return

        lineas.pop()
        if self.editing_index is not None and self.editing_index >= len(lineas):
            self.editing_index = None
        self.app.mark_unsaved_changes()
        self.app.save_current_production()
        self._actualizar_resumen()
        mostrar_toast(self, "Se elimino la ultima linea guardada.", tipo="exito")

    def nueva_linea_similar(self):
        lineas = self.app.get_lineas_produccion()
        if not lineas:
            mostrar_toast(self, "Todavia no hay lineas guardadas para reutilizar.", tipo="advertencia")
            return
        self._aplicar_linea_al_formulario(lineas[-1], mantener_edicion=False, limpiar_metricas=True)
        self._actualizar_preview_producto()
        self.lbl_modo_edicion.configure(text="Modo: nueva linea similar")
        self.app.mark_unsaved_changes()
        self._actualizar_estado_guardado()
        objetivo = self.txt_etiqueta_palet if self.cbo_tipo.get().strip().upper() == "PALET" else self.txt_etiqueta_bobina
        self._move_focus_to(objetivo)

    def duplicar_ultima_linea(self):
        lineas = self.app.get_lineas_produccion()
        if not lineas:
            mostrar_toast(self, "Todavia no hay lineas guardadas para duplicar.", tipo="advertencia")
            return
        nueva = dict(lineas[-1])
        nueva["ultima_hora"] = datetime.now().strftime("%H:%M")
        if str(nueva.get("tipo", "")).strip().upper() == "PALET":
            palets_actuales = sum(1 for linea in lineas if self._safe_float(linea.get("peso", 0)) > 0)
            if self._safe_float(nueva.get("peso", 0)) > 0:
                nueva["palets"] = palets_actuales + 1
            else:
                nueva["palets"] = palets_actuales
        lineas.append(nueva)
        self.app.mark_unsaved_changes()
        self.app.save_current_production()
        self._actualizar_resumen()
        mostrar_toast(self, f"Se duplico la ultima linea. Total lineas: {len(lineas)}", tipo="exito")

    def recuperar_ultima_guardada(self):
        if self.app.current_production_id is None:
            mostrar_toast(self, "Todavia no hay una produccion activa guardada para recuperar.", tipo="advertencia")
            return
        confirmar = messagebox.askyesno(
            "Recuperar ultima guardada",
            "Se recargara la produccion desde la base de datos.\n"
            "Los cambios pendientes que no se hayan guardado se perderan.\n\n"
            "Quieres continuar?",
        )
        if not confirmar:
            return
        if self.app.recargar_produccion_actual_desde_bd():
            self._actualizar_resumen()
            mostrar_toast(self, "Se recupero la ultima version guardada correctamente.", tipo="exito")

    def refresh(self):
        self._aplicar_modo()
        self._actualizar_resumen()
        if self.app.consume_restore_last_line_request() and self.app.get_lineas_produccion():
            self._cargar_linea_en_formulario(len(self.app.get_lineas_produccion()) - 1)
            self.editing_index = None
            self.lbl_modo_edicion.configure(text="Modo: continuando produccion")

    def guardar(self):
        tipo = self.cbo_tipo.get().strip().upper()
        producto_codigo = self.txt_producto.get().strip()
        cantidad_txt = self.txt_cantidad.get().strip()
        info_genero = self._obtener_info_genero(producto_codigo) if producto_codigo else {
            "encontrado": False,
            "descripcion": "",
            "factor": 0.0,
        }

        if not cantidad_txt:
            mostrar_toast(self, "Debes rellenar la cantidad antes de guardar.", tipo="advertencia")
            self.txt_cantidad.focus_set()
            return

        try:
            cantidad_num = float(cantidad_txt.replace(",", ".")) if cantidad_txt else 0
        except ValueError:
            mostrar_toast(self, "La cantidad debe ser numerica.", tipo="advertencia")
            self.txt_cantidad.focus_set()
            return

        descripcion = ""
        factor = 0
        peso_calculado = 0
        fabricacion = ""

        if tipo == "PALET":
            if producto_codigo and not info_genero.get("encontrado"):
                mostrar_toast(self, f"No se encontro el codigo de producto: {producto_codigo}", tipo="advertencia")
                return
            if info_genero.get("encontrado"):
                descripcion = str(info_genero.get("descripcion", "")).strip()
                factor = float(info_genero.get("factor", 0) or 0)
                peso_calculado = round(cantidad_num * factor, 2)
            fabricacion = descripcion
            etiqueta = self.txt_etiqueta_palet.get().strip()
            observaciones = descripcion
        else:
            etiqueta = self.txt_etiqueta_bobina.get().strip()
            observaciones = self.cbo_bobina.get().strip()

        ahora = datetime.now()
        ultima_hora = ahora.strftime("%H:%M")
        palets_calculados = sum(
            1
            for indice, linea in enumerate(self.app.get_lineas_produccion())
            if indice != self.editing_index and self._safe_float(linea.get("peso", 0)) > 0
        )
        if peso_calculado > 0:
            palets_calculados += 1

        nueva_linea = {
            "pedido": self.txt_pedido.get().strip(),
            "tipo": tipo,
            "bobina": self.cbo_bobina.get().strip(),
            "etiqueta": etiqueta,
            "caja": self.txt_caja.get().strip(),
            "lote": self.txt_lote.get().strip(),
            "producto": producto_codigo,
            "observaciones": observaciones,
            "cantidad": self.txt_cantidad.get().strip(),
            "peso": peso_calculado,
            "palets": palets_calculados,
            "fabricacion": fabricacion,
            "ultima_hora": ultima_hora,
            "factor_producto": factor,
        }

        if self.editing_index is None:
            self.app.get_lineas_produccion().append(nueva_linea)
        else:
            self.app.get_lineas_produccion()[self.editing_index] = nueva_linea
            self.editing_index = None

        if tipo == "PALET":
            self._set_entry_value(self.txt_peso, peso_calculado)
            self._set_entry_value(self.txt_fabricacion, fabricacion)
        else:
            self._set_entry_value(self.txt_peso, "")
            self._set_entry_value(self.txt_fabricacion, "")

        self._set_entry_value(self.txt_ultima_hora, ultima_hora)
        self._set_entry_value(self.txt_palets, palets_calculados)

        self.txt_cantidad.delete(0, "end")
        if tipo == "BOBINA":
            self.txt_etiqueta_bobina.delete(0, "end")
        self.txt_pedido.focus_set()

        self.app.mark_unsaved_changes()
        self.app.save_current_production()
        self._actualizar_resumen()
        mostrar_toast(self, f"Linea guardada correctamente. Total lineas: {len(self.app.get_lineas_produccion())}", tipo="exito")

    def imprimir_hoja(self):
        if not self.app.get_lineas_produccion():
            mostrar_toast(self, "Primero debes guardar al menos una linea.", tipo="advertencia")
            return
        self.app.show_view("hoja_produccion")
