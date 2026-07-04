import traceback

from tkinter import messagebox

from app_paths import SingleInstanceLock
from ui.principal import App

if __name__ == "__main__":
    instance_lock = SingleInstanceLock()
    if not instance_lock.acquire():
        messagebox.showwarning(
            "Ancavico ya esta abierto",
            "La aplicacion ya se esta ejecutando en este equipo.\n\nCierra la ventana actual antes de abrir otra.",
        )
        raise SystemExit(0)

    try:
        app = App()
        app.mainloop()
    except Exception:
        traceback.print_exc()
        messagebox.showerror(
            "Error al iniciar Ancavico",
            "No se pudo iniciar la aplicacion. Revisa que la base de datos no este dañada y vuelve a intentarlo.",
        )
    finally:
        instance_lock.release()
