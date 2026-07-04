import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from pathlib import Path
import copy
import sys

from db import DatabaseManager
from ui.produccion import VentanaProduccion
from ui.detalle_dia import VentanaDetalleDia
from ui.detalle_produccion import VentanaDetalleProduccion
from ui.hoja_produccion import VentanaHojaProduccion
from ui.revision_final import VentanaRevisionFinal
from ui.tolvas import VentanaTolvas
from ui.buscar import VentanaBuscar
from ui.historico import VentanaHistorico
from ui.toast import mostrar_toast
from ui.icons import cargar_icono
from ui.theme import (
    BG_APP,
    BG_FRAME,
    BG_HEADER,
    BG_SEC,
    COLOR_BORDE,
    COLOR_TEXTO,
    COLOR_SEC,
    TINT_PRODUCCION,
    TINT_OPERACION,
    TINT_GESTION,
    TINT_DANGER,
)

DIAS_SEMANA = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
NOMBRE_MAQUINA = "VERTICAL"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


def resource_path(relative_path: str) -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).resolve().parent.parent / relative_path


ICON_PATH = resource_path("assets/logovertical.ico")


class VentanaInformacionApp(ctk.CTkToplevel):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.title("Informacion de la App")
        self.geometry("640x600")
        self.resizable(False, False)
        self.configure(fg_color=BG_APP)
        self.transient(master.winfo_toplevel())
        self.grab_set()
        self._build_ui()
        self._centrar(master)

    def _centrar(self, master):
        self.update_idletasks()
        parent = master.winfo_toplevel()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (640 // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (600 // 2)
        self.geometry(f"640x600+{x}+{y}")

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main = ctk.CTkFrame(
            self,
            fg_color=BG_FRAME,
            corner_radius=0,
            border_width=1,
            border_color=COLOR_BORDE,
        )
        main.grid(row=0, column=0, padx=34, pady=(46, 20), sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(0, weight=1)

        content = ctk.CTkFrame(
            main,
            fg_color=BG_FRAME,
            corner_radius=0,
            border_width=1,
            border_color=COLOR_BORDE,
        )
        content.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)

        texto = (
            "Produccion Ancavico\n\n"
            "Version 1.0\n"
            "Desarrollado por: Alex Silva\n"
            "Aplicacion interna de gestion de produccion\n\n"
            "Esta aplicacion permite registrar y consultar la produccion\n"
            "diaria de forma clara, segura y ordenada, facilitando el\n"
            "control del trabajo realizado.\n\n"
            "Recomendaciones de uso:\n"
            "- No modificar hojas manualmente\n"
            "- Utilizar siempre los formularios\n"
            "- Cerrar el dia al finalizar la produccion"
        )

        ctk.CTkLabel(
            content,
            text=texto,
            justify="left",
            anchor="nw",
            text_color="#000000",
            font=ctk.CTkFont(size=18),
        ).grid(row=0, column=0, padx=40, pady=28, sticky="nsew")

        botones = ctk.CTkFrame(main, fg_color="transparent")
        botones.grid(row=1, column=0, padx=0, pady=(16, 0), sticky="ew")
        botones.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            botones,
            text="Volver",
            width=160,
            height=48,
            corner_radius=0,
            fg_color=BG_FRAME,
            hover_color=BG_SEC,
            text_color="#000000",
            border_width=1,
            border_color=COLOR_BORDE,
            font=ctk.CTkFont(size=20, weight="bold"),
            command=self.destroy,
        ).grid(row=0, column=0, sticky="w")


