"""Notificaciones tipo "toast": un aviso que aparece y se cierra solo.

Sustituye a los messagebox nativos de Windows para confirmaciones de
rutina (guardar, duplicar, avisos de validacion...). Esas acciones se
repiten muchas veces por turno de trabajo y antes exigian un clic en
"Aceptar" en un dialogo que ademas rompia la estetica de la app (fuente y
colores del sistema operativo en vez de los de customtkinter).

Los dialogos que exigen una decision real del usuario (askyesno) o que
avisan de un error (showerror) siguen usando messagebox: ahi si conviene
que el usuario tenga que detenerse y confirmar.
"""

import customtkinter as ctk

from ui.theme import BG_FRAME, TOAST_TINTS

_toast_activo_por_raiz = {}


def mostrar_toast(widget, mensaje, tipo="info", duracion_ms=1800):
    raiz = widget.winfo_toplevel()

    anterior = _toast_activo_por_raiz.get(raiz)
    if anterior is not None and anterior.winfo_exists():
        anterior.destroy()

    tint = TOAST_TINTS.get(tipo, TOAST_TINTS["info"])

    toast = ctk.CTkToplevel(raiz)
    toast.overrideredirect(True)
    toast.attributes("-topmost", True)
    toast.configure(fg_color=BG_FRAME)

    tarjeta = ctk.CTkFrame(
        toast,
        fg_color=tint["bg"],
        border_width=1,
        border_color=tint["border"],
        corner_radius=8,
    )
    tarjeta.pack(fill="both", expand=True)

    ctk.CTkLabel(
        tarjeta,
        text=mensaje,
        font=ctk.CTkFont(size=13, weight="bold"),
        text_color=tint["texto"],
        wraplength=380,
        justify="left",
    ).pack(padx=18, pady=12)

    # Con la tarjeta anidada dentro del toplevel hacen falta dos vueltas de
    # actualizacion: la primera resuelve el tamano de la etiqueta, la segunda
    # el de la tarjeta que la contiene. Medir solo con la primera dejaba la
    # ventana con un tamano a medias (se veia cortada, como un glitch).
    toast.update_idletasks()
    toast.update_idletasks()
    ancho = tarjeta.winfo_reqwidth()
    alto = tarjeta.winfo_reqheight()
    x = raiz.winfo_rootx() + (raiz.winfo_width() // 2) - (ancho // 2)
    y = raiz.winfo_rooty() + (raiz.winfo_height() // 2) - (alto // 2)
    toast.geometry(f"{ancho}x{alto}+{x}+{y}")

    _toast_activo_por_raiz[raiz] = toast

    def _cerrar():
        if toast.winfo_exists():
            toast.destroy()

    toast.after(duracion_ms, _cerrar)
    return toast
