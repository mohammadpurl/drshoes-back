"""Analyze media/products — run: python -m scripts.analyze_media"""
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.utils.slugify import slugify

ROOT = Path(__file__).resolve().parent.parent / "media" / "products"
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".webm", ".mov"}

# folder name -> canonical slug (manual mapping for messy names)
FOLDER_SLUG = {
    "ADIZERO ADIOS PRO 3": "adizero-adios-pro-3",
    "ADIZERO ADIOS PRO 4": "adizero-adios-pro-4",
    "ADIZERO BOSTON 12": "adizero-boston-12",
    "ADIZERO BOSTON 13": "adizero-boston-13",
    "Boston 13": "adizero-boston-13",
    "ADIZERO PRIME X3 STRUNG": "adizero-prime-x3-strung",
    "Cloudmonster 2": "on-cloudmonster-2",
    "On Cloudmonster 2": "on-cloudmonster-2",
    "Evo sl": "adizero-evo-sl",
    "evosl": "adizero-evo-sl",
    "Running Adizero EVO SL ATR": "adizero-evo-sl-atr",
    "Nike": "nike-v2k",
    "Nike2": "nike-v2k",
    "Nike Metcon3": "nike-metcon-3",
    "Nike Vaporfly 3": "nike-vaporfly-3",
    "nikeinvincible4": "nike-invincible-4",
    "Pro 3": "adizero-adios-pro-3",
    "Pro 4": "adizero-adios-pro-4",
    "pro4": "adizero-adios-pro-4",
    "ZOOM FLY 6": "nike-zoom-fly-6",
    "New folder": "_unassigned",
}

# root loose files -> slug by filename keywords
ROOT_RULES = [
    ("cloudmonster", "on-cloudmonster-2"),
    ("boston", "adizero-boston-12"),
    ("boston 13", "adizero-boston-13"),
    ("evo sl", "adizero-evo-sl"),
    ("evosl", "adizero-evo-sl"),
    ("zoom fly", "nike-zoom-fly-6"),
    ("vaporfly", "nike-vaporfly-3"),
    ("pro 4", "adizero-adios-pro-4"),
    ("pro 3", "adizero-adios-pro-3"),
    ("pro 444", "adizero-adios-pro-4"),
    ("adios pro", "adizero-adios-pro-4"),
    ("prime x3", "adizero-prime-x3-strung"),
    ("v2k", "nike-v2k"),
]


def guess_slug_from_filename(name: str) -> str:
    low = name.lower()
    for key, slug in ROOT_RULES:
        if key in low:
            return slug
    return slugify(Path(name).stem) or "unassigned"


def target_slug(path: Path) -> str:
    rel = path.relative_to(ROOT)
    parts = rel.parts
    if len(parts) == 1:
        return guess_slug_from_filename(parts[0])
    top = parts[0]
    return FOLDER_SLUG.get(top, slugify(top))


def main() -> None:
    files = [p for p in ROOT.rglob("*") if p.is_file() and p.suffix.lower() in EXTS]
    by_hash: dict[str, list[Path]] = defaultdict(list)
    for p in files:
        by_hash[hashlib.md5(p.read_bytes()).hexdigest()].append(p)

    dups = {h: ps for h, ps in by_hash.items() if len(ps) > 1}
    by_slug: dict[str, list[Path]] = defaultdict(list)
    for p in files:
        by_slug[target_slug(p)].append(p)

    out = {
        "total_files": len(files),
        "unique_hashes": len(by_hash),
        "duplicate_groups": len(dups),
        "files_to_remove_as_duplicates": sum(len(ps) - 1 for ps in dups.values()),
        "proposed_slugs": {k: len(v) for k, v in sorted(by_slug.items())},
        "duplicate_groups_detail": [
            {
                "keep": str(sorted(ps, key=lambda x: len(str(x)))[0].relative_to(ROOT)),
                "remove": [
                    str(p.relative_to(ROOT))
                    for p in sorted(ps, key=lambda x: len(str(x)))[1:]
                ],
            }
            for ps in sorted(dups.values(), key=lambda x: -len(x))
        ],
    }
    report = Path(__file__).resolve().parent.parent / "data" / "media_analysis.json"
    report.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Report:", report)
    print("Total:", out["total_files"], "| Unique:", out["unique_hashes"])
    print("Duplicates to remove:", out["files_to_remove_as_duplicates"])
    print("Slugs:", ", ".join(out["proposed_slugs"].keys()))


if __name__ == "__main__":
    main()
