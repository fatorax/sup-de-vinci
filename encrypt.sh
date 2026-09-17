#!/usr/bin/env bash
# Chiffrement / dechiffrement de fichiers par mot de passe (AES-256-CBC via openssl).
#
# Usage :
#   ./encrypt.sh encrypt <fichier> [fichier_sortie]
#   ./encrypt.sh decrypt <fichier.enc> [fichier_sortie]

set -euo pipefail

usage() {
    echo "Usage: $0 {encrypt|decrypt} <fichier> [fichier_sortie]" >&2
    exit 1
}

[ $# -lt 2 ] && usage
action="$1"
input="$2"

[ -f "$input" ] || { echo "Erreur : fichier introuvable : $input" >&2; exit 1; }

case "$action" in
    encrypt)
        output="${3:-${input}.enc}"
        read -rsp "Mot de passe : " password; echo
        read -rsp "Confirmez le mot de passe : " confirm; echo
        [ "$password" = "$confirm" ] || { echo "Erreur : les mots de passe ne correspondent pas." >&2; exit 1; }

        openssl enc -aes-256-cbc -pbkdf2 -iter 390000 -salt \
            -in "$input" -out "$output" -pass pass:"$password"
        echo "Fichier chiffre : $output"
        ;;
    decrypt)
        output="${3:-${input%.enc}}"
        read -rsp "Mot de passe : " password; echo

        if ! openssl enc -d -aes-256-cbc -pbkdf2 -iter 390000 \
            -in "$input" -out "$output" -pass pass:"$password" 2>/dev/null; then
            rm -f "$output"
            echo "Erreur : mot de passe incorrect ou fichier corrompu." >&2
            exit 1
        fi
        echo "Fichier dechiffre : $output"
        ;;
    *)
        usage
        ;;
esac
