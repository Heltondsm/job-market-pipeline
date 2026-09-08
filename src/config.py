"""Configuration lue depuis l'environnement ou un fichier .env."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


def load_dotenv(path=None):
    # petit loader maison, pour ne dependre d'aucun paquet externe
    path = Path(path or ROOT / ".env")
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv()

FT_CLIENT_ID = os.environ.get("FT_CLIENT_ID", "")
FT_CLIENT_SECRET = os.environ.get("FT_CLIENT_SECRET", "")
SIRENE_API_KEY = os.environ.get("SIRENE_API_KEY", "")

FT_TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire"
FT_OFFRES_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
SIRENE_URL = "https://api.insee.fr/api-sirene/3.11/siret"
INSEE_BDM_URL = "https://api.insee.fr/series/BDM/V1/data/SERIES_BDM"

# les 14 recherches lancees a chaque passage, avec la categorie de repli
SEARCHES = [
    ("data analyst", "DA"), ("data engineer", "DE"), ("data scientist", "DS"),
    ("analytics engineer", "AE"), ("business intelligence", "BI"), ("power bi", "BI"),
    ("machine learning", "ML"), ("data manager", "GOUV"), ("data steward", "GOUV"),
    ("big data", "DE"), ("ingenieur donnees", "DE"), ("analyste donnees", "DA"),
    ("dbt snowflake", "AE"), ("data", "DATA"),
]

# codes NAF interrogeables sur Sirene, avec leur libelle
NAF_CODES = {
    "62.02A": "Conseil en systemes et logiciels informatiques",
    "63.11Z": "Traitement de donnees et hebergement",
    "70.22Z": "Conseil pour les affaires et la gestion",
}

TRANCHE_EFFECTIFS = {
    "00": "0", "01": "1-2", "02": "3-5", "03": "6-9",
    "11": "10-19", "12": "20-49", "21": "50-99", "22": "100-149",
    "31": "150-199", "32": "200-249", "41": "250-499", "42": "500-999",
    "51": "1 000-1 999", "52": "2 000-4 999", "53": "5 000-9 999",
    "NN": "Non renseigne",
}


def missing_credentials():
    manquants = []
    if not FT_CLIENT_ID or not FT_CLIENT_SECRET:
        manquants.append("FT_CLIENT_ID / FT_CLIENT_SECRET")
    if not SIRENE_API_KEY:
        manquants.append("SIRENE_API_KEY")
    return manquants
