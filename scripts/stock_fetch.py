#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stock-fetch: search & download free-license stock media (Pixabay / Mixkit)
into a local asset library with type-based subdirectories.

Pure standard library. JSON on stdout.

Sources (verified 2026-10-09):
  - pixabay  : official API, free key required (env PIXABAY_API_KEY, or a
               `.env` file next to this script / pointed to by STOCK_FETCH_ENV)
               images + videos, 100 req/60s; no systematic bulk downloading
  - mixkit   : no key, parses search pages for direct asset URLs;
               videos / music / sound effects

Falls back gracefully when a source is unreachable and reports per-item errors.
"""
import argparse
import json
import os
import re
import ssl
import sys
import urllib.parse
import urllib.request

# Asset library root: override with STOCK_FETCH_ROOT, else ./assets
ASSETS_ROOT = os.environ.get("STOCK_FETCH_ROOT",
                             os.path.join(os.getcwd(), "assets"))
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
SUBDIR = {"image": "images", "video": "video", "music": "bgm", "sfx": "audio"}
CTX = ssl.create_default_context()


def _env_file():
    if os.environ.get("STOCK_FETCH_ENV"):
        return os.environ["STOCK_FETCH_ENV"]
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")


def _read_key():
    key = os.environ.get("PIXABAY_API_KEY", "")
    if key:
        return key
    env = _env_file()
    if os.path.isfile(env):
        for line in open(env, encoding="utf-8"):
            line = line.strip()
            if line.startswith("PIXABAY_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _get(url, timeout=30, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as resp:
        return resp.read()


def _ext_of(url):
    path = urllib.parse.urlparse(url).path
    ext = os.path.splitext(path)[1].lower()
    return ext if ext in (".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mp3", ".wav") else ""


def _safe_name(query, url, prefix=""):
    base = re.sub(r'[\\/:*?"<>|\s]+', "_", query)[:40] or "asset"
    ext = _ext_of(url) or (".mp4" if "/videos/" in url else ".jpg")
    return f"{prefix}{base}_{abs(hash(url)) % 100000:05d}{ext}"


def _save(url, subdir, name, timeout=180):
    dest_dir = os.path.join(ASSETS_ROOT, subdir)
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, name)
    data = _get(url, timeout=timeout)
    with open(dest, "wb") as f:
        f.write(data)
    return dest, len(data)


# ---------------------------------------------------------------- pixabay
def pixabay_search(query, kind, limit):
    key = _read_key()
    if not key:
        return {"ok": False, "error": "missing PIXABAY_API_KEY (free key: "
                "https://pixabay.com/api/docs/ ; put 'PIXABAY_API_KEY=xxx' in "
                f"{_env_file()} or export the env var)"}
    endpoint = "videos" if kind == "video" else ""
    url = (f"https://pixabay.com/api/{endpoint}/?key={key}&q={urllib.parse.quote(query)}"
           f"&per_page={min(limit, 50)}&safesearch=true")
    try:
        data = json.loads(_get(url))
    except Exception as e:
        return {"ok": False, "error": f"pixabay request failed: {e}"}
    out = []
    if kind == "video":
        for hit in data.get("hits", [])[:limit]:
            v = hit.get("videos", {})
            best = v.get("large") or v.get("medium") or v.get("small") or {}
            if best.get("url"):
                out.append({"source": "pixabay", "type": "video", "url": best["url"],
                            "width": best.get("width"), "height": best.get("height"),
                            "duration": hit.get("duration"), "tags": hit.get("tags", ""),
                            "license": "Pixabay License (free for commercial use, no attribution)"})
    else:
        for hit in data.get("hits", [])[:limit]:
            out.append({"source": "pixabay", "type": "image", "url": hit.get("largeImageURL"),
                        "width": hit.get("imageWidth"), "height": hit.get("imageHeight"),
                        "tags": hit.get("tags", ""),
                        "license": "Pixabay License (free for commercial use, no attribution)"})
    return {"ok": True, "results": out}


# ---------------------------------------------------------------- mixkit
def mixkit_search(query, kind, limit):
    if kind == "image":
        return {"ok": False, "error": "mixkit has no images; kind must be video/music/sfx"}
    path = {"video": "free-stock-video", "music": "free-stock-music",
            "sfx": "free-sound-effects"}.get(kind)
    if not path:
        return {"ok": False, "error": "kind must be image/video/music/sfx"}
    url = f"https://mixkit.co/{path}/?q={urllib.parse.quote(query)}"
    try:
        page = _get(url, timeout=30).decode("utf-8", "replace")
    except Exception as e:
        return {"ok": False, "error": f"mixkit request failed: {e}"}
    out = []
    if kind == "video":
        seen = set()
        for m in re.finditer(r'https://assets\.mixkit\.co/videos/(\d+)/\1-(\d{3,4})\.mp4', page):
            vid = m.group(1)
            if vid in seen:
                continue
            seen.add(vid)
            # Search pages embed a 360p preview; the 1080p tier follows the
            # same fixed naming pattern (verified 2026-10-09).
            best = f"https://assets.mixkit.co/videos/{vid}/{vid}-1080.mp4"
            out.append({"source": "mixkit", "type": "video", "url": best,
                        "preview": m.group(0),
                        "license": "Mixkit License (free for commercial use, no attribution)"})
            if len(out) >= limit:
                break
    else:
        for m in re.finditer(r'https://assets\.mixkit\.co/[^"\\]+\.(?:mp3|wav)', page):
            u = m.group(0)
            if u in {r["url"] for r in out}:
                continue
            out.append({"source": "mixkit", "type": "audio",
                        "url": u, "license": "Mixkit License (free for commercial use, no attribution)"})
            if len(out) >= limit:
                break
    return {"ok": True, "results": out}


# ---------------------------------------------------------------- wikimedia
def wikimedia_search(query, limit):
    api = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&formatversion=2"
           f"&generator=search&gsrsearch={urllib.parse.quote(query)}%20filetype:bitmap"
           f"&gsrlimit={min(limit, 30)}&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=1600")
    try:
        data = json.loads(_get(api, timeout=25))
    except Exception as e:
        return {"ok": False, "error": f"wikimedia request failed: {e}"}
    out = []
    for page in (data.get("query", {}) or {}).get("pages", [])[:limit]:
        info = (page.get("imageinfo") or [{}])[0]
        lic = ((info.get("extmetadata") or {}).get("LicenseShortName") or {}).get("value", "")
        if info.get("thumburl"):
            out.append({"source": "wikimedia", "type": "image", "url": info["thumburl"],
                        "license": f"CC / public domain ({lic}; keep attribution)"})
    return {"ok": True, "results": out}


# ---------------------------------------------------------------- main
def main():
    p = argparse.ArgumentParser(description="Search / download free-license stock media")
    p.add_argument("action", choices=["search", "get"], help="search=list only; get=download top N")
    p.add_argument("--query", "-q", required=True, help="search term (any language, English works best)")
    p.add_argument("--kind", choices=["image", "video", "music", "sfx"], default="image")
    p.add_argument("--source", choices=["pixabay", "mixkit", "wikimedia", "auto"], default="auto")
    p.add_argument("--limit", "-n", type=int, default=5)
    p.add_argument("--dest", help="override destination directory (default: <assets root>/<kind subdir>)")
    args = p.parse_args()

    if args.source == "auto":
        sources = ["pixabay"] if args.kind in ("image", "video") else ["mixkit"]
    else:
        sources = [args.source]

    merged = []
    errors = []
    for src in sources:
        if src == "pixabay":
            r = pixabay_search(args.query, "video" if args.kind == "video" else "image", args.limit)
        elif src == "mixkit":
            r = mixkit_search(args.query, args.kind, args.limit)
        else:
            r = wikimedia_search(args.query, args.limit)
        if r.get("ok"):
            merged += r["results"]
        else:
            errors.append(r["error"])
    merged = merged[:args.limit]

    if args.action == "search":
        out = {"ok": bool(merged) or not errors, "query": args.query, "kind": args.kind,
               "count": len(merged), "results": merged}
        if errors:
            out["errors"] = errors
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    if not merged:
        print(json.dumps({"ok": False, "error": "no results",
                          "errors": errors or None}, ensure_ascii=False, indent=2))
        return
    subdir = args.dest or SUBDIR.get(args.kind, "images")
    downloaded = []
    for item in merged:
        try:
            name = _safe_name(args.query, item["url"], prefix=f"{item['source']}_")
            dest, size = _save(item["url"], subdir, name)
            downloaded.append({**item, "saved": dest, "bytes": size})
        except Exception as e:
            downloaded.append({**item, "error": str(e)})
    ok_n = sum(1 for d in downloaded if "saved" in d)
    print(json.dumps({"ok": ok_n > 0, "downloaded": ok_n, "failed": len(downloaded) - ok_n,
                      "items": downloaded}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
