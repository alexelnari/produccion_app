from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from app_paths import ensure_user_data_file, get_user_data_dir


class DatabaseManager:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else ensure_user_data_file("ancavico.db")

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @staticmethod
    def _num(valor, campo: str, orden: int) -> float:
        try:
            return float(valor or 0)
        except (TypeError, ValueError):
            raise ValueError(
                f"El campo '{campo}' de la linea {orden} no es un numero valido: {valor!r}"
            )

    def backup_database_daily(self):
        if not self.db_path.exists():
            return None
        backup_dir = get_user_data_dir() / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"ancavico_{datetime.now().strftime('%Y%m%d')}.db"
        if not backup_path.exists():
            shutil.copy2(self.db_path, backup_path)
        return backup_path

    def backup_database_now(self, suffix: str = "manual") -> Optional[Path]:
        if not self.db_path.exists():
            return None
        backup_dir = get_user_data_dir() / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"ancavico_{suffix}_{timestamp}.db"
        shutil.copy2(self.db_path, backup_path)
        return backup_path

    def list_backups(self):
        backup_dir = get_user_data_dir() / "backups"
        if not backup_dir.exists():
            return []
        archivos = sorted(backup_dir.glob("ancavico_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
        return archivos

    def restore_database_from_backup(self, backup_path: Path) -> Optional[Path]:
        backup_path = Path(backup_path)
        if not backup_path.exists():
            return None

        safety_backup = self.backup_database_now("antes_restaurar")
        shutil.copy2(backup_path, self.db_path)
        self.init_db()
        return safety_backup

    def _fecha_a_iso(self, fecha: str) -> str:
        fecha = (fecha or "").strip()
        if fecha.count("/") != 2:
            return ""
        try:
            return datetime.strptime(fecha, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            return ""

    def init_db(self):
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS producciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT NOT NULL,
                    encargado TEXT NOT NULL DEFAULT '',
                    operarios TEXT NOT NULL DEFAULT '',
                    incidencias TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS lineas_produccion (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produccion_id INTEGER NOT NULL,
                    orden INTEGER NOT NULL,
                    pedido TEXT NOT NULL DEFAULT '',
                    tipo TEXT NOT NULL DEFAULT '',
                    bobina TEXT NOT NULL DEFAULT '',
                    etiqueta TEXT NOT NULL DEFAULT '',
                    caja TEXT NOT NULL DEFAULT '',
                    lote TEXT NOT NULL DEFAULT '',
                    producto TEXT NOT NULL DEFAULT '',
                    observaciones TEXT NOT NULL DEFAULT '',
                    cantidad TEXT NOT NULL DEFAULT '',
                    peso REAL NOT NULL DEFAULT 0,
                    palets INTEGER NOT NULL DEFAULT 0,
                    fabricacion TEXT NOT NULL DEFAULT '',
                    ultima_hora TEXT NOT NULL DEFAULT '',
                    factor_producto REAL NOT NULL DEFAULT 0,
                    FOREIGN KEY (produccion_id) REFERENCES producciones(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS detalle_produccion (
                    produccion_id INTEGER PRIMARY KEY,
                    lote_1_tipo TEXT NOT NULL DEFAULT '',
                    lote_1_numero TEXT NOT NULL DEFAULT '',
                    lote_2_tipo TEXT NOT NULL DEFAULT '',
                    lote_2_numero TEXT NOT NULL DEFAULT '',
                    lote_3_tipo TEXT NOT NULL DEFAULT '',
                    lote_3_numero TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY (produccion_id) REFERENCES producciones(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS detalle_produccion_filas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produccion_id INTEGER NOT NULL,
                    orden INTEGER NOT NULL,
                    marca TEXT NOT NULL DEFAULT '',
                    etiqueta TEXT NOT NULL DEFAULT '',
                    cantidad TEXT NOT NULL DEFAULT '',
                    gastado TEXT NOT NULL DEFAULT '',
                    resto TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY (produccion_id) REFERENCES producciones(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS import_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produccion_id INTEGER NOT NULL,
                    source_file TEXT NOT NULL,
                    source_sheet TEXT NOT NULL,
                    imported_at TEXT NOT NULL,
                    UNIQUE(source_file, source_sheet),
                    FOREIGN KEY (produccion_id) REFERENCES producciones(id) ON DELETE CASCADE
                );
                """
            )

    def create_production(self, fecha: str) -> int:
        ahora = datetime.now().isoformat(timespec="seconds")
        fecha = fecha or datetime.now().strftime("%d/%m/%Y")
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO producciones (fecha, created_at, updated_at)
                VALUES (?, ?, ?)
                """,
                (fecha, ahora, ahora),
            )
            produccion_id = cursor.lastrowid
            conn.execute(
                """
                INSERT INTO detalle_produccion (
                    produccion_id,
                    lote_1_tipo, lote_1_numero,
                    lote_2_tipo, lote_2_numero,
                    lote_3_tipo, lote_3_numero
                ) VALUES (?, '', '', '', '', '', '')
                """,
                (produccion_id,),
            )
            return produccion_id

    def save_snapshot(self, produccion_id: int, state: dict):
        detalle_dia = state.get("detalle_dia", {})
        detalle_produccion = state.get("detalle_produccion", {})
        lote_bobina = list(detalle_produccion.get("lote_bobina", []))
        lote_bobina += [""] * (6 - len(lote_bobina))
        lineas = state.get("lineas_produccion", [])
        filas_detalle = detalle_produccion.get("filas", [])
        ahora = datetime.now().isoformat(timespec="seconds")
        fecha = detalle_dia.get("fecha") or datetime.now().strftime("%d/%m/%Y")

        with self._connect() as conn:
            conn.execute(
                """
                UPDATE producciones
                SET fecha = ?, encargado = ?, operarios = ?, incidencias = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    detalle_dia.get("fecha", fecha),
                    detalle_dia.get("encargado", ""),
                    detalle_dia.get("operarios", ""),
                    detalle_dia.get("incidencias", ""),
                    ahora,
                    produccion_id,
                ),
            )

            conn.execute("DELETE FROM lineas_produccion WHERE produccion_id = ?", (produccion_id,))
            for orden, linea in enumerate(lineas, start=1):
                conn.execute(
                    """
                    INSERT INTO lineas_produccion (
                        produccion_id, orden, pedido, tipo, bobina, etiqueta, caja, lote,
                        producto, observaciones, cantidad, peso, palets, fabricacion,
                        ultima_hora, factor_producto
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        produccion_id,
                        orden,
                        linea.get("pedido", ""),
                        linea.get("tipo", ""),
                        linea.get("bobina", ""),
                        linea.get("etiqueta", ""),
                        linea.get("caja", ""),
                        linea.get("lote", ""),
                        linea.get("producto", ""),
                        linea.get("observaciones", ""),
                        linea.get("cantidad", ""),
                        self._num(linea.get("peso", 0), "peso", orden),
                        int(self._num(linea.get("palets", 0), "palets", orden)),
                        linea.get("fabricacion", ""),
                        linea.get("ultima_hora", ""),
                        self._num(linea.get("factor_producto", 0), "factor_producto", orden),
                    ),
                )

            conn.execute(
                """
                INSERT INTO detalle_produccion (
                    produccion_id,
                    lote_1_tipo, lote_1_numero,
                    lote_2_tipo, lote_2_numero,
                    lote_3_tipo, lote_3_numero
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(produccion_id) DO UPDATE SET
                    lote_1_tipo = excluded.lote_1_tipo,
                    lote_1_numero = excluded.lote_1_numero,
                    lote_2_tipo = excluded.lote_2_tipo,
                    lote_2_numero = excluded.lote_2_numero,
                    lote_3_tipo = excluded.lote_3_tipo,
                    lote_3_numero = excluded.lote_3_numero
                """,
                (
                    produccion_id,
                    lote_bobina[0], lote_bobina[1],
                    lote_bobina[2], lote_bobina[3],
                    lote_bobina[4], lote_bobina[5],
                ),
            )

            conn.execute("DELETE FROM detalle_produccion_filas WHERE produccion_id = ?", (produccion_id,))
            for orden, fila in enumerate(filas_detalle, start=1):
                conn.execute(
                    """
                    INSERT INTO detalle_produccion_filas (
                        produccion_id, orden, marca, etiqueta, cantidad, gastado, resto
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        produccion_id,
                        orden,
                        fila.get("marca", ""),
                        fila.get("etiqueta", ""),
                        fila.get("cantidad", ""),
                        fila.get("gastado", ""),
                        fila.get("resto", ""),
                    ),
                )

    def has_production_signature(self, fecha: str, total_lineas: int, primer_pedido: str, primer_etiqueta: str, primer_producto: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT 1
                FROM producciones p
                JOIN (
                    SELECT produccion_id, COUNT(*) AS total_lineas
                    FROM lineas_produccion
                    GROUP BY produccion_id
                ) c ON c.produccion_id = p.id
                LEFT JOIN lineas_produccion lp ON lp.produccion_id = p.id AND lp.orden = 1
                WHERE p.fecha = ?
                  AND c.total_lineas = ?
                  AND COALESCE(lp.pedido, '') = ?
                  AND COALESCE(lp.etiqueta, '') = ?
                  AND COALESCE(lp.producto, '') = ?
                LIMIT 1
                """,
                (fecha, total_lineas, primer_pedido, primer_etiqueta, primer_producto),
            ).fetchone()
        return row is not None

    def has_imported_source(self, source_file: str, source_sheet: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT 1
                FROM import_sources
                WHERE source_file = ? AND source_sheet = ?
                LIMIT 1
                """,
                (source_file, source_sheet),
            ).fetchone()
        return row is not None

    def register_import_source(self, produccion_id: int, source_file: str, source_sheet: str):
        ahora = datetime.now().isoformat(timespec="seconds")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO import_sources (produccion_id, source_file, source_sheet, imported_at)
                VALUES (?, ?, ?, ?)
                """,
                (produccion_id, source_file, source_sheet, ahora),
            )

    def delete_production(self, produccion_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM producciones WHERE id = ?", (produccion_id,))
            return cursor.rowcount > 0

    def get_historico_resumen(self):
        with self._connect() as conn:
            resumen = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_producciones,
                    COALESCE((SELECT COUNT(*) FROM lineas_produccion), 0) AS total_lineas,
                    COALESCE((SELECT ROUND(SUM(peso), 2) FROM lineas_produccion), 0) AS total_kg,
                    COALESCE((SELECT COUNT(*) FROM import_sources), 0) AS total_importadas
                FROM producciones
                """
            ).fetchone()
        return dict(resumen) if resumen else {
            "total_producciones": 0,
            "total_lineas": 0,
            "total_kg": 0,
            "total_importadas": 0,
        }

    def get_kpis_del_dia(self, fecha: str) -> dict:
        """Suma lineas y kg de TODAS las producciones creadas en esa fecha.

        Se usa para el header de la pantalla de inicio: si el operario cerro
        una produccion y abrio otra el mismo dia, el total debe reflejar el
        dia completo, no solo la produccion actualmente abierta.
        """
        with self._connect() as conn:
            fila = conn.execute(
                """
                SELECT
                    COUNT(lp.id) AS total_lineas,
                    COALESCE(ROUND(SUM(lp.peso), 2), 0) AS total_kg
                FROM producciones p
                LEFT JOIN lineas_produccion lp ON lp.produccion_id = p.id
                WHERE p.fecha = ?
                """,
                (fecha,),
            ).fetchone()
        return dict(fila) if fila else {"total_lineas": 0, "total_kg": 0}

    def get_historico_producciones(self, fecha_desde: str = "", fecha_hasta: str = "", limite: int = 100):
        where = []
        params = []
        fecha_expr = "substr(p.fecha, 7, 4) || '-' || substr(p.fecha, 4, 2) || '-' || substr(p.fecha, 1, 2)"
        fecha_desde_iso = self._fecha_a_iso(fecha_desde)
        fecha_hasta_iso = self._fecha_a_iso(fecha_hasta)
        if fecha_desde_iso:
            where.append(f"length(p.fecha) = 10 AND {fecha_expr} >= ?")
            params.append(fecha_desde_iso)
        if fecha_hasta_iso:
            where.append(f"length(p.fecha) = 10 AND {fecha_expr} <= ?")
            params.append(fecha_hasta_iso)

        query = """
            SELECT
                p.id,
                p.fecha,
                p.operarios,
                p.encargado,
                p.updated_at,
                COUNT(lp.id) AS total_lineas,
                COALESCE(ROUND(SUM(lp.peso), 2), 0) AS total_kg,
                COALESCE(MAX(CASE WHEN lp.orden = 1 THEN lp.producto END), '') AS primer_producto,
                COALESCE(MAX(CASE WHEN lp.orden = 1 THEN lp.pedido END), '') AS primer_pedido
            FROM producciones p
            LEFT JOIN lineas_produccion lp ON lp.produccion_id = p.id
        """
        if where:
            query += " WHERE " + " AND ".join(where)
        query += """
            GROUP BY p.id, p.fecha, p.operarios, p.encargado, p.updated_at
            ORDER BY p.updated_at DESC, p.id DESC
            LIMIT ?
        """
        params.append(limite)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def search_producciones(self, filtro: str, termino: str = "", limite: int = 50):
        filtro = (filtro or "fecha").lower()
        termino = (termino or "").strip()
        like = f"%{termino}%"
        base_select = """
            SELECT
                p.id,
                p.fecha,
                p.operarios,
                p.encargado,
                p.updated_at,
                COUNT(lp.id) AS total_lineas
            FROM producciones p
            LEFT JOIN lineas_produccion lp ON lp.produccion_id = p.id
        """
        base_group = """
            GROUP BY p.id, p.fecha, p.operarios, p.encargado, p.updated_at
            ORDER BY p.updated_at DESC, p.id DESC
            LIMIT ?
        """
        if filtro == "pedido":
            query = base_select + """
                WHERE EXISTS (
                    SELECT 1 FROM lineas_produccion lp2
                    WHERE lp2.produccion_id = p.id AND lp2.pedido LIKE ?
                )
            """ + base_group
            params = (like, limite)
        elif filtro == "producto":
            query = base_select + """
                WHERE EXISTS (
                    SELECT 1 FROM lineas_produccion lp2
                    WHERE lp2.produccion_id = p.id AND lp2.producto LIKE ?
                )
            """ + base_group
            params = (like, limite)
        elif filtro == "operarios":
            query = base_select + "WHERE p.operarios LIKE ? " + base_group
            params = (like, limite)
        else:
            query = base_select + "WHERE p.fecha LIKE ? " + base_group
            params = (like, limite)
        if not termino:
            query = base_select + base_group
            params = (limite,)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def load_latest_production(self) -> Optional[Tuple[int, dict]]:
        with self._connect() as conn:
            row = conn.execute("SELECT id FROM producciones ORDER BY updated_at DESC, id DESC LIMIT 1").fetchone()
        if not row:
            return None
        produccion_id = row["id"]
        return produccion_id, self.load_production(produccion_id)

    def load_latest_production_for_date(self, fecha: str) -> Optional[Tuple[int, dict]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id
                FROM producciones
                WHERE fecha = ?
                ORDER BY updated_at DESC, id DESC
                LIMIT 1
                """,
                (fecha,),
            ).fetchone()
        if not row:
            return None
        produccion_id = row["id"]
        return produccion_id, self.load_production(produccion_id)

    def get_latest_lote_for_tipo_bobina(self, tipo_bobina: str) -> str:
        tipo_bobina = (tipo_bobina or "").strip()
        if not tipo_bobina:
            return ""

        query = """
            SELECT numero_lote
            FROM (
                SELECT dp.lote_1_tipo AS tipo_bobina, dp.lote_1_numero AS numero_lote, p.updated_at, p.id
                FROM detalle_produccion dp
                JOIN producciones p ON p.id = dp.produccion_id
                UNION ALL
                SELECT dp.lote_2_tipo AS tipo_bobina, dp.lote_2_numero AS numero_lote, p.updated_at, p.id
                FROM detalle_produccion dp
                JOIN producciones p ON p.id = dp.produccion_id
                UNION ALL
                SELECT dp.lote_3_tipo AS tipo_bobina, dp.lote_3_numero AS numero_lote, p.updated_at, p.id
                FROM detalle_produccion dp
                JOIN producciones p ON p.id = dp.produccion_id
            )
            WHERE tipo_bobina = ?
              AND TRIM(COALESCE(numero_lote, '')) <> ''
            ORDER BY updated_at DESC, id DESC
            LIMIT 1
        """
        with self._connect() as conn:
            row = conn.execute(query, (tipo_bobina,)).fetchone()
        return row["numero_lote"] if row else ""

    def get_latest_etiqueta_por_tipo(self, tipo: str) -> str:
        """Ultima etiqueta (de bobina o palet) usada, la mas reciente entre
        todas las producciones. "orden" es la posicion de la linea dentro de
        su produccion (se reasigna en cada guardado), asi que ordenar por
        produccion mas reciente y luego por orden descendente da la ultima
        linea guardada de verdad.
        """
        tipo = (tipo or "").strip().upper()
        if not tipo:
            return ""

        query = """
            SELECT lp.etiqueta
            FROM lineas_produccion lp
            JOIN producciones p ON p.id = lp.produccion_id
            WHERE lp.tipo = ?
              AND TRIM(COALESCE(lp.etiqueta, '')) <> ''
            ORDER BY p.updated_at DESC, lp.orden DESC
            LIMIT 1
        """
        with self._connect() as conn:
            row = conn.execute(query, (tipo,)).fetchone()
        return row["etiqueta"] if row else ""

    def get_ultimos_caja_lote_por_producto(self, codigo_producto: str) -> dict:
        """Caja y Lote de la ultima linea guardada (en cualquier produccion)
        para un codigo de Genero, para autocompletar esos campos cuando se
        repite un producto ya usado antes. Mismo criterio de "mas reciente"
        que get_latest_etiqueta_por_tipo.
        """
        codigo_producto = (codigo_producto or "").strip()
        if not codigo_producto:
            return {"caja": "", "lote": ""}

        query = """
            SELECT lp.caja, lp.lote
            FROM lineas_produccion lp
            JOIN producciones p ON p.id = lp.produccion_id
            WHERE lp.producto = ?
            ORDER BY p.updated_at DESC, lp.orden DESC
            LIMIT 1
        """
        with self._connect() as conn:
            row = conn.execute(query, (codigo_producto,)).fetchone()
        if not row:
            return {"caja": "", "lote": ""}
        return {"caja": row["caja"] or "", "lote": row["lote"] or ""}

    def get_ultima_observacion_por_producto(self, codigo_producto: str) -> str:
        """Observaciones de la ultima linea guardada (en cualquier produccion)
        para un codigo de Genero, para autocompletar ese campo en Revision
        Final cuando se repite un producto ya usado antes. Mismo criterio de
        "mas reciente" que get_ultimos_caja_lote_por_producto.
        """
        codigo_producto = (codigo_producto or "").strip()
        if not codigo_producto:
            return ""

        query = """
            SELECT lp.observaciones
            FROM lineas_produccion lp
            JOIN producciones p ON p.id = lp.produccion_id
            WHERE lp.producto = ?
            ORDER BY p.updated_at DESC, lp.orden DESC
            LIMIT 1
        """
        with self._connect() as conn:
            row = conn.execute(query, (codigo_producto,)).fetchone()
        return (row["observaciones"] or "") if row else ""

    def get_production_summary(self, produccion_id: int) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    p.id,
                    p.fecha,
                    p.updated_at,
                    COUNT(lp.id) AS lineas
                FROM producciones p
                LEFT JOIN lineas_produccion lp ON lp.produccion_id = p.id
                WHERE p.id = ?
                GROUP BY p.id, p.fecha, p.updated_at
                """,
                (produccion_id,),
            ).fetchone()
        if not row:
            return None

        updated_at = row["updated_at"] or ""
        if updated_at:
            try:
                updated_at = datetime.fromisoformat(updated_at).strftime("%d/%m/%Y %H:%M")
            except ValueError:
                pass

        return {
            "id": row["id"],
            "fecha": row["fecha"] or "",
            "lineas": row["lineas"] or 0,
            "updated_at": updated_at,
        }

    def load_production(self, produccion_id: int) -> dict:
        with self._connect() as conn:
            produccion = conn.execute("SELECT * FROM producciones WHERE id = ?", (produccion_id,)).fetchone()
            detalle = conn.execute("SELECT * FROM detalle_produccion WHERE produccion_id = ?", (produccion_id,)).fetchone()
            lineas = conn.execute("SELECT * FROM lineas_produccion WHERE produccion_id = ? ORDER BY orden", (produccion_id,)).fetchall()
            filas_detalle = conn.execute("SELECT * FROM detalle_produccion_filas WHERE produccion_id = ? ORDER BY orden", (produccion_id,)).fetchall()

        detalle_dia = {
            "fecha": produccion["fecha"] if produccion else "",
            "encargado": produccion["encargado"] if produccion else "",
            "operarios": produccion["operarios"] if produccion else "",
            "incidencias": produccion["incidencias"] if produccion else "",
        }
        detalle_produccion = {
            "lote_bobina": [
                detalle["lote_1_tipo"] if detalle else "",
                detalle["lote_1_numero"] if detalle else "",
                detalle["lote_2_tipo"] if detalle else "",
                detalle["lote_2_numero"] if detalle else "",
                detalle["lote_3_tipo"] if detalle else "",
                detalle["lote_3_numero"] if detalle else "",
            ],
            "filas": [
                {
                    "marca": fila["marca"],
                    "etiqueta": fila["etiqueta"],
                    "cantidad": fila["cantidad"],
                    "gastado": fila["gastado"],
                    "resto": fila["resto"],
                }
                for fila in filas_detalle
            ],
        }
        lineas_produccion = [
            {
                "pedido": linea["pedido"],
                "tipo": linea["tipo"],
                "bobina": linea["bobina"],
                "etiqueta": linea["etiqueta"],
                "caja": linea["caja"],
                "lote": linea["lote"],
                "producto": linea["producto"],
                "observaciones": linea["observaciones"],
                "cantidad": linea["cantidad"],
                "peso": linea["peso"],
                "palets": linea["palets"],
                "fabricacion": linea["fabricacion"],
                "ultima_hora": linea["ultima_hora"],
                "factor_producto": linea["factor_producto"],
            }
            for linea in lineas
        ]
        return {
            "lineas_produccion": lineas_produccion,
            "detalle_dia": detalle_dia,
            "detalle_produccion": detalle_produccion,
        }
