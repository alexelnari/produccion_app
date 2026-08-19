import json
import re
import threading
import urllib.error
import urllib.request

from version import APP_VERSION

GITHUB_REPO = "alexelnari/produccion_app"
RELEASES_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
RELEASES_PAGE_URL = f"https://github.com/{GITHUB_REPO}/releases/latest"

_TIMEOUT_SEGUNDOS = 5


def _normalizar_version(texto):
    numeros = re.findall(r"\d+", texto or "")
    return tuple(int(n) for n in numeros) if numeros else (0,)


def hay_version_mas_reciente(version_actual, version_remota):
    return _normalizar_version(version_remota) > _normalizar_version(version_actual)


def obtener_ultima_version():
    """Consulta la ultima Release en GitHub. Devuelve el tag (ej. 'v1.1') o None si falla."""
    try:
        peticion = urllib.request.Request(
            RELEASES_API_URL,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "Ancavico-App"},
        )
        with urllib.request.urlopen(peticion, timeout=_TIMEOUT_SEGUNDOS) as respuesta:
            datos = json.load(respuesta)
        return datos.get("tag_name")
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return None


def comprobar_actualizacion_en_segundo_plano(on_version_nueva):
    """Lanza la comprobacion en un hilo aparte para no bloquear el arranque.

    Si hay una version mas reciente disponible, llama a on_version_nueva(tag)
    desde ese mismo hilo en segundo plano: quien reciba el callback debe
    reprogramarlo al hilo principal (p.ej. con `after`) antes de tocar la
    interfaz, ya que Tkinter no es seguro para usarse desde otros hilos.
    """

    def _tarea():
        tag = obtener_ultima_version()
        if tag and hay_version_mas_reciente(APP_VERSION, tag):
            on_version_nueva(tag)

    threading.Thread(target=_tarea, daemon=True).start()
