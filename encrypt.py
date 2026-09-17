"""Chiffrement / dechiffrement de fichiers par mot de passe (AES via Fernet).

Le nombre d'iterations PBKDF2 par defaut vient de config.json (kdf_iterations)
et est enregistre dans l'en-tete de chaque fichier chiffre : changer cette
valeur dans config.json n'empeche donc pas de dechiffrer d'anciens fichiers.

Usage:
    python encrypt.py encrypt <fichier> [--out fichier.enc]
    python encrypt.py decrypt <fichier.enc> [--out fichier]
"""
import argparse
import base64
import getpass
import os
import struct

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

import config as cfg

SALT_SIZE = 16
HEADER = struct.Struct(">I")  # iterations PBKDF2, stockees dans le fichier


def derive_key(password: str, salt: bytes, iterations: int) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def encrypt_file(path: str, out_path: str, password: str, iterations: int) -> None:
    salt = os.urandom(SALT_SIZE)
    key = derive_key(password, salt, iterations)
    token = Fernet(key).encrypt(open(path, "rb").read())

    with open(out_path, "wb") as f:
        f.write(HEADER.pack(iterations) + salt + token)
    print(f"Fichier chiffre : {out_path}")


def decrypt_file(path: str, out_path: str, password: str) -> None:
    data = open(path, "rb").read()
    (iterations,) = HEADER.unpack_from(data)
    offset = HEADER.size
    salt, token = data[offset : offset + SALT_SIZE], data[offset + SALT_SIZE :]
    key = derive_key(password, salt, iterations)

    try:
        plaintext = Fernet(key).decrypt(token)
    except InvalidToken:
        raise SystemExit("Erreur : mot de passe incorrect ou fichier corrompu.")

    with open(out_path, "wb") as f:
        f.write(plaintext)
    print(f"Fichier dechiffre : {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["encrypt", "decrypt"])
    parser.add_argument("fichier")
    parser.add_argument("--out", help="Fichier de sortie (par defaut : ajoute/retire .enc)")
    args = parser.parse_args()

    if args.action == "encrypt":
        out_path = args.out or args.fichier + ".enc"
    else:
        out_path = args.out or (
            args.fichier[:-4] if args.fichier.endswith(".enc") else args.fichier + ".dec"
        )

    password = getpass.getpass("Mot de passe : ")

    if args.action == "encrypt":
        confirm = getpass.getpass("Confirmez le mot de passe : ")
        if password != confirm:
            raise SystemExit("Erreur : les mots de passe ne correspondent pas.")
        encrypt_file(args.fichier, out_path, password, cfg.load()["kdf_iterations"])
    else:
        decrypt_file(args.fichier, out_path, password)


if __name__ == "__main__":
    main()
