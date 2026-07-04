import os
import shutil
from pathlib import Path
import sys
from typing import Optional
import msvcrt


APP_NAME = "Ancavico"


def get_bundle_dir() -> Path:
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        return Path(bundle_root).resolve()
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def get_runtime_dir() -> Path:
    return get_bundle_dir()


def get_user_data_dir() -> Path:
    if getattr(sys, "frozen", False):
        base_dir = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        data_dir = base_dir / APP_NAME
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    return get_bundle_dir()


def get_bundle_path(filename: str) -> Path:
    return get_bundle_dir() / filename


def get_data_path(filename: str) -> Path:
    return get_user_data_dir() / filename


def ensure_user_data_file(filename: str, source_filename: Optional[str] = None) -> Path:
    destination = get_data_path(filename)
    if destination.exists():
        return destination

    source_name = source_filename or filename
    source = get_bundle_path(source_name)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.exists():
        shutil.copy2(source, destination)
    return destination


class SingleInstanceLock:
    def __init__(self, filename: str = "ancavico.lock"):
        self.lock_path = get_data_path(filename)
        self.handle = None

    def acquire(self) -> bool:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = open(self.lock_path, "a+b")
        try:
            self.handle.seek(0)
            if self.handle.tell() == 0:
                self.handle.write(b"0")
                self.handle.flush()
            self.handle.seek(0)
            msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
            return True
        except OSError:
            self.release()
            return False

    def release(self):
        if not self.handle:
            return
        try:
            self.handle.seek(0)
            msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        try:
            self.handle.close()
        finally:
            self.handle = None
