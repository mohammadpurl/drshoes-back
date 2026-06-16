"""
Reorganize media/products -> media/products/{slug}/[{color}/]file
and remove duplicate files (same MD5).

Usage:
  python -m scripts.organize_media --dry-run
  python -m scripts.organize_media
"""

import argparse
import hashlib
import json
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.utils.slugify import slugify

ROOT = Path(__file__).resolve().parent.parent / "media" / "products"
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".webm", ".mov"}
COLORS = {"black", "white", "gray", "grey", "blue", "brown", "orange", "green"}

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

ROOT_RULES = [
    ("cloudmonster", "on-cloudmonster-2"),
    ("boston 13", "adizero-boston-13"),
    ("boston", "adizero-boston-12"),
    ("evo sl", "adizero-evo-sl"),
    ("evosl", "adizero-evo-sl"),
    ("zoom fly", "nike-zoom-fly-6"),
    ("vaporfly", "nike-vaporfly-3"),
    ("pro 444", "adizero-adios-pro-4"),
    ("pro 4", "adizero-adios-pro-4"),
    ("pro 3", "adizero-adios-pro-3"),
    ("adios pro 4", "adizero-adios-pro-4"),
    ("adios pro 3", "adizero-adios-pro-3"),
    ("prime x3", "adizero-prime-x3-strung"),
    ("v2k", "nike-v2k"),
    ("metcon", "nike-metcon-3"),
    ("invincible", "nike-invincible-4"),
]


def guess_slug_from_filename(name: str) -> str:
    low = name.lower()
    for key, slug in ROOT_RULES:
        if key in low:
            return slug
    if re.match(r"^\d{10,}_\d+_n", low):
        return "adizero-adios-pro-4"
    return slugify(Path(name).stem) or "unassigned"


def parse_path(path: Path) -> tuple[str, str | None]:
    rel = path.relative_to(ROOT)
    parts = rel.parts
    if len(parts) == 1:
        return guess_slug_from_filename(parts[0]), None
    top = parts[0]
    slug = FOLDER_SLUG.get(top, slugify(top))
    color = None
    if len(parts) >= 3 and parts[1].lower() in COLORS:
        color = parts[1].lower().replace("grey", "gray")
    return slug, color


def file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def pick_canonical(paths: list[Path]) -> Path:
    def score(p: Path) -> tuple:
        rel = p.relative_to(ROOT)
        in_folder = 0 if len(rel.parts) == 1 else 1
        numbered = 1 if re.search(r"\(\d+\)", p.name) else 0
        return (-in_folder, numbered, len(str(rel)), str(rel))

    return sorted(paths, key=score)[0]


def clean_filename(path: Path, digest: str) -> str:
    stem = slugify(path.stem) or digest[:8]
    if len(stem) > 48:
        stem = stem[:48]
    return f"{stem}{path.suffix.lower()}"


def collect_files() -> list[Path]:
    return [p for p in ROOT.rglob("*") if p.is_file() and p.suffix.lower() in EXTS]


def remove_junk(dry_run: bool) -> int:
    removed = 0
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix.lower() not in EXTS:
            if dry_run:
                print(f"[dry-run] delete junk: {p.relative_to(ROOT)}")
            else:
                p.unlink(missing_ok=True)
            removed += 1
    return removed


def organize(*, dry_run: bool) -> dict:
    files = collect_files()
    by_hash: dict[str, list[Path]] = defaultdict(list)
    for p in files:
        by_hash[file_hash(p)].append(p)

    to_delete: list[Path] = []
    to_move: list[tuple[Path, Path]] = []
    seen_dest_hash: dict[str, str] = {}

    for digest, group in by_hash.items():
        canonical = pick_canonical(group)
        slug, color = parse_path(canonical)
        dest_dir = ROOT / slug / (color or "")
        fname = clean_filename(canonical, digest)
        dest = dest_dir / fname
        n = 1
        while dest.exists() and file_hash(dest) != digest:
            dest = dest_dir / f"{dest.stem}-{n}{dest.suffix}"
            n += 1

        if canonical.resolve() != dest.resolve():
            to_move.append((canonical, dest))

        seen_dest_hash[str(dest.resolve())] = digest

        for p in group:
            if p.resolve() != canonical.resolve():
                to_delete.append(p)

    # second pass: if canonical already moved in plan, ok
    actions = {"deleted": 0, "moved": 0, "junk": 0}
    actions["junk"] = remove_junk(dry_run)

    for p in to_delete:
        if dry_run:
            print(f"[dry-run] delete dup: {p.relative_to(ROOT)}")
        else:
            p.unlink(missing_ok=True)
        actions["deleted"] += 1

    for src, dest in to_move:
        if dry_run:
            print(f"[dry-run] move: {src.relative_to(ROOT)} -> {dest.relative_to(ROOT)}")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if src.exists():
                shutil.move(str(src), str(dest))
        actions["moved"] += 1

    if not dry_run:
        for d in sorted(ROOT.rglob("*"), reverse=True):
            if d.is_dir() and d != ROOT and not any(d.iterdir()):
                d.rmdir()

    manifest: dict[str, list[str]] = defaultdict(list)
    base = "http://localhost:8000/static/products"
    for p in sorted(ROOT.rglob("*")):
        if p.is_file() and p.suffix.lower() in EXTS:
            rel = p.relative_to(ROOT).as_posix()
            slug = p.relative_to(ROOT).parts[0]
            manifest[slug].append(f"{base}/{rel}")

    manifest_path = Path(__file__).resolve().parent.parent / "data" / "media_manifest.json"
    if not dry_run:
        manifest_path.write_text(
            json.dumps(dict(sorted(manifest.items())), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    actions["unique_files"] = len(by_hash)
    actions["slugs"] = len(manifest)
    return actions


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = organize(dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
