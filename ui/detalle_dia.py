import customtkinter as ctk
from datetime import datetime

from ui.toast import mostrar_toast
from ui.icons import cargar_icono
from ui.theme import BG_APP, BG_FRAME, BG_HEADER, BG_LABEL, COLOR_BORDE, COLOR_TEXTO, COLOR_SEC, TINT_PRODUCCION


class VentanaDetalleDia(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG_APP)
        self.app = app
        self._build_ui()

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
            text="Detalles del Dia",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#ffffff",
        ).place(relx=0.5, rely=0.5, anchor="center")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=1, column=0, padx=0, pady=(0, 0), sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        body = ctk.CTkFrame(scroll, fg_color="transparent")
        body.grid(row=1, column=0, padx=20, pady=(0, 12), sticky="nsew")
        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=3)
        body.grid_rowconfigure(0, weight=1)

        card_info = ctk.CTkFrame(
            body,
            fg_color=BG_FRAME,
            corner_radius=10,
            border_width=1,
            border_color=COLOR_BORDE,
        )
        card_info.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        card_info.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card_info,
            text="RESPONSABLES",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_SEC,
            fg_color=BG_LABEL,
            corner_radius=6,
            anchor="w",
            padx=10,
        ).grid(row=0, column=0, padx=14, pady=(10, 6), sticky="ew", ipady=4)

        form = ctk.CTkFrame(card_info, fg_color="transparent")
        form.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="ew")
        form.grid_columnconfigure(1, weight=1)

        self.txt_fecha = self._build_row(form, "Fecha:", 0)
        self.txt_operarios = self._build_row(form, "Operarios:", 1)
        self.txt_encargado = self._build_row(form, "Jefe de Maquina:", 2)

        ctk.CTkLabel(
            card_info,
            text="NOTA",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_SEC,
            fg_color=BG_LABEL,
            corner_radius=6,
            anchor="w",
            padx=10,
        ).grid(row=2, column=0, padx=14, pady=(4, 6), sticky="ew", ipady=4)

        ctk.CTkLabel(
            card_info,
            text="Usa esta pantalla para dejar reflejado quien estuvo en linea y cualquier incidencia del turno.",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_SEC,
            justify="left",
            anchor="nw",
            wraplength=300,
        ).grid(row=3, column=0, padx=16, pady=(0, 16), sticky="ew")

        card_incidencias = ctk.CTkFrame(
            body,
            fg_color=BG_FRAME,
            corner_radius=10,
            border_width=1,
            border_color=COLOR_BORDE,
        )
        card_incidencias.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        card_incidencias.grid_columnconfigure(0, weight=1)
        card_incidencias.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            card_incidencias,
            text="INCIDENCIAS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_SEC,
            fg_color=BG_LABEL,
            corner_radius=6,
            anchor="w",
            padx=10,
        ).grid(row=0, column=0, padx=14, pady=(10, 6), sticky="ew", ipady=4)

        self.txt_incidencias = ctk.CTkTextbox(
            card_incidencias,
            height=240,
            border_width=1,
            border_color=COLOR_BORDE,
            font=ctk.CTkFont(size=13),
        )
        self.txt_incidencias.grid(row=1, column=0, padx=14, pady=(0, 14), sticky="nsew")

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, padx=20, pady=(0, 18), sticky="e")

        ctk.CTkButton(
            footer,
            text="GUARDAR",
            image=cargar_icono("guardar_blanco"),
            compound="left",
            width=160,
            height=46,
            corner_radius=8,
            fg_color=BG_HEADER,
            hover_color="#1a202c",
            text_color="#ffffff",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.guardar,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            footer,
            text="VOLVER",
            image=cargar_icono("volver_gris"),
            compound="left",
            width=160,
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

    def _build_row(self, parent, label, row):
        ctk.CTkLabel(
            parent,
            text=label,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXTO,
            width=130,
            anchor="w",
        ).grid(row=row, column=0, pady=5, sticky="w")

        entry = ctk.CTkEntry(parent, height=32, border_color=COLOR_BORDE)
        entry.grid(row=row, column=1, pady=5, padx=(8, 0), sticky="ew")
        return entry

    def refresh(self):
        datos = self.app.get_detalle_dia()
        if not datos.get("fecha"):
            datos["fecha"] = datetime.now().strftime("%d/%m/%Y")
        self._set_entry(self.txt_fecha, datos.get("fecha", ""))
        self._set_entry(self.txt_operarios, datos.get("operarios", ""))
        self._set_entry(self.txt_encargado, datos.get("encargado", ""))
        self.txt_incidencias.delete("1.0", "end")
        self.txt_incidencias.insert("1.0", datos.get("incidencias", ""))

    def _set_entry(self, entry, value):
        entry.delete(0, "end")
        entry.insert(0, value)

    def guardar(self):
        detalle = self.app.get_detalle_dia()
        detalle.update(
            {
                "fecha": self.txt_fecha.get().strip(),
                "operarios": self.txt_operarios.get().strip(),
                "encargado": self.txt_encargado.get().strip(),
                "incidencias": self.txt_incidencias.get("1.0", "end").strip(),
            }
        )
        self.app.save_current_production()
        mostrar_toast(self, "Datos guardados correctamente.", tipo="exito")
