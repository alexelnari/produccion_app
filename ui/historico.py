import customtkinter as ctk

from ui.icons import cargar_icono
from ui.theme import BG_APP, BG_FRAME, BG_HEADER, BG_LABEL, COLOR_BORDE, COLOR_TEXTO, COLOR_SEC, TINT_GESTION


class VentanaHistorico(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG_APP)
        self.app = app
        self.cards = []
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(self, fg_color=BG_HEADER, corner_radius=10, height=52)
        header.grid(row=0, column=0, padx=20, pady=(18, 10), sticky="ew")
        header.grid_propagate(False)
        ctk.CTkFrame(header, fg_color=TINT_GESTION["border"], height=4, corner_radius=0).place(
            relx=0, rely=0, relwidth=1, anchor="nw"
        )
        ctk.CTkLabel(
            header,
            text="Estadisticas / Historico",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#ffffff",
        ).place(relx=0.5, rely=0.5, anchor="center")

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        top.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.lbl_total_producciones = self._stat_card(top, 0, "Producciones")
        self.lbl_total_lineas = self._stat_card(top, 1, "Lineas")
        self.lbl_total_kg = self._stat_card(top, 2, "Kg")
        self.lbl_total_importadas = self._stat_card(top, 3, "Importadas")

        main = ctk.CTkFrame(self, fg_color=BG_FRAME, corner_radius=12, border_width=1, border_color=COLOR_BORDE)
        main.grid(row=2, column=0, padx=20, pady=(0, 18), sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)

        filtros = ctk.CTkFrame(main, fg_color="transparent")
        filtros.grid(row=0, column=0, padx=20, pady=(18, 8), sticky="ew")

        ctk.CTkLabel(filtros, text="Fecha desde:", font=ctk.CTkFont(size=13, weight="bold"), text_color=COLOR_TEXTO).pack(side="left", padx=(0, 8))
        self.txt_desde = ctk.CTkEntry(filtros, width=120, height=34, border_color=COLOR_BORDE, placeholder_text="dd/mm/aaaa")
        self.txt_desde.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(filtros, text="Fecha hasta:", font=ctk.CTkFont(size=13, weight="bold"), text_color=COLOR_TEXTO).pack(side="left", padx=(0, 8))
        self.txt_hasta = ctk.CTkEntry(filtros, width=120, height=34, border_color=COLOR_BORDE, placeholder_text="dd/mm/aaaa")
        self.txt_hasta.pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            filtros,
            text="FILTRAR",
            image=cargar_icono("filtro_blanco"),
            compound="left",
            width=120,
            height=36,
            corner_radius=8,
            fg_color=BG_HEADER,
            hover_color="#1a202c",
            text_color="#ffffff",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.refresh,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            filtros,
            text="LIMPIAR",
            image=cargar_icono("limpiar_gris"),
            compound="left",
            width=120,
            height=36,
            corner_radius=8,
            fg_color=BG_FRAME,
            hover_color=BG_LABEL,
            text_color=COLOR_TEXTO,
            border_width=1,
            border_color=COLOR_BORDE,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._limpiar_filtros,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            filtros,
            text="VOLVER",
            image=cargar_icono("volver_gris"),
            compound="left",
            width=120,
            height=36,
            corner_radius=8,
            fg_color=BG_FRAME,
            hover_color=BG_LABEL,
            text_color=COLOR_TEXTO,
            border_width=1,
            border_color=COLOR_BORDE,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.app.show_view("inicio"),
        ).pack(side="right")

        self.lbl_estado = ctk.CTkLabel(
            main,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2b6cb0",
            anchor="w",
        )
        self.lbl_estado.grid(row=1, column=0, padx=20, pady=(0, 8), sticky="ew")

        self.scroll = ctk.CTkScrollableFrame(main, fg_color="transparent")
        self.scroll.grid(row=2, column=0, padx=20, pady=(0, 16), sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=1)

    def _stat_card(self, parent, col, titulo):
        card = ctk.CTkFrame(parent, fg_color=BG_FRAME, corner_radius=12, border_width=1, border_color=COLOR_BORDE)
        card.grid(row=0, column=col, padx=6, sticky="ew")
        ctk.CTkLabel(card, text=titulo.upper(), font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_SEC).pack(anchor="w", padx=14, pady=(10, 2))
        value = ctk.CTkLabel(card, text="0", font=ctk.CTkFont(size=22, weight="bold"), text_color=COLOR_TEXTO)
        value.pack(anchor="w", padx=14, pady=(0, 10))
        return value

    def _limpiar_cards(self):
        for card in self.cards:
            card.destroy()
        self.cards.clear()

    def _limpiar_filtros(self):
        self.txt_desde.delete(0, "end")
        self.txt_hasta.delete(0, "end")
        self.refresh()

    def _render_card(self, item):
        card = ctk.CTkFrame(self.scroll, fg_color="#fbfcfd", corner_radius=10, border_width=1, border_color=COLOR_BORDE)
        card.grid(sticky="ew", pady=6)
        card.grid_columnconfigure(0, weight=1)
        self.cards.append(card)

        cabecera = f"Produccion #{item['id']}  |  Fecha: {item['fecha']}  |  Lineas: {item['total_lineas']}  |  Kg: {item['total_kg']}"
        ctk.CTkLabel(card, text=cabecera, font=ctk.CTkFont(size=13, weight="bold"), text_color=COLOR_TEXTO, anchor="w").grid(row=0, column=0, padx=14, pady=(10, 4), sticky="ew")

        detalle = f"Operarios: {item['operarios'] or '-'}   |   Orden inicial: {item['primer_pedido'] or '-'}   |   Genero inicial: {item['primer_producto'] or '-'}"
        ctk.CTkLabel(card, text=detalle, font=ctk.CTkFont(size=12), text_color=COLOR_SEC, anchor="w").grid(row=1, column=0, padx=14, pady=(0, 10), sticky="ew")

        ctk.CTkButton(
            card,
            text="VER HOJA",
            image=cargar_icono("documento_blanco"),
            compound="left",
            width=120,
            height=34,
            corner_radius=8,
            fg_color="#2b6cb0",
            hover_color="#2c5282",
            text_color="#ffffff",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda produccion_id=item['id']: self.app.ver_hoja_por_id(produccion_id, origin="historico"),
        ).grid(row=0, column=1, rowspan=2, padx=14, pady=10)

        ctk.CTkButton(
            card,
            text="CARGAR COPIA",
            image=cargar_icono("abrir_gris"),
            compound="left",
            width=120,
            height=34,
            corner_radius=8,
            fg_color=BG_FRAME,
            hover_color=BG_LABEL,
            text_color=COLOR_TEXTO,
            border_width=1,
            border_color=COLOR_BORDE,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda produccion_id=item['id']: self.app.cargar_produccion_como_copia(produccion_id),
        ).grid(row=0, column=2, rowspan=2, padx=(0, 14), pady=10)

    def refresh(self):
        resumen = self.app.db.get_historico_resumen()
        self.lbl_total_producciones.configure(text=str(resumen.get("total_producciones", 0)))
        self.lbl_total_lineas.configure(text=str(resumen.get("total_lineas", 0)))
        self.lbl_total_kg.configure(text=str(resumen.get("total_kg", 0)))
        self.lbl_total_importadas.configure(text=str(resumen.get("total_importadas", 0)))

        fecha_desde = self.txt_desde.get().strip()
        fecha_hasta = self.txt_hasta.get().strip()
        items = self.app.db.get_historico_producciones(fecha_desde, fecha_hasta)

        self._limpiar_cards()
        for item in items:
            self._render_card(item)

        self.lbl_estado.configure(text=f"Producciones mostradas: {len(items)}")