class VentanaCopiasSeguridad(ctk.CTkToplevel):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.title("Copias de Seguridad")
        self.geometry("760x560")
        self.resizable(False, False)
        self.configure(fg_color=BG_APP)
        self.transient(master.winfo_toplevel())
        self.grab_set()
        self.backups = []
        self.selected_backup = None
        self._build_ui()
        self._centrar(master)
        self.refresh()

    def _centrar(self, master):
        self.update_idletasks()
        parent = master.winfo_toplevel()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (760 // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (560 // 2)
        self.geometry(f"760x560+{x}+{y}")

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(self, fg_color=BG_HEADER, corner_radius=10, height=52)
        header.grid(row=0, column=0, padx=20, pady=(18, 10), sticky="ew")
        header.grid_propagate(False)
        ctk.CTkLabel(
            header,
            text="Copias de Seguridad",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#ffffff",
        ).place(relx=0.5, rely=0.5, anchor="center")

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")

        ctk.CTkButton(
            top,
            text="CREAR COPIA MANUAL",
            width=180,
            height=36,
            corner_radius=8,
            fg_color=BG_HEADER,
            hover_color="#1a202c",
            text_color="#ffffff",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._crear_copia_manual,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            top,
            text="ACTUALIZAR LISTA",
            width=150,
            height=36,
            corner_radius=8,
            fg_color=BG_FRAME,
            hover_color=BG_SEC,
            text_color=COLOR_TEXTO,
            border_width=1,
            border_color=COLOR_BORDE,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.refresh,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            top,
            text="CERRAR",
            width=120,
            height=36,
            corner_radius=8,
            fg_color=BG_FRAME,
            hover_color=BG_SEC,
            text_color=COLOR_TEXTO,
            border_width=1,
            border_color=COLOR_BORDE,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.destroy,
        ).pack(side="right")

        self.lbl_info = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_SEC,
            anchor="w",
            justify="left",
        )
        self.lbl_info.grid(row=2, column=0, padx=20, pady=(0, 8), sticky="ew")

        body = ctk.CTkFrame(self, fg_color=BG_FRAME, corner_radius=12, border_width=1, border_color=COLOR_BORDE)
        body.grid(row=3, column=0, padx=20, pady=(0, 18), sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self.scroll = ctk.CTkScrollableFrame(body, fg_color="transparent")
        self.scroll.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=1)

    def _crear_copia_manual(self):
        ruta = self.app.db.backup_database_now("manual")
        self.refresh()
        mostrar_toast(self, f"Copia manual creada en:\n{ruta}", tipo="exito", duracion_ms=4000)

    def _restaurar_copia(self, backup_path: Path):
        confirmar = messagebox.askyesno(
            "Restaurar copia",
            "Se va a restaurar la base de datos completa desde esta copia.\n"
            "La app guardara antes una copia de seguridad adicional.\n\n"
            f"Archivo:\n{backup_path}\n\n"
            "Quieres continuar?",
        )
        if not confirmar:
            return

        seguridad = self.app.db.restore_database_from_backup(backup_path)
        self.app._resetear_estado_actual(datetime.now().strftime("%d/%m/%Y"))
        self.app.hoja_preview_state = None
        self.app.hoja_preview_production_id = None
        self.app.hoja_preview_origin = None
        self.app._preguntar_inicio_con_ultima_produccion()
        self.app.show_view("inicio")
        self.refresh()
        messagebox.showinfo(
            "Copia restaurada",
            "La base de datos se ha restaurado correctamente.\n\n"
            f"Copia usada:\n{backup_path}\n\n"
            f"Copia de seguridad previa:\n{seguridad}",
        )

    def refresh(self):
        for widget in self.scroll.winfo_children():
            widget.destroy()

        self.backups = self.app.db.list_backups()
        self.lbl_info.configure(
            text=(
                "Desde aqui puedes crear una copia manual o restaurar una copia anterior.\n"
                "Las restauraciones afectan a toda la base de datos."
            )
        )

        if not self.backups:
            ctk.CTkLabel(
                self.scroll,
                text="Todavia no hay copias de seguridad disponibles.",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=COLOR_SEC,
                anchor="w",
            ).grid(row=0, column=0, sticky="ew")
            return

        for index, backup in enumerate(self.backups):
            card = ctk.CTkFrame(self.scroll, fg_color="#fbfcfd", corner_radius=10, border_width=1, border_color=COLOR_BORDE)
            card.grid(row=index, column=0, sticky="ew", pady=6)
            card.grid_columnconfigure(0, weight=1)

            stamp = datetime.fromtimestamp(backup.stat().st_mtime).strftime("%d/%m/%Y %H:%M:%S")
            ctk.CTkLabel(
                card,
                text=backup.name,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=COLOR_TEXTO,
                anchor="w",
            ).grid(row=0, column=0, padx=14, pady=(10, 4), sticky="ew")

            ctk.CTkLabel(
                card,
                text=f"Fecha de la copia: {stamp}",
                font=ctk.CTkFont(size=12),
                text_color=COLOR_SEC,
                anchor="w",
            ).grid(row=1, column=0, padx=14, pady=(0, 10), sticky="ew")

            ctk.CTkButton(
                card,
                text="RESTAURAR",
                width=130,
                height=34,
                corner_radius=8,
                fg_color="#dd6b20",
                hover_color="#c05621",
                text_color="#ffffff",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda path=backup: self._restaurar_copia(path),
            ).grid(row=0, column=1, rowspan=2, padx=(0, 14), pady=10)


