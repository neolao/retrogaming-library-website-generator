# Retrogaming library website generator

This project generates a static website from console folders.

## Quick start

1. Add console folders and games in `library/`
2. Run the generator

Command:

```
python3 generate.py
```

The site is generated in `dist/` (file `index.html`).

## Library structure

Each console folder contains games. A game is usually a folder with metadata and media files (no ROMs in `library/`).

Example:

```
library/
  SNES/
    Super Metroid/
      game.json
      cover.jpg
```

Example `game.json`:

```
{
  "title": "Super Metroid",
  "year": 1994,
  "publisher": "Nintendo",
  "region": "PAL",
  "tags": ["action", "adventure"],
  "notes": "Original cartridge",
  "cover": "cover.jpg",
  "video": "preview.mp4"
}
```

## Updating the library

Add or update your folders, then run:

```
python3 generate.py
```

## Import ROM folders

If your ROMs are stored in one folder per game, you can import them like this:

```
python3 import_roms.py "SNES" "/path/to/roms/SNES"
```

It will create `library/SNES/<game-folder>/`, copy only images/videos, and add a minimal `game.json`. Use `--overwrite` to replace existing game folders.
