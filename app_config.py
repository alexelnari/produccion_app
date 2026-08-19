import json

from app_paths import get_data_path

CONFIG_FILENAME = "config.json"

DEFAULTS = {
    "ruta_colos": r"C:\Program Files\Colos\Colos.exe",
    "ruta_bartender": r"C:\Program Files\Seagull\BarTender.exe",
}


def cargar_config():
    ruta = get_data_path(CONFIG_FILENAME)
    if not ruta.exists():
        return dict(DEFAULTS)

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except (OSError, ValueError):
        return dict(DEFAULTS)

    config = dict(DEFAULTS)
    config.update({clave: valor for clave, valor in datos.items() if clave in DEFAULTS})
    return config


def guardar_config(config):
    ruta = get_data_path(CONFIG_FILENAME)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
