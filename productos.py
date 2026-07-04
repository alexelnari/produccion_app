import json

from app_paths import get_bundle_path

JSON_PATH = get_bundle_path("productos_info_filtrado.json")


def cargar_productos():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


PRODUCTOS = cargar_productos()


def recargar_productos():
    global PRODUCTOS
    PRODUCTOS = cargar_productos()
    return PRODUCTOS


def buscar_producto(codigo):
    codigo = str(codigo).strip()
    return PRODUCTOS.get(codigo)
