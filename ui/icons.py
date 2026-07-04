"""Carga de los iconos PNG (generados por scripts/generar_iconos.py) como
CTkImage, con cache en memoria para no releer el mismo archivo varias veces.

No importa nada de ui/principal.py a proposito: varias ventanas se importan
entre si (principal.py importa produccion.py, tolvas.py, etc.), y si este
modulo importara de vuelta desde principal.py se crearia un import circular.
"""

import sys
from pathlib import Path

import customtkinter as ctk
from PIL import Image

_CACHE = {}


def _resource_path(relative_path: str) -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).resolve().parent.parent / relative_path


def cargar_icono(nombre, tamano=18):
    """Devuelve un ctk.CTkImage para assets/icons/{nombre}.png, o None si no existe."""
    clave = (nombre, tamano)
    if clave in _CACHE:
        return _CACHE[clave]

    ruta = _resource_path(f"assets/icons/{nombre}.png")
    if not ruta.exists():
        return None

    imagen = Image.open(ruta)
    ctk_imagen = ctk.CTkImage(light_image=imagen, dark_image=imagen, size=(tamano, tamano))
    _CACHE[clave] = ctk_imagen
    return ctk_imagen
