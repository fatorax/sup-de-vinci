"""Sauvegarde chiffree d'un dossier, avec cle separee et hash de verification.

Archive le dossier source en .tar.gz, chiffre l'archive (Fernet/AES),
puis ecrit trois fichiers lies par un meme horodatage :
  - backup-dir/<nom>_<horodatage>.tar.gz.enc  (archive chiffree)
  - keys-dir/<nom>_<horodatage>.key           (cle de dechiffrement)
  - keys-dir/<nom>_<horodatage>.json          (manifeste : hash SHA-256, infos)

La cle et le hash sont stockes a part de l'archive (dossier "keys" different
du dossier "backup") : quelqu'un qui vole uniquement la sauvegarde ne peut
pas la dechiffrer, et restore.py refuse toute archive dont le hash ne
correspond plus a celui du manifeste.

Usage:
    python backup.py [--source DOSSIER] [--backup-dir DOSSIER] [--keys-dir DOSSIER]
"""
import argparse
import hashlib
import json
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path

from cryptography.fernet import Fernet

DEFAULT_SOURCE = r"C:\Users\romain\Desktop\www\html"
DEFAULT_BACKUP_DIR = r"C:\Users\romain\Desktop\www\backup"
DEFAULT_KEYS_DIR = r"C:\Users\romain\Desktop\www\keys"

CHUNK_SIZE = 1024 * 1024


def sha256_of_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_archive(source: Path, dest_tar: Path) -> None:
    with tarfile.open(dest_tar, "w:gz") as tar:
        tar.add(source, arcname=source.name)


def backup(source: Path, backup_dir: Path, keys_dir: Path) -> None:
    if not source.is_dir():
        raise SystemExit(f"Erreur : dossier source introuvable : {source}")

    backup_dir.mkdir(parents=True, exist_ok=True)
    keys_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{source.name}_{timestamp}"

    with tempfile.TemporaryDirectory() as tmp:
        plain_tar = Path(tmp) / f"{backup_name}.tar.gz"
        print(f"Archivage de {source} ...")
        make_archive(source, plain_tar)

        sha256_hash = sha256_of_file(plain_tar)
        size_bytes = plain_tar.stat().st_size

        print("Chiffrement de l'archive ...")
        key = Fernet.generate_key()
        token = Fernet(key).encrypt(plain_tar.read_bytes())

    backup_file = backup_dir / f"{backup_name}.tar.gz.enc"
    key_file = keys_dir / f"{backup_name}.key"
    manifest_file = keys_dir / f"{backup_name}.json"

    backup_file.write_bytes(token)
    key_file.write_bytes(key)
    manifest_file.write_text(
        json.dumps(
            {
                "source": str(source),
                "timestamp": timestamp,
                "backup_file": backup_file.name,
                "key_file": key_file.name,
                "sha256_plaintext": sha256_hash,
                "size_bytes": size_bytes,
                "algorithm": "Fernet (AES-128-CBC + HMAC-SHA256)",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print("Sauvegarde terminee :")
    print(f"  Archive chiffree : {backup_file}")
    print(f"  Cle              : {key_file}")
    print(f"  Manifeste (hash) : {manifest_file}")
    print(f"  SHA-256          : {sha256_hash}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--backup-dir", default=DEFAULT_BACKUP_DIR)
    parser.add_argument("--keys-dir", default=DEFAULT_KEYS_DIR)
    args = parser.parse_args()

    backup(Path(args.source), Path(args.backup_dir), Path(args.keys_dir))


if __name__ == "__main__":
    main()
