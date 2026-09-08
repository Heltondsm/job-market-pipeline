"""Ecriture des sorties : JSON, CSV, et un fichier .js optionnel."""

import csv
import json
from datetime import datetime

from .config import DATA_DIR


def _payload(items, cle, extra=None):
    return {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "count": len(items),
        **(extra or {}),
        cle: items,
    }


def write_json(items, nom, cle, extra=None):
    DATA_DIR.mkdir(exist_ok=True)
    chemin = DATA_DIR / f"{nom}.json"
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(_payload(items, cle, extra), f, ensure_ascii=False, indent=2)
    return chemin


def write_csv(items, nom):
    if not items:
        return None
    DATA_DIR.mkdir(exist_ok=True)
    chemin = DATA_DIR / f"{nom}.csv"
    with open(chemin, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(items[0].keys()))
        writer.writeheader()
        writer.writerows(items)
    return chemin


def write_js(items, nom, variable, cle, extra=None):
    """Meme contenu que le JSON, mais chargeable par <script src> depuis un
    fichier local : un fetch() sur file:// est bloque par le navigateur."""
    DATA_DIR.mkdir(exist_ok=True)
    chemin = DATA_DIR / f"{nom}.js"
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(f"// genere par le pipeline, ne pas editer a la main\n")
        f.write(f"window.{variable} = ")
        json.dump(_payload(items, cle, extra), f, ensure_ascii=False)
        f.write(";\n")
    return chemin
