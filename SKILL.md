---
name: stock-fetch
description: Use when a task needs stock media assets - search and download free-license images, videos, music or sound effects from Pixabay/Mixkit into a local asset library. Not for AI generation (use image/video generation skills) or GIF stickers.
---

# stock-fetch

Search free-license stock media (real footage, not AI-generated) and download it into a type-based asset library: `assets/images`, `assets/video`, `assets/bgm` (music), `assets/audio` (sound effects). The library root is `./assets` by default — override with `STOCK_FETCH_ROOT` or `--dest`.

## Usage

Script `scripts/stock_fetch.py` (pure standard library, JSON on stdout):

```bash
# search only (JSON with URLs + license info)
python scripts/stock_fetch.py search -q "sunset ocean" --kind image -n 5

# search videos and download top 2 → assets/video/
python scripts/stock_fetch.py get -q "city timelapse" --kind video -n 2

# music / sound effects (mixkit, no key needed)
python scripts/stock_fetch.py get -q "upbeat corporate" --kind music -n 3   # → bgm/
python scripts/stock_fetch.py get -q "click" --kind sfx -n 3                # → audio/

# pick a source / override destination
python scripts/stock_fetch.py get -q "forest" --kind image --source pixabay --dest images/nature
```

## Sources & keys

| Source | Media | Key | Notes |
|---|---|---|---|
| pixabay | images + videos | free key required | put `PIXABAY_API_KEY=xxx` in `scripts/.env` or export it; apply at https://pixabay.com/api/docs/ ; 100 req/60s, no bulk downloading |
| mixkit | videos + music + SFX | none | parses search pages; 1080p direct links inferred from the fixed naming pattern |
| wikimedia | CC / public-domain images | none | keep attribution; reachability varies by network |

`--source auto` (default): image/video → pixabay (needs key); music/sfx → mixkit.

Returned JSON: `search` → `results[]` with `url` and `license`; `get` → `items[]` with `saved` path and `bytes`, failures carry `error`.

## Boundaries

- AI-generated media → use image/video *generation* skills instead.
- This skill only retrieves real-world stock assets.
