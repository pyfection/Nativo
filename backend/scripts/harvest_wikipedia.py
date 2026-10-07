"""
Harvest sentences from a Wikipedia edition into source snippets.

Snippets feed Quick Contribute: in the wiki's own language they become
"confirm the standard spelling" cards (e.g. Bavarian Wikipedia writes words
its own way), and in other languages they become "translate this sentence"
cards for people who speak them. Each sentence keeps its article URL and
the CC BY-SA licence, which the cards show and link.

    DATABASE_URL=... uv run python backend/scripts/harvest_wikipedia.py \\
        --language Bavarian --wiki bar.wikipedia.org --random 20
    ... --language English --wiki en.wikipedia.org --titles Munich Danube
    ... --full     # whole articles instead of just the lead section

Re-running is safe: sentences already stored for the language are skipped.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.database import SessionLocal  # noqa: E402
from app.models.language import Language  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services import source_service  # noqa: E402

LICENSE = "CC BY-SA 4.0"
# Wikimedia asks API clients to identify themselves.
USER_AGENT = "NativoHarvest/0.1 (https://github.com/pyfection/nativo)"
PAUSE_SECONDS = 1.0


def _api(wiki: str, params: dict, attempts: int = 4) -> dict:
    query = urllib.parse.urlencode({"format": "json", "formatversion": "2", **params})
    request = urllib.request.Request(
        f"https://{wiki}/w/api.php?{query}", headers={"User-Agent": USER_AGENT}
    )
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == attempts - 1:
                raise
            # Rate limited: wait as asked (or back off) and try again.
            time.sleep(int(exc.headers.get("Retry-After") or 0) or 5 * 2**attempt)
    raise RuntimeError("unreachable")


def _extracts(wiki: str, *, titles: list[str] | None, random: int, full: bool):
    """Yield (title, plain text) per article."""
    base = {
        "action": "query",
        "prop": "extracts|pageprops",
        "explaintext": "1",
        "ppprop": "disambiguation",
    }
    if not full:
        base["exintro"] = "1"
    # The API serves up to 20 lead sections per request, but whole articles
    # only one at a time.
    batch = 1 if full else 20
    if titles:
        chunks = [{"titles": "|".join(titles[i : i + batch])} for i in range(0, len(titles), batch)]
    else:
        chunks = []
        left = random
        while left > 0:
            size = min(batch, left)
            chunks.append({"generator": "random", "grnnamespace": "0", "grnlimit": str(size)})
            left -= size
    for i, chunk in enumerate(chunks):
        if i:
            time.sleep(PAUSE_SECONDS)
        data = _api(wiki, {**base, **chunk, "exlimit": str(batch)})
        for page in data.get("query", {}).get("pages", []):
            if page.get("missing") or not page.get("extract"):
                continue
            if "disambiguation" in page.get("pageprops", {}):
                continue  # lists of links, not prose
            yield page["title"], page["extract"]


def _language(db, name: str) -> Language:
    language = (
        db.query(Language).filter((Language.name == name) | (Language.iso_639_3 == name)).first()
    )
    if language is None:
        sys.exit(f"No language named {name!r}")
    return language


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--language", required=True, help="Language name or ISO 639-3 code")
    parser.add_argument("--wiki", required=True, help="e.g. bar.wikipedia.org")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--random", type=int, help="Number of random articles")
    source.add_argument("--titles", nargs="+", help="Article titles")
    parser.add_argument("--full", action="store_true", help="Whole articles, not just leads")
    parser.add_argument("--username", help="Account to credit (default: none)")
    parser.add_argument("--dry-run", action="store_true", help="Count, don't store")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        language = _language(db, args.language)
        creator_id = None
        if args.username:
            user = db.query(User).filter(User.username == args.username).first()
            if user is None:
                sys.exit(f"No user named {args.username!r}")
            creator_id = user.id

        total = 0
        for title, text in _extracts(
            args.wiki, titles=args.titles, random=args.random or 0, full=args.full
        ):
            url = f"https://{args.wiki}/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
            created = source_service.add_text(
                db,
                language.id,
                source_url=url,
                source_title=title,
                text=text,
                license=LICENSE,
                creator_id=creator_id,
            )
            total += len(created)
            print(f"{len(created):4d}  {title}")
        if args.dry_run:
            db.rollback()
            print(f"{total} new sentences (dry run, nothing stored)")
        else:
            db.commit()
            print(f"{total} new sentences stored for {language.name}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
