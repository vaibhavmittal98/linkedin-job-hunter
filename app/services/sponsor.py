"""IND recognised-sponsor matching.

Given a company name (as it appears on a scraped job), decide whether it
corresponds to an IND-recognised sponsor from the official public register.

Data source: `app/data/ind_sponsors.json` — a list of {name, kvk, key} records
scraped from ind.nl's public register. `key` is the normalized match key.

Matching is tuned for RECALL (catch all real sponsors) over precision — a few
false positives are acceptable, missing a real sponsor is not. See the rules in
`match_sponsor` for the exact strategy.

Everything here is pure/read-only: no DB, no network. The list is loaded once
into module-level sets at import time.
"""

import json
import re
import unicodedata
from pathlib import Path
from functools import lru_cache

_DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "ind_sponsors.json"

# Legal-entity / structural tokens stripped when normalizing a company name.
# (Single letters cover the "B.V." -> "b v" split after punctuation removal.)
_LEGAL_TOKENS = {
    "bv", "nv", "cv", "vof", "ua", "sarl", "llp", "llc", "ltd", "inc", "gmbh",
    "se", "pty", "sa", "cooperatief", "cooperatieve", "holding", "holdings",
    "group", "groep", "b", "v", "n", "c", "u", "a",
}

# Tokens too generic to anchor a token-subset match on their own.
_GENERIC_TOKENS = {
    "people", "corp", "group", "salt", "systems", "solutions", "services",
    "technology", "technologies", "consulting", "digital", "data",
    "international", "netherlands", "nederland", "europe", "global", "it",
    "the", "and", "of", "for", "flex", "staffing", "professionals", "life",
    "work", "next", "partners", "studios",
}


def _strip_accents(s: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch)
    )


def normalize(name: str) -> str:
    """Normalize a company name to a match key.

    Lowercase, strip accents, replace '&'->'and', drop punctuation, and remove
    legal-entity tokens. e.g. 'Coöperatieve Rabobank U.A.' -> 'rabobank',
    'Adyen N.V.' -> 'adyen', 'Booking.com B.V.' -> 'booking com'.
    """
    if not name:
        return ""
    s = _strip_accents(name.lower()).replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(t for t in s.split() if t and t not in _LEGAL_TOKENS).strip()


# --- Load the sponsor list once at import time ---------------------------------

def _load():
    keyset: set[str] = set()
    if _DATA_FILE.exists():
        records = json.loads(_DATA_FILE.read_text(encoding="utf-8"))
        for r in records:
            k = r.get("key") or normalize(r.get("name", ""))
            if k:
                keyset.add(k)
    multiword = {k for k in keyset if " " in k}
    mw_tokens = {k: set(k.split()) for k in multiword}
    return keyset, multiword, mw_tokens


_KEYSET, _MULTIWORD, _MW_TOKENS = _load()


def sponsor_count() -> int:
    """Number of distinct sponsor keys loaded (for diagnostics)."""
    return len(_KEYSET)


@lru_cache(maxsize=8192)
def is_sponsor(company: str) -> bool:
    """True if the company name matches an IND-recognised sponsor.

    Recall-tuned rules (in order):
      1. exact normalized key match
      2. a sponsor key is a leading whole-word prefix of the job key
         ('Nedap Beveiligingstechniek' -> 'nedap')
      3. the job key is a leading whole-word prefix of a multi-word sponsor key
         ('CGI' -> 'cgi nederland', 'Spotify' -> 'spotify netherlands')
      4. all tokens of a multi-word sponsor key appear in the job's tokens,
         with at least one distinctive (non-generic) shared token
         ('Just Eat Takeaway.com' -> 'takeaway com')
    """
    return match_sponsor(company) is not None


def match_sponsor(company: str) -> str | None:
    """Return the matched sponsor key, or None. See `is_sponsor` for rules."""
    k = normalize(company)
    if not k:
        return None
    if k in _KEYSET:
        return k

    words = k.split()
    kwset = set(words)

    # rule 2: sponsor key is a leading word-prefix of the job
    for i in range(len(words) - 1, 0, -1):
        pref = " ".join(words[:i])
        if pref in _KEYSET:
            return pref

    # rule 3: job is a leading word-prefix of a multi-word sponsor key
    needle = k + " "
    for s in _MULTIWORD:
        if s.startswith(needle):
            return s

    # rule 4: all tokens of a multi-word sponsor key are present in the job
    for s, ts in _MW_TOKENS.items():
        if len(ts) >= 2 and ts <= kwset and (ts - _GENERIC_TOKENS) & kwset:
            return s

    return None
