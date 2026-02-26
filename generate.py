#!/usr/bin/env python3
import argparse
import json
import shutil
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Optional


ROM_EXTENSIONS = {
    ".nes",
    ".sfc",
    ".smc",
    ".gb",
    ".gbc",
    ".gba",
    ".gen",
    ".md",
    ".sms",
    ".gg",
    ".pce",
    ".iso",
    ".cue",
    ".chd",
    ".zip",
    ".7z",
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def safe_slug(text: str) -> str:
    out = []
    for ch in text.lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in {" ", "-", "_", "."}:
            out.append("-")
    slug = "".join(out).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "item"


def is_hidden(path: Path) -> bool:
    return path.name.startswith(".")


def read_game_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def resolve_media_path(game_dir: Path, media_value: Optional[str]) -> Optional[Path]:
    if not media_value:
        return None
    media_path = (game_dir / media_value).resolve()
    if media_path.exists():
        return media_path
    return None


def copy_media(media_path: Path, game_dir: Path, assets_dir: Path) -> Path:
    rel_path = media_path.relative_to(game_dir)
    dest_path = assets_dir / rel_path
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(media_path, dest_path)
    return dest_path


def find_console_entries(console_dir: Path) -> list[Path]:
    entries = []
    for entry in console_dir.iterdir():
        if is_hidden(entry):
            continue
        if entry.is_dir() or (entry.is_file() and entry.suffix.lower() in ROM_EXTENSIONS):
            entries.append(entry)
    return sorted(entries, key=lambda p: p.name.lower())


def build_library(library_dir: Path, out_dir: Path) -> dict:
    consoles = []
    assets_dir = out_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    for console_dir in sorted(library_dir.iterdir(), key=lambda p: p.name.lower()):
        if not console_dir.is_dir() or is_hidden(console_dir):
            continue

        console_name = console_dir.name
        console_slug = safe_slug(console_name)
        games = []

        for entry in find_console_entries(console_dir):
            if entry.is_dir():
                game_dir = entry
                data = read_game_json(game_dir / "game.json")
                title = data.get("title") or game_dir.name
                cover_path = resolve_media_path(game_dir, data.get("cover"))
                video_path = resolve_media_path(game_dir, data.get("video"))
                cover_rel = None
                video_rel = None

                if cover_path:
                    dest_dir = assets_dir / console_slug / safe_slug(title)
                    dest_path = copy_media(cover_path, game_dir, dest_dir)
                    cover_rel = dest_path.relative_to(out_dir).as_posix()

                if video_path:
                    dest_dir = assets_dir / console_slug / safe_slug(title)
                    dest_path = copy_media(video_path, game_dir, dest_dir)
                    video_rel = dest_path.relative_to(out_dir).as_posix()

                games.append(
                    {
                        "title": title,
                        "year": data.get("year"),
                        "publisher": data.get("publisher"),
                        "region": data.get("region"),
                        "tags": data.get("tags") or [],
                        "notes": data.get("notes"),
                        "cover": cover_rel,
                        "video": video_rel,
                        "source": str(game_dir.relative_to(library_dir)),
                    }
                )
            else:
                games.append(
                    {
                        "title": entry.stem,
                        "year": None,
                        "publisher": None,
                        "region": None,
                        "tags": [],
                        "notes": None,
                        "cover": None,
                        "video": None,
                        "source": str(entry.relative_to(library_dir)),
                    }
                )

        consoles.append(
            {
                "name": console_name,
                "slug": console_slug,
                "games": games,
            }
        )

    generated_at = datetime.now(timezone.utc).isoformat()
    return {"generated_at": generated_at, "consoles": consoles}


def render_html(library: dict) -> str:
    total_games = sum(len(c["games"]) for c in library["consoles"])
    lines = []
    lines.append("<!doctype html>")
    lines.append("<html lang=\"fr\">")
    lines.append("<head>")
    lines.append("  <meta charset=\"utf-8\">")
    lines.append("  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">")
    lines.append("  <title>Bibliotheque retrogaming</title>")
    lines.append("  <style>")
    lines.append("    body { font-family: Arial, sans-serif; margin: 24px; }")
    lines.append("    header { margin-bottom: 24px; }")
    lines.append("    .console { margin-bottom: 32px; }")
    lines.append("    .games { display: grid; gap: 12px; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); }")
    lines.append("    .game { border: 1px solid #ddd; border-radius: 8px; padding: 12px; }")
    lines.append("    .game h3 { margin: 8px 0 6px; font-size: 16px; }")
    lines.append("    .meta { color: #555; font-size: 13px; margin: 4px 0; }")
    lines.append("    .tags { color: #666; font-size: 12px; }")
    lines.append("    img.cover { width: 100%; height: auto; border-radius: 6px; }")
    lines.append("    video.preview { width: 100%; border-radius: 6px; }")
    lines.append("  </style>")
    lines.append("</head>")
    lines.append("<body>")
    lines.append("  <header>")
    lines.append("    <h1>Bibliotheque retrogaming</h1>")
    lines.append(f"    <p>Total : {total_games} jeux</p>")
    lines.append("  </header>")

    if not library["consoles"]:
        lines.append("  <p>Aucun jeu pour le moment. Ajoutez des dossiers dans library/ et relancez la generation.</p>")

    for console in library["consoles"]:
        lines.append("  <section class=\"console\">")
        lines.append(f"    <h2>{escape(console['name'])} ({len(console['games'])})</h2>")
        lines.append("    <div class=\"games\">")
        for game in console["games"]:
            lines.append("      <article class=\"game\">")
            if game["cover"]:
                lines.append(
                    f"        <img class=\"cover\" src=\"{escape(game['cover'])}\" alt=\"{escape(game['title'])}\">"
                )
            if game["video"]:
                lines.append(
                    "        <video class=\"preview\" controls preload=\"metadata\">"
                    f"<source src=\"{escape(game['video'])}\"></video>"
                )
            lines.append(f"        <h3>{escape(game['title'])}</h3>")
            meta = []
            if game["year"]:
                meta.append(str(game["year"]))
            if game["publisher"]:
                meta.append(str(game["publisher"]))
            if game["region"]:
                meta.append(str(game["region"]))
            if meta:
                lines.append(f"        <div class=\"meta\">{' - '.join(escape(m) for m in meta)}</div>")
            if game["tags"]:
                tags = ", ".join(escape(str(t)) for t in game["tags"])
                lines.append(f"        <div class=\"tags\">{tags}</div>")
            if game["notes"]:
                lines.append(f"        <p class=\"meta\">{escape(str(game['notes']))}</p>")
            lines.append("      </article>")
        lines.append("    </div>")
        lines.append("  </section>")

    lines.append("</body>")
    lines.append("</html>")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate retrogaming library website.")
    parser.add_argument("--library", default="library", help="Input library directory")
    parser.add_argument("--out", default="dist", help="Output directory")
    args = parser.parse_args()

    library_dir = Path(args.library)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not library_dir.exists():
        library_dir.mkdir(parents=True, exist_ok=True)

    library = build_library(library_dir, out_dir)

    (out_dir / "library.json").write_text(
        json.dumps(library, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )

    (out_dir / "index.html").write_text(render_html(library), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
