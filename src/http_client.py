"""Appels HTTP avec relances, sur la bibliotheque standard uniquement."""

import time
import urllib.error
import urllib.request


class HttpError(Exception):
    pass


def request(req, timeout=30, retries=3, backoff=2.0):
    """Renvoie (headers, bytes). Relance sauf sur les erreurs qui ne servent a rien
    de retenter (400, 401, 403, 404)."""
    derniere = None
    for tentative in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.headers, resp.read()
        except urllib.error.HTTPError as e:
            if e.code == 204:
                return e.headers, b""
            if e.code in (400, 401, 403, 404):
                raise HttpError(f"HTTP {e.code} sur {req.full_url[:80]}") from e
            derniere = e
        except Exception as e:
            derniere = e
        if tentative < retries - 1:
            time.sleep(backoff * (tentative + 1))
    raise HttpError(str(derniere))
