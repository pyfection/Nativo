"""
Find words to draft: tokens the corpus uses that the dictionary lacks.

Step 1 of an LLM-drafted word batch (step 2 is drafting the entries, step 3
is `import_drafts.py`). The corpus is the Bavarian UI bundle — hundreds of
natively corrected strings — plus any extra text files given.

Each candidate records how trustworthy its spelling is. A token is
*verified* when at least one string containing it was last changed by a
native-correction commit (see VERIFIED_COMMIT_PATTERN): the spelling has
been checked by a speaker, so only the dictionary work (lemma, part of
speech, gloss) is left to the drafter. Tokens seen only in strings nobody
has corrected yet are marked unverified.

Known forms come from the database (`DATABASE_URL`, raw SQL so it works on
any schema revision) or from a JSON list via --known-forms.

    uv run python backend/scripts/draft_candidates.py --language Bavarian \\
        --out candidates.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.utils.text_normalize import fold_for_match, iter_tokens  # noqa: E402

LOCALES = REPO / "frontend" / "src" / "locales"

# Commit subjects that mean "a speaker checked these strings".
VERIFIED_COMMIT_PATTERN = re.compile(
    r"native|user-verified|^fix\b|^bavarian fixes|^correct bavarian|normalize remaining bavarian"
    r"|bavarian eyebrow|bavarian: correct",
    re.IGNORECASE,
)

INTERPOLATION = re.compile(r"\{\{[^}]*\}\}")
URLISH = re.compile(r"\S+@\S+|https?://\S+|\S+\.\w{2,4}\b")


def _flatten(tree: dict, prefix: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in tree.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            out.update(_flatten(value, path))
        elif isinstance(value, str):
            out[path] = value
    return out


def _verified_lines(path: Path) -> set[int]:
    """1-based line numbers whose last change came from a verified commit."""
    blame = subprocess.run(
        ["git", "blame", "--line-porcelain", str(path)],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    summaries: dict[str, str] = {}
    verified: set[int] = set()
    sha = None
    final_line = 0
    for line in blame.splitlines():
        header = re.match(r"^([0-9a-f]{40}) \d+ (\d+)", line)
        if header:
            sha, final_line = header.group(1), int(header.group(2))
        elif line.startswith("summary "):
            summaries[sha] = line[len("summary ") :]
        elif line.startswith("\t") and VERIFIED_COMMIT_PATTERN.search(summaries.get(sha, "")):
            verified.add(final_line)
    return verified


def _locale_strings(lang_code: str) -> list[tuple[str, str, bool]]:
    """(key, string, verified) for every string in a locale bundle."""
    path = LOCALES / lang_code / "common.json"
    lines = path.read_text().splitlines()
    verified_lines = _verified_lines(path)
    flat = _flatten(json.loads(path.read_text()))

    # Map each key's value back to its line to read its blame.
    out = []
    for key, value in flat.items():
        leaf = key.rsplit(".", 1)[-1]
        encoded = json.dumps(value, ensure_ascii=False)
        line_no = next(
            (
                i + 1
                for i, text in enumerate(lines)
                if text.strip().startswith(f'"{leaf}":') and encoded in text
            ),
            None,
        )
        out.append((key, value, line_no in verified_lines))
    return out


def _known_forms(args) -> set[str]:
    if args.known_forms:
        return {fold_for_match(f) for f in json.loads(Path(args.known_forms).read_text())}
    from sqlalchemy import create_engine, text

    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "select f.form from word_forms f join lexemes l on l.id = f.lexeme_id "
                "join languages lang on lang.id = l.language_id where lang.name = :name"
            ),
            {"name": args.language},
        ).fetchall()
    return {fold_for_match(r.form) for r in rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--language", default="Bavarian")
    parser.add_argument("--locale", default="bar", help="locale bundle holding the corpus")
    parser.add_argument("--known-forms", help="JSON list of known forms instead of the DB")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    english = dict((k, v) for k, v, _ in _locale_strings("en"))
    known = _known_forms(args)

    stats: dict[str, dict] = defaultdict(
        lambda: {"surfaces": set(), "count": 0, "verified": False, "examples": []}
    )
    for key, value, verified in _locale_strings(args.locale):
        clean = URLISH.sub(" ", INTERPOLATION.sub(" ", value))
        for token, _, _ in iter_tokens(clean):
            if token.isdigit() or len(token) < 2 and token.lower() not in {"a", "i"}:
                continue
            fold = fold_for_match(token)
            if fold in known:
                continue
            entry = stats[fold]
            entry["surfaces"].add(token)
            entry["count"] += 1
            entry["verified"] = entry["verified"] or verified
            example = {"key": key, "text": value, "english": english.get(key), "verified": verified}
            if len(entry["examples"]) < 3 or (verified and not entry["examples"][0]["verified"]):
                entry["examples"].append(example)
                entry["examples"].sort(key=lambda e: not e["verified"])
                del entry["examples"][3:]

    candidates = sorted(
        (
            {
                "token": fold,
                "surfaces": sorted(entry["surfaces"]),
                "count": entry["count"],
                "verified": entry["verified"],
                "examples": entry["examples"],
            }
            for fold, entry in stats.items()
        ),
        key=lambda c: (not c["verified"], -c["count"], c["token"]),
    )
    Path(args.out).write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + "\n")
    verified = sum(c["verified"] for c in candidates)
    print(f"{len(candidates)} unknown tokens ({verified} verified) -> {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
