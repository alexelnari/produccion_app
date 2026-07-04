import customtkinter as ctk
from tkinter import messagebox
from ui.admin_dialog import ask_admin_password, verificar_clave_admin
from ui.toast import mostrar_toast
from ui.icons import cargar_icono
from ui.theme import BG_APP, BG_FRAME, BG_HEADER, BG_LABEL, COLOR_BORDE, COLOR_TEXTO, COLOR_SEC, TINT_OPERACION


class VentanaBuscar(ctk.CTkFrame):
    FILTROS = {
        "Fecha": "fecha",
        "Pedido": "pedido",
        "Producto": "producto",
        "Operarios": "operarios",
    }

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG_APP)
        self.app = app
        self.resultado_frames = []
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color=BG_HEADER, corner_radius=10, height=52)
        header.grid(row=0, column=0, padx=20, pady=(18, 10), sticky="ew")
        header.grid_propagate(False)
        ctk.CTkFrame(header, fg_color=TINT_OPERACION["border"], height=4, corner_radius=0).place(
            relx=0, rely=0, relwidth=1, anchor="nw"
        )
        ctk.CTkLabel(
            header,
            text="Buscar Producciones",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#ffffff",
        ).place(relx=0.5, rely=0.5, anchor="center")

        main = ctk.CTkFrame(self, fg_color=BG_FRAME, corner_radius=12, border_width=1, border_color=COLOR_BORDE)
        main.grid(row=1, column=0, padx=20, pady=(0, 18), sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)

        filtros = ctk.CTkFrame(main, fg_color="transparent")
        filtros.grid(row=0, column=0, padx=20, pady=(18, 8), sticky="ew")
        filtros.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            filtros,
            text="Buscar por:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXTO,
        ).grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.cbo_filtro = ctk.CTkComboBox(
            filtros,
            values=list(self.FILTROS.keys()),
            width=180,
            border_color=COLOR_BORDE,
        )
        self.cbo_filtro.grid(row=0, column=1, padx=(0, 12), sticky="w")
        self.cbo_filtro.set("Fecha")

        self.txt_busqueda = ctk.CTkEntry(
            filtros,
            height=34,
            border_color=COLOR_BORDE,
            placeholder_text="Escribe aqui para buscar...",
        )
        self.txt_busqueda.grid(row=0, column=2, padx=(0, 12), sticky="ew")
        self.txt_busqueda.bind("<Return>", lambda _e: self.buscar())
        filtros.grid_columnconfigure(2, weight=1)

        ctk.CTkButton(
            filtros,
            text="BUSCAR",
            image=cargar_icono("buscar_blanco"),
            compound="left",
            width=130,
            height=36,
            corner_radius=8,
            fg_color=BG_HEADER,
            hover_color="#1a202c",
            text_color="#ffffff",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.buscar,
        ).grid(row=0, column=3, padx=(0, 8))

        ctk.CTkButton(
            filtros,
            text="VOLVER",
            image=cargar_icono("volver_gris"),
            compound="left",
            width=130,
            height=36,
            corner_radius=8,
            fg_color=BG_FRAME,
            hover_color=BG_LABEL,
            text_color=COLOR_TEXTO,
            border_width=1,
            border_color=COLOR_BORDE,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.app.show_view("inicio"),
        ).grid(row=0, column=4)

        info = ctk.CTkLabel(
            main,
            text="Busca por fecha, pedido, producto u operarios. Si dejas el campo vacio, veras las ultimas producciones guardadas.",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_SEC,
            anchor="w",
        )
        info.grid(row=1, column=0, padx=20, pady=(0, 8), sticky="ew")

        self.resultados = ctk.CTkScrollableFrame(main, fg_color="transparent")
        self.resultados.grid(row=2, column=0, padx=20, pady=(0, 16), sticky="nsew")
        self.resultados.grid_columnconfigure(0, weight=1)

        self.lbl_estado = ctk.CTkLabel(
            main,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2b6cb0",
            anchor="w",
        )
        self.lbl_estado.grid(row=3, column=0, padx=20, pady=(0, 12), sticky="ew")

    def _limpiar_resultados(self):
        for frame in self.resultado_frames:
            frame.destroy()
        self.resultado_frames.clear()

    def _render_resultado(self, resultado):
        frame = ctk.CTkFrame(self.resultados, fg_color="#fbfcfd", corner_radius=10, border_width=1, border_color=COLOR_BORDE)
        frame.grid(sticky="ew", pady=6)
        frame.grid_columnconfigure(0, weight=1)
        self.resultado_frames.append(frame)

        cabecera = f"Produccion #{resultado['id']}  |  Fecha: {resultado['fecha']}  |  Lineas: {resultado['total_lineas']}"
        ctk.CTkLabel(
            frame,
            text=cabecera,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXTO,
            anchor="w",
        ).grid(row=0, column=0, padx=14, pady=(10, 4), sticky="ew")

        detalle = f"Operarios: {resultado['operarios'] or '-'}   |   Encargado: {resultado['encargado'] or '-'}"
        ctk.CTkLabel(
            frame,
            text=detalle,
            font=ctk.CTkFont(size=12),
            text_color=COLOR_SEC,
            anchor="w",
        ).grid(row=1, column=0, padx=14, pady=(0, 10), sticky="ew")

        ctk.CTkButton(
            frame,
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
            command=lambda produccion_id=resultado['id']: self.app.ver_hoja_por_id(produccion_id, origin="buscar"),
        ).grid(row=0, column=1, rowspan=2, padx=14, pady=10)

        ctk.CTkButton(
            frame,
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
            command=lambda produccion_id=resultado['id']: self.app.cargar_produccion_como_copia(produccion_id),
        ).grid(row=0, column=2, rowspan=2, padx=(0, 14), pady=10)

        ctk.CTkButton(
            frame,
            text="BORRAR",
            image=cargar_icono("eliminar_blanco"),
            compound="left",
            width=120,
            height=34,
            corner_radius=8,
            fg_color="#e53e3e",
            hover_color="#c53030",
            text_color="#ffffff",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda item=resultado: self._borrar_produccion(item),
        ).grid(row=0, column=3, rowspan=2, padx=(0, 14), pady=10)

    def _solicitar_clave_admin(self):
        clave = ask_admin_password(self, title="Acceso protegido", prompt="Introduce la clave de administrador:")
        if clave is None:
            return False
        if not verificar_clave_admin(clave):
            messagebox.showerror("Acceso denegado", "La clave introducida no es correcta.")
            return False
        return True

    def _borrar_produccion(self, resultado):
        produccion_id = resultado["id"]
        if not self._solicitar_clave_admin():
            return

        confirmar = messagebox.askyesno(
            "Borrar produccion",
            "Se va a borrar esta produccion de forma permanente.\n\n"
            f"ID: {produccion_id}\n"
            f"Fecha: {resultado.get('fecha', '-')}\n"
            f"Lineas: {resultado.get('total_lineas', 0)}\n\n"
            "Antes de borrar se generara una copia de seguridad.\n"
            "Quieres continuar?",
        )
        if not confirmar:
            return

        try:
            backup_path = self.app.db.backup_database_now("antes_borrar_produccion")
            borrada = self.app.db.delete_production(produccion_id)
        except Exception as exc:
            messagebox.showerror("Borrar produccion", f"No se pudo borrar la produccion.\n\n{exc}")
            return
        if not borrada:
            mostrar_toast(self, "No se encontro la produccion seleccionada.", tipo="advertencia")
            self.buscar()
            return

        if self.app.current_production_id == produccion_id:
            self.app.current_production_id = None
            self.app.app_state = self.app._nuevo_estado()
            self.app.restore_last_line_on_open = False
            self.app._cargar_ultima_produccion_en_memoria()

        detalle_backup = f"\n\nCopia guardada en:\n{backup_path}" if backup_path else ""
        mostrar_toast(self, f"La produccion {produccion_id} se borro correctamente.{detalle_backup}", tipo="exito", duracion_ms=4000)
        self.buscar()

    def buscar(self):
        filtro_label = self.cbo_filtro.get()
        filtro = self.FILTROS.get(filtro_label, "fecha")
        termino = self.txt_busqueda.get().strip()
        resultados = self.app.db.search_producciones(filtro, termino)

        self._limpiar_resultados()
        if resultados:
            for resultado in resultados:
                self._render_resultado(resultado)
            self.lbl_estado.configure(text=f"Resultados encontrados: {len(resultados)}")
        else:
            self.lbl_estado.configure(text="No se encontraron producciones con ese criterio.")

    def refresh(self):
        self.buscar()
