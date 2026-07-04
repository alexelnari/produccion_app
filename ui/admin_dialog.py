import hashlib

import customtkinter as ctk

from ui.icons import cargar_icono
from ui.theme import BG_APP, BG_FRAME, BG_HEADER, BG_LABEL, COLOR_BORDE, COLOR_TEXTO, TINT_GESTION

_CLAVE_ADMIN_HASH = "c38c70e0a2a5e78063d030f095c1db48f5dcf840b7403f15819e326cfdd00d85"


def verificar_clave_admin(clave: str) -> bool:
    return hashlib.sha256((clave or "").encode("utf-8")).hexdigest() == _CLAVE_ADMIN_HASH


class AdminPasswordDialog(ctk.CTkToplevel):
    def __init__(self, master, title="Acceso protegido", prompt="Introduce la clave de administrador:"):
        super().__init__(master)
        self.result = None
        self.title(title)
        self.geometry("540x340")
        self.resizable(False, False)
        self.configure(fg_color=BG_APP)
        self.transient(master.winfo_toplevel())
        self.grab_set()
        self._build_ui(prompt)
        self._center_over_parent(master)

    def _center_over_parent(self, master):
        self.update_idletasks()
        parent = master.winfo_toplevel()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (540 // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (340 // 2)
        self.geometry(f"540x340+{x}+{y}")

    def _build_ui(self, prompt):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color=BG_HEADER, corner_radius=10, height=62)
        header.grid(row=0, column=0, padx=20, pady=(18, 10), sticky="ew")
        header.grid_propagate(False)
        ctk.CTkFrame(header, fg_color=TINT_GESTION["border"], height=4, corner_radius=0).place(
            relx=0, rely=0, relwidth=1, anchor="nw"
        )
        ctk.CTkLabel(
            header,
            text="Acceso protegido",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#ffffff",
        ).place(relx=0.5, rely=0.5, anchor="center")

        main = ctk.CTkFrame(self, fg_color=BG_FRAME, corner_radius=12, border_width=1, border_color=COLOR_BORDE)
        main.grid(row=1, column=0, padx=20, pady=(0, 18), sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            main,
            text=prompt,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLOR_TEXTO,
            anchor="w",
            justify="left",
            wraplength=440,
        ).grid(row=0, column=0, padx=24, pady=(24, 12), sticky="ew")

        self.entry = ctk.CTkEntry(main, width=360, height=44, border_color=COLOR_BORDE, show="*")
        self.entry.grid(row=1, column=0, padx=24, pady=(0, 22), sticky="ew")
        self.entry.bind("<Return>", self._accept)
        self.entry.focus_set()

        buttons_wrap = ctk.CTkFrame(main, fg_color=BG_LABEL, corner_radius=10)
        buttons_wrap.grid(row=2, column=0, padx=24, pady=(10, 20), sticky="ew")
        buttons = ctk.CTkFrame(buttons_wrap, fg_color="transparent")
        buttons.pack(fill="x", padx=18, pady=14)
        buttons.grid_columnconfigure((0, 1), weight=1)

        accept_button = ctk.CTkButton(
            buttons,
            text="ACEPTAR",
            image=cargar_icono("aceptar_blanco"),
            compound="left",
            height=42,
            corner_radius=8,
            fg_color=BG_HEADER,
            hover_color="#1a202c",
            text_color="#ffffff",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._accept,
        )
        accept_button.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        cancel_button = ctk.CTkButton(
            buttons,
            text="CANCELAR",
            image=cargar_icono("cancelar_gris"),
            compound="left",
            height=42,
            corner_radius=8,
            fg_color=BG_FRAME,
            hover_color=BG_LABEL,
            text_color=COLOR_TEXTO,
            border_width=1,
            border_color=COLOR_BORDE,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._cancel,
        )
        cancel_button.grid(row=0, column=1, padx=(8, 0), sticky="ew")

    def _accept(self, _event=None):
        self.result = self.entry.get()
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


def ask_admin_password(master, title="Acceso protegido", prompt="Introduce la clave de administrador:"):
    dialog = AdminPasswordDialog(master, title=title, prompt=prompt)
    dialog.wait_window()
    return dialog.result
