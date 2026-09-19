#!/usr/bin/env python3
"""Refresh the public Unciv Mod metadata index from GitHub's unciv-mod topic."""

from __future__ import annotations

import argparse
import json
import math
import os
import ssl
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_URL = "https://api.github.com/search/repositories"
PER_PAGE = 100
MAX_SEARCH_RESULTS = 1000
REQUEST_INTERVAL_SECONDS = 6.2
METADATA_FIELDS = (
    "id",
    "full_name",
    "description",
    "html_url",
    "created_at",
    "updated_at",
    "pushed_at",
    "stargazers_count",
    "forks_count",
    "open_issues_count",
    "language",
    "size",
    "default_branch",
    "topics",
    "archived",
    "fork",
    "license",
)

last_request_at = 0.0


def system_ca_bundle() -> Path | None:
    candidates = [
        os.environ.get("SSL_CERT_FILE"),
        ssl.get_default_verify_paths().cafile,
        "/etc/ssl/cert.pem",
        "/etc/pki/tls/certs/ca-bundle.crt",
    ]
    try:
        import certifi

        candidates.append(certifi.where())
    except ImportError:
        pass
    return next((Path(path) for path in candidates if path and Path(path).is_file()), None)


SSL_CONTEXT = ssl.create_default_context(cafile=system_ca_bundle())


def api_get(query: str, page: int) -> dict:
    global last_request_at
    delay = REQUEST_INTERVAL_SECONDS - (time.monotonic() - last_request_at)
    if delay > 0:
        time.sleep(delay)

    url = f"{API_URL}?{urlencode({'q': query, 'per_page': PER_PAGE, 'page': page})}"
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "unciv-mod-creator-skill",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        response = urlopen(request, timeout=30, context=SSL_CONTEXT)
    except HTTPError as error:
        if error.code in (403, 429):
            reset_at = error.headers.get("X-RateLimit-Reset")
            if reset_at:
                wait = max(1, int(reset_at) - int(time.time()) + 1)
                print(f"GitHub rate limit reached; waiting {wait}s", flush=True)
                time.sleep(wait)
                response = urlopen(request, timeout=30, context=SSL_CONTEXT)
            else:
                raise
        else:
            raise

    with response:
        last_request_at = time.monotonic()
        data = json.load(response)

    if data.get("incomplete_results"):
        raise RuntimeError(f"GitHub returned incomplete results for {query!r}")
    return data


def search_range(start: date, end: date) -> list[dict]:
    query = f"topic:unciv-mod created:{start.isoformat()}..{end.isoformat()}"
    first_page = api_get(query, 1)
    total = first_page["total_count"]

    if total > MAX_SEARCH_RESULTS:
        if start == end:
            raise RuntimeError(f"More than {MAX_SEARCH_RESULTS} results on {start}; cannot page completely")
        midpoint = start + timedelta(days=(end - start).days // 2)
        return search_range(start, midpoint) + search_range(midpoint + timedelta(days=1), end)

    items = list(first_page["items"])
    pages = math.ceil(total / PER_PAGE)
    for page in range(2, pages + 1):
        items.extend(api_get(query, page)["items"])
    if len(items) != total:
        raise RuntimeError(f"Expected {total} results for {query!r}, received {len(items)}")
    return items


def mod_metadata(repo: dict) -> dict:
    item = {field: repo.get(field) for field in METADATA_FIELDS}
    license_data = item["license"]
    item["license"] = None if license_data is None else {
        "spdx_id": license_data.get("spdx_id"),
        "name": license_data.get("name"),
        "url": license_data.get("url"),
    }
    return item


def main() -> None:
    script_directory = Path(__file__).resolve().parent
    default_output = script_directory.parent / "references" / "mod_catalog.json"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=default_output)
    args = parser.parse_args()

    today = datetime.now(timezone.utc).date()
    repos: dict[str, dict] = {}
    for year in range(2008, today.year + 1):
        start = date(year, 1, 1)
        end = min(date(year, 12, 31), today)
        for repo in search_range(start, end):
            repos[repo["full_name"].lower()] = mod_metadata(repo)
        print(f"Collected {year}: {len(repos)} unique repositories", flush=True)

    ordered = sorted(repos.values(), key=lambda item: item["full_name"].lower())
    catalog = {
        "source": "GitHub repository search: topic:unciv-mod",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(ordered),
        "items": ordered,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(ordered)} repositories to {args.output}", flush=True)


if __name__ == "__main__":
    main()
