import json
from datetime import datetime
import re

from app_paths import ensure_user_data_file

JSON_PATH = ensure_user_data_file("tolvas_info.json")


def cargar_tolvas():
    if not JSON_PATH.exists():
        return {}
    with open(JSON_PATH, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    return {str(k): v for k, v in data.items()}


TOLVAS = cargar_tolvas()


def recargar_tolvas():
    global TOLVAS
    TOLVAS = cargar_tolvas()
    return TOLVAS


def buscar_tolvas(codigo):
    return TOLVAS.get(str(codigo).strip())


def guardar_tolvas_producto(codigo, datos):
    codigo = str(codigo).strip()
    data = cargar_tolvas()
    articulo = int(codigo) if codigo.isdigit() else codigo
    tolvas = list(datos.get("tolvas", []))[:8]
    tolvas += [""] * (8 - len(tolvas))
    data[codigo] = {
        "articulo": articulo,
        "tolvas": tolvas,
        "porcentaje": str(datos.get("porcentaje", "") or ""),
        "descripcion": str(datos.get("descripcion", "") or ""),
        "pesos": str(datos.get("pesos", "") or ""),
        "kilos_caja": str(datos.get("kilos_caja", "") or ""),
        "tipo_caja": str(datos.get("tipo_caja", "") or ""),
        "tipo_plastico": str(datos.get("tipo_plastico", "") or ""),
        "precinto": str(datos.get("precinto", "") or ""),
        "detalle_fabricacion": str(datos.get("detalle_fabricacion", "") or ""),
        "ultima_edicion": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    recargar_tolvas()
    return data[codigo]


def _normalizar_ingrediente(valor):
    texto = str(valor or "").strip().lower()
    if not texto:
        return ""

    reemplazos = {
        "carn.": "carne",
        "mej.": "mejillon",
        "cab.": "cabeza",
        "pim.": "pimiento",
        "lang.": "langostino",
    }
    for origen, destino in reemplazos.items():
        texto = texto.replace(origen, destino)

    texto = texto.replace('"', "")
    texto = texto.replace("-", " ")
    texto = re.sub(r"\s+", " ", texto).strip()

    sinonimos = {
        "anillas": "anilla",
        "almejas": "almeja",
        "mejillon entero": "mejillon entero",
        "mejillon con concha": "mejillon entero",
        "mejillon roto": "mejillon roto",
        "mejillon p": "mejillon p",
        "mejillon m": "mejillon m",
        "mejillon e": "mejillon entero",
        "carne de almeja": "carne almeja",
        "carn almeja": "carne almeja",
        "gamba grecia": "gamba",
        "cab de pulpo": "cabeza pulpo",
        "cabeza de pulpo": "cabeza pulpo",
        "cab pulpo": "cabeza pulpo",
        "rejo p": "rejo",
        "marzoquita": "mazorquita",
        "cebollita": "cebolla",
        "pimiento verde": "pim verde",
        "pim verde": "pim verde",
        "pimiento rojo": "pim rojo",
        "pim rojo": "pim rojo",
    }
    return sinonimos.get(texto, texto)


def _extraer_ingredientes(valor):
    texto = str(valor or "").strip()
    if not texto:
        return []

    partes = re.split(r"[;/]", texto)
    ingredientes = []
    for parte in partes:
        ingrediente = _normalizar_ingrediente(parte)
        if ingrediente:
            ingredientes.append(ingrediente)
    return ingredientes


def _ingredientes_normalizados(datos_articulo):
    ingredientes = []
    vistos = set()
    for valor in datos_articulo.get("tolvas", []):
        for ingrediente in _extraer_ingredientes(valor):
            if ingrediente in vistos:
                continue
            vistos.add(ingrediente)
            ingredientes.append(ingrediente)
    return ingredientes


def buscar_composiciones_parecidas(codigo, limite=5):
    codigo = str(codigo).strip()
    actual = buscar_tolvas(codigo)
    if not actual:
        return []

    ingredientes_actuales = set(_ingredientes_normalizados(actual))
    if not ingredientes_actuales:
        return []

    parecidas = []
    for otro_codigo, datos in TOLVAS.items():
        otro_codigo = str(otro_codigo).strip()
        if otro_codigo == codigo:
            continue

        ingredientes_otro = set(_ingredientes_normalizados(datos))
        if not ingredientes_otro:
            continue

        compartidos = ingredientes_actuales & ingredientes_otro
        if len(compartidos) < 2:
            continue

        solo_actual = ingredientes_actuales - ingredientes_otro
        solo_otro = ingredientes_otro - ingredientes_actuales
        score = (len(compartidos) * 100) - (len(solo_actual) * 10) - (len(solo_otro) * 10)
        parecidas.append(
            {
                "codigo": otro_codigo,
                "descripcion": str(datos.get("descripcion", "") or ""),
                "compartidos": sorted(compartidos),
                "solo_actual": sorted(solo_actual),
                "solo_otro": sorted(solo_otro),
                "total_compartidos": len(compartidos),
                "score": score,
            }
        )

    parecidas.sort(
        key=lambda item: (
            -item["total_compartidos"],
            -item["score"],
            item["codigo"],
        )
    )
    return parecidas[:limite]
