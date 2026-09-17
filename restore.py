"""Restauration d'une sauvegarde chiffree creee par backup.py.

Retrouve la cle et le manifeste correspondant a une sauvegarde, dechiffre
l'archive, verifie que son hash SHA-256 correspond bien a celui enregistre
au moment de la sauvegarde (protection contre corruption/alteration), puis
extrait le contenu dans le dossier de destination.

Usage:
    python restore.py --list
    python restore.py [--backup NOM_OU_HORODATAGE] [--dest DOSSIER]
                       [--backup-dir DOSSIER] [--keys-dir DOSSIER] [--force]

Sans --backup, la sauvegarde la plus recente est utilisee.
Sans --dest, la restauration se fait dans le dossier source d'origine
(refuse si non vide, sauf --force).
"""
import argparse
import hashlib
import json
import tarfile
import tempfile
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

DEFAULT_BACKUP_DIR = r"C:\Users\romain\Desktop\www\backup"
DEFAULT_KEYS_DIR = r"C:\Users\romain\Desktop\www\keys"


def sha256_of_bytes(data: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(data)
    return digest.hexdigest()


def list_backups(keys_dir: Path) -> list:
    manifests = sorted(keys_dir.glob("*.json"))
    return [json.loads(m.read_text(encoding="utf-8")) for m in manifests]


def find_manifest(keys_dir: Path, name):
    manifests = list_backups(keys_dir)
    if not manifests:
        raise SystemExit(f"Erreur : aucune sauvegarde trouvee dans {keys_dir}")

    if name is None:
        return manifests[-1]

    for m in manifests:
        backup_stem = m["backup_file"]
        if backup_stem.endswith(".tar.gz.enc"):
            backup_stem = backup_stem[: -len(".tar.gz.enc")]
        candidates = {m["backup_file"], m["timestamp"], backup_stem, Path(m["key_file"]).stem}
        if name in candidates:
            return m

    raise SystemExit(f"Erreur : sauvegarde '{name}' introuvable dans {keys_dir}")


def restore(manifest: dict, backup_dir: Path, keys_dir: Path, dest: Path, force: bool) -> None:
    backup_file = backup_dir / manifest["backup_file"]
    key_file = keys_dir / manifest["key_file"]

    if not backup_file.is_file():
        raise SystemExit(f"Erreur : archive introuvable : {backup_file}")
    if not key_file.is_file():
        raise SystemExit(f"Erreur : cle introuvable : {key_file}")

    if dest.exists() and any(dest.iterdir()) and not force:
        raise SystemExit(
            f"Erreur : le dossier de destination '{dest}' existe deja et n'est pas vide. "
            "Utilisez --force pour ecraser son contenu."
        )

    key = key_file.read_bytes()
    token = backup_file.read_bytes()

    print("Dechiffrement de l'archive ...")
    try:
        plaintext = Fernet(key).decrypt(token)
    except (InvalidToken, ValueError):
        raise SystemExit("Erreur : cle invalide ou archive corrompue (echec du dechiffrement).")

    print("Verification du hash SHA-256 ...")
    actual_hash = sha256_of_bytes(plaintext)
    expected_hash = manifest["sha256_plaintext"]
    if actual_hash != expected_hash:
        raise SystemExit(
            "Erreur : hash invalide, l'archive semble corrompue ou alteree.\n"
            f"  Attendu : {expected_hash}\n"
            f"  Obtenu  : {actual_hash}"
        )
    print("Hash valide, l'archive est intacte.")

    dest.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_tar = Path(tmp) / "restore.tar.gz"
        tmp_tar.write_bytes(plaintext)
        print(f"Extraction vers {dest} ...")
        with tarfile.open(tmp_tar, "r:gz") as tar:
            tar.extractall(dest)

    print(f"Restauration terminee dans : {dest}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--backup", help="Nom de fichier ou horodatage de la sauvegarde (defaut : la plus recente)")
    parser.add_argument("--dest", help="Dossier de destination (defaut : dossier source d'origine)")
    parser.add_argument("--backup-dir", default=DEFAULT_BACKUP_DIR)
    parser.add_argument("--keys-dir", default=DEFAULT_KEYS_DIR)
    parser.add_argument("--force", action="store_true", help="Ecraser le dossier de destination s'il n'est pas vide")
    parser.add_argument("--list", action="store_true", help="Lister les sauvegardes disponibles et quitter")
    args = parser.parse_args()

    keys_dir = Path(args.keys_dir)

    if args.list:
        manifests = list_backups(keys_dir)
        if not manifests:
            print("Aucune sauvegarde trouvee.")
            return
        for m in manifests:
            print(f"{m['timestamp']}  {m['backup_file']}  ({m['size_bytes']} octets, source: {m['source']})")
        return

    manifest = find_manifest(keys_dir, args.backup)
    dest = Path(args.dest) if args.dest else Path(manifest["source"])

    restore(manifest, Path(args.backup_dir), keys_dir, dest, args.force)


if __name__ == "__main__":
    main()
