#!/usr/bin/env python3
"""
Pipeline de veille du marche de l'emploi data.

Interroge France Travail et l'INSEE, deduplique, classe, et ecrit les resultats
dans data/. Chaque source est isolee : si l'une tombe, les autres passent quand meme.

Usage :
    python3 pipeline.py                  offres + entreprises
    python3 pipeline.py --offres         offres seulement
    python3 pipeline.py --entreprises    entreprises seulement
    python3 pipeline.py --js             ecrit aussi les .js pour un dashboard local
    python3 pipeline.py --dept 75 92 93  restreint la recherche d'entreprises
"""

import argparse
import sys
from datetime import datetime

from src import config, france_travail, sirene, outputs

DEPARTEMENTS_DEFAUT = ["75", "92", "93", "94", "77", "78", "91", "95"]


def run_offres(ecrire_js=False):
    print("\n[1] Offres d'emploi (France Travail)")
    token = france_travail.get_token()
    offres, echecs = france_travail.collect(token)

    chemins = [outputs.write_json(offres, "offres", "offres"),
               outputs.write_csv(offres, "offres")]
    if ecrire_js:
        chemins.append(outputs.write_js(offres, "offres", "OFFRES_DATA", "offres"))

    par_categorie = {}
    for o in offres:
        par_categorie[o["categorie"]] = par_categorie.get(o["categorie"], 0) + 1
    alternances = sum(1 for o in offres if o["alternance"])

    print(f"    {len(offres)} offres, dont {alternances} en alternance")
    print("    " + " | ".join(f"{k}:{v}" for k, v in sorted(
        par_categorie.items(), key=lambda x: -x[1])))
    for c in chemins:
        if c:
            print(f"    -> {c.relative_to(config.ROOT)}")
    return len(offres), echecs


def run_entreprises(departements, ecrire_js=False):
    print("\n[2] Entreprises (INSEE Sirene)")
    entreprises, totaux, echecs = sirene.collect(departements)

    chemins = [outputs.write_json(entreprises, "entreprises", "entreprises",
                                  {"totaux_par_naf": totaux}),
               outputs.write_csv(entreprises, "entreprises")]
    if ecrire_js:
        chemins.append(outputs.write_js(entreprises, "entreprises", "SIRENE_DATA",
                                        "entreprises", {"totaux_par_naf": totaux}))

    print(f"    {len(entreprises)} entreprises uniques de 50 salaries et plus")
    for c in chemins:
        if c:
            print(f"    -> {c.relative_to(config.ROOT)}")
    return len(entreprises), echecs


def main():
    parser = argparse.ArgumentParser(description="Veille du marche de l'emploi data")
    parser.add_argument("--offres", action="store_true", help="offres seulement")
    parser.add_argument("--entreprises", action="store_true", help="entreprises seulement")
    parser.add_argument("--js", action="store_true", help="ecrire aussi les fichiers .js")
    parser.add_argument("--dept", nargs="+", default=DEPARTEMENTS_DEFAUT,
                        help="departements pour la recherche d'entreprises")
    args = parser.parse_args()

    manquants = config.missing_credentials()
    if manquants:
        print("Cles manquantes : " + ", ".join(manquants))
        print("Copiez .env.example vers .env et renseignez vos cles.")
        return 1

    tout = not (args.offres or args.entreprises)
    debut = datetime.now()
    resume, echecs_totaux = [], []

    if tout or args.offres:
        try:
            n, echecs = run_offres(args.js)
            resume.append(f"offres: {n}")
            echecs_totaux += echecs
        except Exception as e:
            resume.append("offres: ECHEC")
            echecs_totaux.append(("France Travail", str(e)))
            print(f"    echec complet : {e}")

    if tout or args.entreprises:
        try:
            n, echecs = run_entreprises(args.dept, args.js)
            resume.append(f"entreprises: {n}")
            echecs_totaux += echecs
        except Exception as e:
            resume.append("entreprises: ECHEC")
            echecs_totaux.append(("Sirene", str(e)))
            print(f"    echec complet : {e}")

    duree = (datetime.now() - debut).total_seconds()
    print(f"\nTermine en {duree:.0f} s  |  " + "  |  ".join(resume))
    if echecs_totaux:
        print(f"{len(echecs_totaux)} appel(s) en echec :")
        for source, msg in echecs_totaux:
            print(f"  - {source} : {msg[:90]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
