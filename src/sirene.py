"""Recherche d'entreprises via l'API Sirene de l'INSEE."""

import json
import urllib.parse
import urllib.request

from . import config
from .http_client import request

# tranches 21 a 53 = etablissements de 50 salaries et plus
TRANCHE_MIN, TRANCHE_MAX = "21", "53"

ORDRE_EFFECTIFS = [
    "5 000-9 999", "2 000-4 999", "1 000-1 999", "500-999", "250-499",
    "200-249", "150-199", "100-149", "50-99",
]


def fetch(naf_code, departements, nombre=1000):
    """Etablissements d'un code NAF dans une liste de departements.
    Renvoie (total annonce, liste dedupliquee par nom d'entreprise)."""
    filtre_dept = " OR ".join(f"codePostalEtablissement:{d}*" for d in departements)
    q = (f"periode(activitePrincipaleEtablissement:{naf_code}) AND ({filtre_dept}) "
         f"AND trancheEffectifsEtablissement:[{TRANCHE_MIN} TO {TRANCHE_MAX}]")
    params = urllib.parse.urlencode({
        "q": q,
        "nombre": nombre,
        "champs": ("denominationUniteLegale,siret,codePostalEtablissement,"
                   "libelleCommuneEtablissement,trancheEffectifsEtablissement"),
        "tri": "trancheEffectifsEtablissement desc",
    })
    req = urllib.request.Request(f"{config.SIRENE_URL}?{params}", headers={
        "X-INSEE-Api-Key-Integration": config.SIRENE_API_KEY, "Accept": "application/json"})
    _, body = request(req, timeout=20)
    data = json.loads(body)
    total = (data.get("header") or {}).get("total", 0)

    entreprises, vues = [], set()
    for etab in data.get("etablissements", []):
        nom = ((etab.get("uniteLegale") or {}).get("denominationUniteLegale") or "").strip()
        if not nom or nom in vues:
            continue
        vues.add(nom)
        adresse = etab.get("adresseEtablissement") or {}
        cp = adresse.get("codePostalEtablissement") or ""
        entreprises.append({
            "nom": nom,
            "siret": etab.get("siret", ""),
            "ville": adresse.get("libelleCommuneEtablissement", ""),
            "code_postal": cp,
            "departement": cp[:2],
            "effectif": config.TRANCHE_EFFECTIFS.get(
                etab.get("trancheEffectifsEtablissement", "NN"), "?"),
        })
    return total, entreprises


def collect(departements, naf_codes=None, verbose=True):
    """Interroge chaque code NAF, fusionne et trie par effectif decroissant.
    Un code NAF qui echoue n'interrompt pas les autres."""
    naf_codes = naf_codes or config.NAF_CODES
    fusion, vues, totaux, echecs = [], set(), {}, []
    for code, libelle in naf_codes.items():
        try:
            total, entreprises = fetch(code, departements)
        except Exception as e:
            echecs.append((code, str(e)))
            if verbose:
                print(f"  x  NAF {code} : {e}")
            continue
        totaux[code] = total
        ajoutees = 0
        for e in entreprises:
            if e["nom"] in vues:
                continue
            vues.add(e["nom"])
            e["secteur"] = libelle
            fusion.append(e)
            ajoutees += 1
        if verbose:
            print(f"  ok NAF {code} : +{ajoutees} (total {len(fusion)})")

    rang = {v: i for i, v in enumerate(ORDRE_EFFECTIFS)}
    fusion.sort(key=lambda e: rang.get(e["effectif"], 99))
    return fusion, totaux, echecs
