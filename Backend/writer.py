# Guarda los JSON en Backend/locals_json con rutas relativas a este archivo.
# Los errores de escritura se propagan para que el flujo que llama pueda avisar.
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "locals_json"


# Comparte el guardado JSON de listas para usuarios, canchas y administradores.
def _write_json_list(path: Path, data: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as archivo:
        
        json.dump(data, archivo, ensure_ascii=False, indent=4)
        archivo.write("\n")


def write_user(dates: list[dict]) -> None:
    # Guarda la lista completa de usuarios en su archivo local.
    
    _write_json_list(DATA_DIR / "user.json", dates)


def write_courts(dates: list[dict]) -> None:
    # Guarda la lista completa de canchas en su archivo local.
    _write_json_list(DATA_DIR / "courts.json", dates)


def write_admin(data: list[dict]) -> None:
    # Guarda la lista completa de administradores en su archivo local.
    _write_json_list(DATA_DIR / "admin.json", data)