class PantallaInicio(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main = ctk.CTkFrame(
            self,
            fg_color=BG_FRAME,
            corner_radius=14,
            border_width=1,
            border_color=COLOR_BORDE,
        )
        main.grid(row=0, column=0, padx=28, pady=28, sticky="nsew")

        for col in range(2):
            main.grid_columnconfigure(col, weight=1)
        main.grid_rowconfigure(3, weight=1)
        main.grid_rowconfigure(5, weight=1)

        header = ctk.CTkFrame(main, fg_color=BG_HEADER, corner_radius=10, height=86)
        header.grid(row=0, column=0, columnspan=2, padx=14, pady=(14, 10), sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        header.grid_rowconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=NOMBRE_MAQUINA,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#ffffff",
        ).grid(row=0, column=0, padx=(24, 10), sticky="w")

        stats = ctk.CTkFrame(header, fg_color="transparent")
        stats.grid(row=0, column=1, padx=(10, 24), sticky="e")

        self.lbl_reloj = ctk.CTkLabel(
            stats,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#cbd5e0",
            anchor="e",
            justify="right",
        )
        self.lbl_reloj.pack(anchor="e")

        self.lbl_kpis_dia = ctk.CTkLabel(
            stats,
            text="",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff",
            anchor="e",
            justify="right",
        )
        self.lbl_kpis_dia.pack(anchor="e", pady=(3, 0))

        self._actualizar_reloj()

        self.resumen_card = ctk.CTkFrame(main, fg_color=BG_SEC, corner_radius=8, height=38)
        self.resumen_card.grid(row=1, column=0, columnspan=2, padx=14, pady=(0, 10), sticky="ew")
        self.resumen_card.grid_propagate(False)
        self.lbl_resumen = ctk.CTkLabel(
            self.resumen_card,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_SEC,
            anchor="w",
        )
        self.lbl_resumen.pack(fill="both", expand=True, padx=16)

        self._section_title(main, 2, "Produccion")
        self._boton_tarjeta(
            main, 3, 0, "Nuevo dia de Produccion",
            "nuevo_dia", self.app.iniciar_nuevo_dia, TINT_PRODUCCION,
        )
        self._boton_tarjeta(
            main, 3, 1, "Abrir Produccion Existente",
            "abrir", self.app.abrir_ultima_produccion, TINT_PRODUCCION,
        )

        self._section_title(main, 4, "Operacion")
        self._boton_tarjeta(
            main, 5, 0, "Tolvas",
            "tolvas", lambda: self.app.show_view("tolvas"), TINT_OPERACION,
        )
        self._boton_tarjeta(
            main, 5, 1, "Buscar",
            "buscar", lambda: self.app.show_view("buscar"), TINT_OPERACION,
        )

        self._section_title(main, 6, "Gestion")
        self._boton_tarjeta(
            main, 7, 0, "Estadisticas / Historico",
            "historico", lambda: self.app.show_view("historico"), TINT_GESTION,
        )
        self._boton_tarjeta(
            main, 7, 1, "Informacion de la App",
            "info", self._mostrar_informacion_app, TINT_GESTION,
        )
        self._small_button(main, 8, 0, "Salir", self.app.destroy, columnspan=2, pady=(4, 22), tint=TINT_DANGER)

    def _actualizar_reloj(self):
        ahora = datetime.now()
        dia_semana = DIAS_SEMANA[ahora.weekday()]
        self.lbl_reloj.configure(text=f"{dia_semana} {ahora.strftime('%d/%m/%Y')}   {ahora.strftime('%H:%M:%S')}")
        self.after(1000, self._actualizar_reloj)

    def _actualizar_kpis_dia(self):
        fecha_hoy = datetime.now().strftime("%d/%m/%Y")
        kpis = self.app.db.get_kpis_del_dia(fecha_hoy)
        lineas = kpis.get("total_lineas", 0)
        kg = kpis.get("total_kg", 0)
        self.lbl_kpis_dia.configure(text=f"Lineas hoy: {lineas}   |   Kg hoy: {kg:.1f}")

    def _actualizar_resumen_produccion(self):
        resumen = self.app.get_current_production_summary()
        if not resumen.get("has_data"):
            texto = "Sin produccion activa en este equipo todavia."
        else:
            fecha = resumen.get("fecha") or "sin fecha"
            lineas = resumen.get("lineas", 0)
            texto = f"Ultima produccion cargada  -  Fecha: {fecha}   |   Lineas guardadas: {lineas}"
            actualizado = resumen.get("updated_at")
            if actualizado:
                texto += f"   |   Ultimo guardado: {actualizado}"
        self.lbl_resumen.configure(text=texto)

    def refresh(self):
        self._actualizar_resumen_produccion()
        self._actualizar_kpis_dia()

    def _mostrar_informacion_app(self):
        ventana = VentanaInformacionApp(self, self.app)
        ventana.focus_set()

    def _section_title(self, parent, row, text):
        bar = ctk.CTkFrame(parent, fg_color=BG_SEC, corner_radius=8, height=40)
        bar.grid(row=row, column=0, columnspan=2, padx=14, pady=(8, 6), sticky="ew")
        bar.grid_propagate(False)

        ctk.CTkLabel(
            bar,
            text=text.upper(),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_SEC,
        ).place(relx=0.02, rely=0.5, anchor="w")


    def _boton_tarjeta(self, parent, row, col, titulo, icono, command, tint, columnspan=1):
        card = ctk.CTkFrame(
            parent,
            height=64,
            corner_radius=10,
            fg_color=tint["bg"],
            border_width=1,
            border_color=tint["border"],
            cursor="hand2",
        )
        card.grid(row=row, column=col, columnspan=columnspan, padx=14, pady=(4, 10), sticky="ew")
        card.grid_propagate(False)
        card.grid_columnconfigure(1, weight=1)

        lbl_icono = ctk.CTkLabel(card, text="", image=cargar_icono(icono, tamano=30), cursor="hand2")
        lbl_icono.grid(row=0, column=0, padx=(18, 12), pady=10)

        lbl_titulo = ctk.CTkLabel(
            card,
            text=titulo,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=tint["texto"],
            anchor="w",
            justify="left",
            cursor="hand2",
        )
        lbl_titulo.grid(row=0, column=1, sticky="w", padx=(0, 16))

        def _entrar(_evento=None):
            card.configure(fg_color=tint["hover"])

        def _salir_hover(_evento=None):
            card.configure(fg_color=tint["bg"])

        def _click(_evento=None):
            command()

        for widget in (card, lbl_icono, lbl_titulo):
            widget.bind("<Button-1>", _click)
            widget.bind("<Enter>", _entrar)
            widget.bind("<Leave>", _salir_hover)

        return card

    def _small_button(self, parent, row, col, text, command, columnspan=1, pady=(4, 22), tint=None):
        tint = tint or {"bg": BG_FRAME, "hover": BG_SEC, "border": COLOR_BORDE, "texto": COLOR_SEC}
        btn = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            height=42,
            corner_radius=10,
            fg_color=tint["bg"],
            hover_color=tint["hover"],
            text_color=tint["texto"],
            border_width=1,
            border_color=tint["border"],
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        btn.grid(row=row, column=col, columnspan=columnspan, padx=14, pady=pady, sticky="ew")

    def _empty_space(self, parent, row, col):
        ctk.CTkFrame(parent, fg_color="transparent").grid(
            row=row, column=col, padx=14, pady=(4, 10), sticky="ew"
        )


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Produccion Ancavico")
        if ICON_PATH.exists():
            self.iconbitmap(str(ICON_PATH))
        self.configure(fg_color=BG_APP)

        self.db = DatabaseManager()
        self.db.init_db()
        self.db.backup_database_daily()
        self.current_production_id = None
        self.app_state = self._nuevo_estado()
        self.hoja_preview_state = None
        self.hoja_preview_production_id = None
        self.hoja_preview_origin = None
        self.restore_last_line_on_open = False
        self.active_production_mode = "nueva"
        self.active_production_source_id = None
        self.last_saved_at = ""
        self.has_unsaved_changes = False
        self.tolvas_recent_articles = []

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._centrar_ventana(1080, 700)
        self.minsize(820, 560)
        self._build_ui()
        self.after(150, self._preguntar_inicio_con_ultima_produccion)

    def _nuevo_estado(self):
        return {
            "lineas_produccion": [],
            "detalle_dia": {
                "fecha": "",
                "encargado": "",
                "operarios": "",
                "incidencias": "",
            },
            "detalle_produccion": {
                "lote_bobina": ["", "", "", "", "", ""],
                "filas": [],
            },
        }

    def _cargar_ultima_produccion_en_memoria(self):
        ultima = self.db.load_latest_production()
        if not ultima:
            return
        self.current_production_id, self.app_state = ultima

    def _resetear_estado_actual(self, fecha=None):
        self.current_production_id = None
        self.app_state = self._nuevo_estado()
        self.restore_last_line_on_open = False
        self.active_production_mode = "nueva"
        self.active_production_source_id = None
        self.last_saved_at = ""
        self.has_unsaved_changes = False
        if fecha:
            self.app_state["detalle_dia"]["fecha"] = fecha

    def _set_active_production_context(self, mode, source_id=None):
        self.active_production_mode = mode
        self.active_production_source_id = source_id

    def mark_unsaved_changes(self):
        self.has_unsaved_changes = True

    def get_active_production_context(self):
        return {
            "mode": self.active_production_mode,
            "source_id": self.active_production_source_id,
            "current_id": self.current_production_id,
            "last_saved_at": self.last_saved_at,
            "has_unsaved_changes": self.has_unsaved_changes,
        }

    def registrar_tolvas_reciente(self, codigo, descripcion=""):
        codigo = str(codigo).strip()
        descripcion = str(descripcion or "").strip()
        if not codigo:
            return

        nuevo = {"codigo": codigo, "descripcion": descripcion}
        self.tolvas_recent_articles = [
            item for item in self.tolvas_recent_articles
            if str(item.get("codigo", "")).strip() != codigo
        ]
        self.tolvas_recent_articles.insert(0, nuevo)
        self.tolvas_recent_articles = self.tolvas_recent_articles[:8]

    def get_tolvas_recientes(self):
        return list(self.tolvas_recent_articles)

    def _preguntar_inicio_con_ultima_produccion(self):
        if self.current_production_id is not None or self.get_lineas_produccion():
            return

        ultima = self.db.load_latest_production()
        if not ultima:
            self._resetear_estado_actual(datetime.now().strftime("%d/%m/%Y"))
            return

        produccion_id, estado = ultima
        fecha = estado.get("detalle_dia", {}).get("fecha", "") or "sin fecha"
        total_lineas = len(estado.get("lineas_produccion", []))
        continuar = messagebox.askyesno(
            "Continuar ultima produccion",
            "Se ha encontrado una produccion guardada.\n\n"
            f"Fecha: {fecha}\n"
            f"Lineas guardadas: {total_lineas}\n\n"
            "Si pulsas 'Si', continuas con esa produccion.\n"
            "Si pulsas 'No', la app se abre limpia para empezar una nueva.",
        )

        if continuar:
            self.current_production_id, self.app_state = produccion_id, estado
            self._set_active_production_context("continuada", produccion_id)
            self.restore_last_line_on_open = True
            self.show_view("produccion")
        else:
            self._resetear_estado_actual(datetime.now().strftime("%d/%m/%Y"))
            self.show_view("inicio")

    def _centrar_ventana(self, ancho, alto):
        self.update_idletasks()
        pw = self.winfo_screenwidth()
        ph = self.winfo_screenheight()
        margen_horizontal = 80
        margen_vertical = 100
        ancho = min(ancho, max(820, pw - margen_horizontal))
        alto = min(alto, max(560, ph - margen_vertical))
        x = (pw // 2) - (ancho // 2)
        y = (ph // 2) - (alto // 2)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=0, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self.frames = {}
        frame_classes = {
            "inicio": PantallaInicio,
            "produccion": VentanaProduccion,
            "detalle_dia": VentanaDetalleDia,
            "detalle_produccion": VentanaDetalleProduccion,
            "hoja_produccion": VentanaHojaProduccion,
            "revision_final": VentanaRevisionFinal,
            "tolvas": VentanaTolvas,
            "buscar": VentanaBuscar,
            "historico": VentanaHistorico,
        }

        for name, frame_class in frame_classes.items():
            frame = frame_class(self.container, self)
            frame.grid(row=0, column=0, sticky="nsew")
            self.frames[name] = frame

        self.show_view("inicio")

    def abrir_gestor_copias(self):
        ventana = VentanaCopiasSeguridad(self, self)
        ventana.focus_set()

    def show_view(self, name):
        if name != "hoja_produccion":
            self.hoja_preview_state = None
            self.hoja_preview_production_id = None
            self.hoja_preview_origin = None
        frame = self.frames[name]
        if hasattr(frame, "refresh"):
            frame.refresh()
        frame.tkraise()

    def get_current_production_summary(self):
        if self.current_production_id is None:
            return {
                "has_data": False,
                "id": None,
                "fecha": "",
                "lineas": 0,
                "updated_at": "",
            }

        resumen = self.db.get_production_summary(self.current_production_id)
        if resumen:
            resumen["has_data"] = True
            return resumen

        return {
            "has_data": True,
            "id": self.current_production_id,
            "fecha": self.app_state["detalle_dia"].get("fecha", ""),
            "lineas": len(self.get_lineas_produccion()),
            "updated_at": "",
        }

    def ensure_current_production(self):
        if self.current_production_id is None:
            fecha = self.app_state["detalle_dia"].get("fecha") or datetime.now().strftime("%d/%m/%Y")
            self.app_state["detalle_dia"]["fecha"] = fecha
            self.current_production_id = self.db.create_production(fecha)
        return self.current_production_id

    def save_current_production(self):
        produccion_id = self.ensure_current_production()
        try:
            self.db.save_snapshot(produccion_id, self.app_state)
        except Exception as exc:
            messagebox.showerror(
                "Error al guardar",
                "No se pudo guardar la produccion en la base de datos.\n\n"
                f"{exc}\n\n"
                "Los datos siguen en pantalla; corrige el problema e intenta guardar de nuevo.",
            )
            raise
        self.last_saved_at = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.has_unsaved_changes = False

    def _hay_produccion_activa_de_otro_dia(self, fecha_hoy):
        fecha_actual = (self.app_state.get("detalle_dia", {}).get("fecha", "") or "").strip()
        if not fecha_actual or fecha_actual == fecha_hoy:
            return False
        return self.current_production_id is not None or bool(self.get_lineas_produccion())

    def iniciar_nuevo_dia(self):
        fecha_hoy = datetime.now().strftime("%d/%m/%Y")

        if self._hay_produccion_activa_de_otro_dia(fecha_hoy):
            fecha_actual = self.app_state["detalle_dia"].get("fecha", "") or "sin fecha"
            total_lineas = len(self.get_lineas_produccion())
            continuar_actual = messagebox.askyesno(
                "Produccion de otro dia detectada",
                "La produccion activa no pertenece al dia de hoy.\n\n"
                f"Fecha activa: {fecha_actual}\n"
                f"Fecha de hoy: {fecha_hoy}\n"
                f"Lineas guardadas: {total_lineas}\n\n"
                "Si pulsas 'Si', continuas con esa produccion anterior.\n"
                "Si pulsas 'No', se crea un nuevo dia limpio para hoy.",
            )
            if continuar_actual:
                self._set_active_production_context("continuada", self.current_production_id)
                self.restore_last_line_on_open = True
                self.show_view("produccion")
                return

            self._resetear_estado_actual(fecha_hoy)

        ultima_de_hoy = self.db.load_latest_production_for_date(fecha_hoy)
        if ultima_de_hoy:
            continuar = messagebox.askyesno(
                "Produccion de hoy encontrada",
                "Ya existe una produccion guardada de hoy.\n\n"
                "Si pulsas 'Si', continuas con la ultima produccion de hoy.\n"
                "Si pulsas 'No', se crea una produccion nueva para hoy.",
            )
            if continuar:
                self.current_production_id, self.app_state = ultima_de_hoy
                self._set_active_production_context("continuada", self.current_production_id)
                self.restore_last_line_on_open = True
                self.show_view("produccion")
                return

        self.app_state = self._nuevo_estado()
        self.app_state["detalle_dia"]["fecha"] = fecha_hoy
        self.current_production_id = self.db.create_production(fecha_hoy)
        self._set_active_production_context("nueva", self.current_production_id)
        self.save_current_production()
        self.show_view("produccion")

    def abrir_ultima_produccion(self):
        ultima = self.db.load_latest_production()
        if not ultima:
            mostrar_toast(self, "Todavia no hay producciones guardadas.", tipo="info")
            return
        self.current_production_id, self.app_state = ultima
        self._set_active_production_context("abierta", self.current_production_id)
        self.show_view("produccion")

    def abrir_produccion_por_id(self, produccion_id):
        self.current_production_id = produccion_id
        self.app_state = self.db.load_production(produccion_id)
        self._set_active_production_context("abierta", produccion_id)
        self.restore_last_line_on_open = True
        self.show_view("produccion")

    def cargar_produccion_como_copia(self, produccion_id):
        estado_original = self.db.load_production(produccion_id)
        fecha_hoy = datetime.now().strftime("%d/%m/%Y")
        resumen = self.db.get_production_summary(produccion_id) or {}
        total_lineas = len(estado_original.get("lineas_produccion", []))

        confirmar = messagebox.askyesno(
            "Cargar como copia nueva",
            "Se va a cargar esta produccion como una copia nueva.\n\n"
            f"Produccion origen: #{produccion_id}\n"
            f"Fecha origen: {resumen.get('fecha', '-')}\n"
            f"Lineas origen: {total_lineas}\n\n"
            "La produccion actual se conservara y no se mezclara con la historica.\n"
            "Quieres continuar?",
        )
        if not confirmar:
            return

        if self.current_production_id is not None:
            self.save_current_production()

        nuevo_estado = copy.deepcopy(estado_original)
        nuevo_estado["detalle_dia"]["fecha"] = fecha_hoy
        self.app_state = nuevo_estado
        self.current_production_id = self.db.create_production(fecha_hoy)
        self._set_active_production_context("copia", produccion_id)
        self.save_current_production()
        self.restore_last_line_on_open = True
        self.show_view("produccion")

    def recargar_produccion_actual_desde_bd(self):
        if self.current_production_id is None:
            return False
        self.app_state = self.db.load_production(self.current_production_id)
        self.restore_last_line_on_open = True
        self.has_unsaved_changes = False
        self.show_view("produccion")
        return True

    def consume_restore_last_line_request(self):
        valor = self.restore_last_line_on_open
        self.restore_last_line_on_open = False
        return valor

    def ver_hoja_por_id(self, produccion_id, origin=None):
        self.hoja_preview_production_id = produccion_id
        self.hoja_preview_state = self.db.load_production(produccion_id)
        self.hoja_preview_origin = origin
        self.show_view("hoja_produccion")

    def get_hoja_state(self):
        return self.hoja_preview_state or self.app_state

    def is_hoja_preview(self):
        return self.hoja_preview_state is not None

    def get_lineas_produccion(self):
        return self.app_state["lineas_produccion"]

    def get_detalle_dia(self):
        return self.app_state["detalle_dia"]

    def get_detalle_produccion(self):
        return self.app_state["detalle_produccion"]

    def _on_close(self):
        guardado_ok = True
        try:
            if self.current_production_id is not None:
                self.save_current_production()
        except Exception as error:
            guardado_ok = False
            messagebox.showerror(
                "Error al guardar",
                f"No se pudo guardar la produccion actual antes de cerrar.\n\nDetalle: {error}",
            )

        if not guardado_ok:
            if not messagebox.askyesno(
                "Salir",
                "No se pudo guardar la produccion. Si cierras ahora podrias perder cambios.\n\nQuieres cerrar de todas formas?",
            ):
                return
        elif self.get_lineas_produccion():
            if not messagebox.askyesno("Salir", "Se guardara la produccion actual antes de salir. Quieres cerrar la app?"):
                return
        self.destroy()
