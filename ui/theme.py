"""Paleta de colores compartida por todas las ventanas de la app.

Antes cada ventana definia su propia copia de estas constantes (a veces con
nombres distintos para el mismo color). Cambiar un color exigia tocar 9
archivos; ahora basta con editar este modulo.
"""

BG_APP = "#f0f2f5"
BG_FRAME = "#ffffff"
BG_HEADER = "#2d3748"
BG_HEADER_HOVER = "#1a202c"
BG_LABEL = "#e8ecf0"
COLOR_BORDE = "#cbd5e0"
COLOR_TEXTO = "#1a202c"
COLOR_SEC = "#4a5568"

# Antes "#f8f9fa", casi identico al blanco de fondo (BG_FRAME) y dificil de
# distinguir de un campo editable. Este tono tiene contraste suficiente para
# que un campo de solo lectura se note como tal de un vistazo.
COLOR_READONLY = "#e2e8f0"

# Colores semanticos de accion, ya usados de forma dispersa e inconsistente
# en cada ventana. Centralizados aqui para que "verde = confirmar/anadir",
# "rojo = peligro/salir", etc. signifique lo mismo en toda la app.
COLOR_DANGER = "#e53e3e"
COLOR_DANGER_HOVER = "#c53030"
COLOR_SUCCESS = "#2f855a"
COLOR_SUCCESS_HOVER = "#276749"
COLOR_INFO = "#2b6cb0"
COLOR_INFO_HOVER = "#2c5282"
COLOR_WARNING = "#dd6b20"
COLOR_WARNING_HOVER = "#c05621"
COLOR_PURPLE = "#805ad5"
COLOR_PURPLE_HOVER = "#6b46c1"

# Alias retrocompatible: principal.py usaba BG_SEC para el mismo color que
# BG_LABEL en el resto de ventanas.
BG_SEC = BG_LABEL

# Tintes pastel para agrupar botones por seccion en la pantalla de inicio.
# Deliberadamente suaves (no solidos): en el resto de la app "boton de color
# solido" ya significa "accion importante" (GUARDAR, SALIR...). Usar el mismo
# lenguaje visual aqui diluiria ese significado, asi que estos tintes solo
# ayudan a agrupar de un vistazo, sin competir con los botones de accion.
# "icono" es tambien el color con el que se generan los pictogramas PNG
# (ver scripts/generar_iconos.py) para que el icono y el texto combinen.
TINT_PRODUCCION = {"bg": "#ebf8ff", "hover": "#d6ecfa", "border": "#bee3f8", "texto": "#2b6cb0", "icono": "#2b6cb0"}
TINT_OPERACION = {"bg": "#f0fff4", "hover": "#dcfce7", "border": "#c6f6d5", "texto": "#276749", "icono": "#276749"}
TINT_GESTION = {"bg": BG_LABEL, "hover": COLOR_BORDE, "border": COLOR_BORDE, "texto": COLOR_SEC, "icono": "#4a5568"}

# Version suave de COLOR_DANGER para el boton "Salir" de la pantalla de
# inicio: mismo lenguaje pastel que las tarjetas de arriba (para que encaje
# con la ventana), pero en rojo para que siga leyendose como "accion de
# salida" en vez de fundirse con el resto de botones neutros.
TINT_DANGER = {"bg": "#fff5f5", "hover": "#fed7d7", "border": "#feb2b2", "texto": "#c53030"}

# Tintes suaves para las notificaciones "toast" (ver ui/toast.py). Antes cada
# tipo usaba su color solido (COLOR_SUCCESS, etc.) de fondo completo, lo que
# resultaba muy pesado visualmente para avisos que aparecen varias veces por
# turno (cada guardado). Mismo lenguaje pastel + texto de color que ya se usa
# en las tarjetas de la pantalla de inicio.
TOAST_TINTS = {
    "exito": {"bg": "#f0fff4", "border": "#c6f6d5", "texto": "#276749"},
    "advertencia": {"bg": "#fffaf0", "border": "#feebc8", "texto": "#c05621"},
    "info": {"bg": "#ebf8ff", "border": "#bee3f8", "texto": "#2b6cb0"},
    "error": {"bg": "#fff5f5", "border": "#fed7d7", "texto": "#c53030"},
}
