"""DNS provider scope filtering used by ``force-doh`` and ``recommend``.

The user picks one of three scopes:

- ``country``         : only providers whose ``region`` matches the
                        active country bucket
- ``country+majors``  : the above, plus globally-trusted majors
                        (Cloudflare / Google / Quad9)
- ``all``             : every provider in the catalog

Country -> region mapping is intentionally coarse because the real
selection driver is RTT — we only want to make sure the *primary* DNS
choice is geographically appropriate before benchmarking.
"""
from __future__ import annotations

# Country code -> provider region buckets that are "local" for it.
# Multiple regions per country lets e.g. HK users prefer both Asia-side
# and global anycast providers.
COUNTRY_TO_LOCAL_REGIONS: dict[str, set[str]] = {
    "AUTO": {"intl", "cn", "tw", "ru"},
    "CN":   {"cn"},
    "JP":   {"intl", "tw"},
    "TW":   {"tw"},
    "HK":   {"intl", "tw"},
    "KR":   {"intl"},
    "US":   {"intl"},
    "EU":   {"intl"},
    "RU":   {"ru", "intl"},
    "SG":   {"intl"},
}

# Globally-trusted, uncensored, well-monitored majors used in the
# "country + majors" scope.
GLOBAL_MAJORS: set[str] = {"Cloudflare", "Google", "Quad9"}

SCOPE_VALUES = ("country", "country+majors", "all")


def filter_providers(
    providers: dict[str, dict],
    scope: str,
    country_code: str,
) -> dict[str, dict]:
    """Return ``providers`` filtered by ``scope`` for ``country_code``."""
    if scope == "all" or country_code == "AUTO":
        return dict(providers)

    local = COUNTRY_TO_LOCAL_REGIONS.get(country_code, {"intl"})

    if scope == "country":
        return {k: v for k, v in providers.items() if v["region"] in local}

    if scope == "country+majors":
        return {
            k: v
            for k, v in providers.items()
            if v["region"] in local or k in GLOBAL_MAJORS
        }

    # Unknown scope -> safest fallback is "all".
    return dict(providers)
