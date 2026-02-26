#!/usr/bin/env python3
import argparse
import json
import shutil
from pathlib import Path
from typing import Optional, Set


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".mkv", ".avi"}


def safe_game_title(folder_name: str) -> str:
    return folder_name.strip() or "Unknown game"


def is_hidden(path: Path) -> bool:
    return path.name.startswith(".")


def copy_folder(src: Path, dest: Path, overwrite: bool) -> None:
    if dest.exists():
        if not overwrite:
            return
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    for item in src.rglob("*"):
        if is_hidden(item):
            continue
        if not item.is_file():
            continue
        if item.suffix.lower() not in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS:
            continue
        rel = item.relative_to(src)
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)


def select_media_file(game_dir: Path, extensions: Set[str], preferred_stems: Set[str]) -> Optional[str]:
    candidates = []
    for item in game_dir.rglob("*"):
        if not item.is_file():
            continue
        if item.suffix.lower() not in extensions:
            continue
        if is_hidden(item):
            continue
        candidates.append(item)

    for item in candidates:
        if item.stem.lower() in preferred_stems:
            return item.relative_to(game_dir).as_posix()
    if candidates:
        return candidates[0].relative_to(game_dir).as_posix()
    return None


def ensure_game_json(game_dir: Path) -> None:
    json_path = game_dir / "game.json"
    if json_path.exists():
        return

    cover = select_media_file(game_dir, IMAGE_EXTENSIONS, {"cover", "box", "front"})
    video = select_media_file(game_dir, VIDEO_EXTENSIONS, {"video", "trailer", "preview"})
    data = {"title": safe_game_title(game_dir.name)}
    if cover:
        data["cover"] = cover
    if video:
        data["video"] = video
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")


def import_roms(console: str, source_dir: Path, library_dir: Path, overwrite: bool) -> int:
    if not source_dir.exists() or not source_dir.is_dir():
        raise SystemExit(f"Source directory not found: {source_dir}")

    console_dir = library_dir / console
    console_dir.mkdir(parents=True, exist_ok=True)

    for game_dir in sorted(source_dir.iterdir(), key=lambda p: p.name.lower()):
        if not game_dir.is_dir() or is_hidden(game_dir):
            continue
        dest_dir = console_dir / game_dir.name
        copy_folder(game_dir, dest_dir, overwrite=overwrite)
        ensure_game_json(dest_dir)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Import ROM folders into library/ (metadata + media)")
    parser.add_argument("console", help="Console name (folder name under library)")
    parser.add_argument("source", help="Path to ROM folders (each game is a folder)")
    parser.add_argument("--library", default="library", help="Library directory")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing game folders",
    )
    args = parser.parse_args()

    return import_roms(args.console, Path(args.source), Path(args.library), args.overwrite)


if __name__ == "__main__":
    raise SystemExit(main())
