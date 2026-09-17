"""Configuration partagee par backup.py, restore.py et encrypt.py.

Les valeurs sont lues depuis config.json (cree automatiquement avec des
valeurs par defaut s'il n'existe pas encore). Modifier config.json suffit
a changer les dossiers utilises ou les parametres de cryptage, sans toucher
aux scripts.
"""
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent / "config.json"

DEFAULTS = {
    "source_dir": r"C:\Users\romain\Desktop\www\html",
    "backup_dir": r"C:\Users\romain\Desktop\www\backup",
    "keys_dir": r"C:\Users\romain\Desktop\www\keys",
    "compression": "gz",
    "kdf_iterations": 390000,
}

VALID_COMPRESSIONS = {"gz", "bz2", "xz"}


def load() -> dict:
    """Charge config.json (le cree avec les valeurs par defaut si absent)."""
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(json.dumps(DEFAULTS, indent=2), encoding="utf-8")
        return dict(DEFAULTS)

    config = {**DEFAULTS, **json.loads(CONFIG_PATH.read_text(encoding="utf-8"))}

    if config["compression"] not in VALID_COMPRESSIONS:
        raise SystemExit(
            f"Erreur config.json : compression invalide '{config['compression']}' "
            f"(valeurs possibles : {', '.join(sorted(VALID_COMPRESSIONS))})"
        )
    if not isinstance(config["kdf_iterations"], int) or config["kdf_iterations"] < 1:
        raise SystemExit("Erreur config.json : kdf_iterations doit etre un entier positif")

    return config
