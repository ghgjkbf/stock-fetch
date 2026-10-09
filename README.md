# stock-fetch

English | [中文](README.zh-CN.md)

**Search and download free-license stock media from the command line — images, videos, music, and sound effects — into a type-based local asset library.**

Built for AI-agent workflows: when a task needs real-world footage or assets (not AI-generated ones), the agent runs this script, gets JSON back, and the files are already filed under the right folder.

## Why

Free stock sites are scattered and network-reachable from some machines but not others. stock-fetch is deliberately small:

- **Two working sources, one command.** Pixabay (official API, free key) covers images + videos; Mixkit (no key, page parsing) covers videos + music + SFX.
- **Type-based filing.** Downloads land in `assets/images | video | bgm | audio` automatically, so an asset library stays organized without manual moves.
- **License info in the output.** Every result carries its license string; agents can cite it without a second lookup.
- **Zero dependencies.** Pure Python standard library, JSON on stdout, exit codes that behave.

## Quick start

```bash
# search only
python scripts/stock_fetch.py search -q "sunset ocean" --kind image -n 5

# download top 2 matching videos
python scripts/stock_fetch.py get -q "city timelapse" --kind video -n 2

# music and sound effects (no key needed)
python scripts/stock_fetch.py get -q "upbeat corporate" --kind music -n 3
python scripts/stock_fetch.py get -q "click" --kind sfx -n 3
```

Result JSON:

```json
{
  "ok": true,
  "downloaded": 1,
  "failed": 0,
  "items": [
    {
      "source": "mixkit",
      "type": "video",
      "url": "https://assets.mixkit.co/videos/41576/41576-1080.mp4",
      "license": "Mixkit License (free for commercial use, no attribution)",
      "saved": "assets/video/mixkit_sunset_80676.mp4",
      "bytes": 187175135
    }
  ]
}
```

## Configuration

| Setting | How |
|---|---|
| Pixabay key | free key from [pixabay.com/api/docs](https://pixabay.com/api/docs/) — put `PIXABAY_API_KEY=xxx` in `scripts/.env`, or export the env var |
| Asset library root | `STOCK_FETCH_ROOT` env var, else `./assets` relative to the working directory |
| Env file location | `STOCK_FETCH_ENV` env var, else `scripts/.env` next to the script |
| Destination override | `--dest video/city` (relative to the library root) |

Rate limits: Pixabay allows 100 requests / 60 seconds and forbids systematic bulk downloading — this tool is for picking a handful of assets per task, not mirroring the catalog.

## Sources

| Source | Media | Key | Notes |
|---|---|---|---|
| [Pixabay](https://pixabay.com/) | images + videos | free key | official API, safe-search on |
| [Mixkit](https://mixkit.co/) | videos + music + SFX | none | search-page parsing; 1080p links inferred from the fixed naming pattern |
| [Wikimedia Commons](https://commons.wikimedia.org/) | CC / public-domain images | none | fallback via `--source wikimedia`; keep attribution |

## Use as an agent skill

`SKILL.md` is included, so `npx skills add <this repo>` (or any skill loader that reads SKILL.md) can expose it to your agent directly.

## License

Apache-2.0
