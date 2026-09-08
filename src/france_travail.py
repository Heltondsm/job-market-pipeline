"""Collecte des offres via l'API France Travail (Offres d'emploi v2)."""

import json
import re
import time
import urllib.parse
import urllib.request

from . import config
from .http_client import request


def get_token():
    """Authentification OAuth2 en client_credentials."""
    data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": config.FT_CLIENT_ID,
        "client_secret": config.FT_CLIENT_SECRET,
        "scope": "api_offresdemploiv2 o2dsoffre",
    }).encode()
    req = urllib.request.Request(config.FT_TOKEN_URL, data=data, headers={
        "Content-Type": "application/x-www-form-urlencoded"})
    _, body = request(req, timeout=20)
    return json.loads(body)["access_token"]


def search(token, params):
    """Renvoie (total annonce par l'API, liste des resultats)."""
    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{config.FT_OFFRES_URL}?{query}", headers={
        "Authorization": f"Bearer {token}", "Accept": "application/json"})
    headers, body = request(req)
    total = 0
    content_range = headers.get("Content-Range", "") or ""
    if "/" in content_range:
        try:
            total = int(content_range.split("/")[1])
        except (ValueError, IndexError):
            pass
    resultats = json.loads(body).get("resultats", []) if body else []
    return total, resultats


def classify(titre):
    """Range une offre dans une famille de metiers a partir de son intitule.
    L'ordre compte : analytics engineer avant data engineer, sinon il serait avale."""
    t = titre.lower()
    if re.search(r"analytics engineer", t):
        return "AE"
    if re.search(r"data scientist|science des données", t):
        return "DS"
    if re.search(r"machine learning|ml engineer|\bia\b|intelligence artificielle|deep learning|llm", t):
        return "ML"
    if re.search(r"data engineer|ingénieur.{0,12}(data|données)|big data|etl|spark|pipeline", t):
        return "DE"
    if re.search(r"power ?bi|business intelligence|\bbi\b|tableau|qlik|dataviz", t):
        return "BI"
    if re.search(r"data (manager|steward|owner|gouvern)|gouvernance", t):
        return "GOUV"
    if re.search(r"data analyst|analyste.{0,12}(data|données)|analyst", t):
        return "DA"
    return "DATA"


def format_salaire(salaire):
    if not salaire:
        return ""
    libelle = salaire.get("libelle", "") or ""
    return (libelle
            .replace("Annuel de ", "")
            .replace("Mensuel de ", "/mois : ")
            .replace(" Euros", " €")
            .strip())


def is_alternance(offre, titre):
    nature = (offre.get("natureContrat") or "").lower()
    return (bool(offre.get("alternance"))
            or "alternance" in nature
            or "apprentissage" in nature
            or bool(re.search(r"alternan|apprenti", titre.lower())))


def normalize(offre, categorie_repli):
    titre = (offre.get("intitule") or "").strip()
    lieu = (offre.get("lieuTravail") or {}).get("libelle", "") or ""
    dept = re.match(r"^(\d{2,3})\s*-", lieu)
    categorie = classify(titre)
    oid = offre.get("id", "")
    return {
        "id": oid,
        "titre": titre[:110],
        "entreprise": ((offre.get("entreprise") or {}).get("nom") or "n/c")[:55],
        "lieu": lieu[:45],
        "departement": dept.group(1) if dept else "",
        "contrat": offre.get("typeContrat", "") or "",
        "alternance": is_alternance(offre, titre),
        "salaire": format_salaire(offre.get("salaire"))[:70],
        "experience": ((offre.get("experienceLibelle") or "")
                       .replace("Débutant accepté", "Débutant ok"))[:40],
        "date": (offre.get("dateCreation") or "")[:10],
        "categorie": categorie if categorie != "DATA" else categorie_repli,
        "url": ((offre.get("origineOffre") or {}).get("urlOrigine", "")
                or f"https://candidat.francetravail.fr/offres/recherche/detail/{oid}"),
    }


def collect(token, searches=None, pause=0.4, verbose=True):
    """Lance toutes les recherches, deduplique sur l'identifiant de l'offre.
    Une recherche qui echoue n'interrompt pas les autres."""
    searches = searches or config.SEARCHES
    vues, offres, echecs = set(), [], []
    for mots, categorie_repli in searches:
        try:
            _, resultats = search(token, {"motsCles": mots, "range": "0-99", "sort": "1"})
        except Exception as e:
            echecs.append((mots, str(e)))
            if verbose:
                print(f"  x  {mots} : {e}")
            continue
        nouvelles = 0
        for offre in resultats:
            oid = offre.get("id", "")
            if not oid or oid in vues:
                continue
            vues.add(oid)
            offres.append(normalize(offre, categorie_repli))
            nouvelles += 1
        if verbose:
            print(f"  ok {mots} : +{nouvelles} (total {len(offres)})")
        time.sleep(pause)
    offres.sort(key=lambda o: o["date"], reverse=True)
    return offres, echecs
