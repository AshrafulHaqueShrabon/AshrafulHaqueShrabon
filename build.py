#!/usr/bin/env python3
"""Retro README builder (Python 3.11+, standard library only).

    python build.py               build README.md + static images (offline, deterministic)
    python build.py --check       validate profile.toml and print a checklist
    python build.py --fetch-icons also download skill icons that aren't vendored yet
    python build.py --live        fetch GitHub languages, render the output-branch images

Everything is generated from profile.toml; see SETUP.md.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

if sys.version_info < (3, 11):
    sys.exit("build.py needs Python 3.11 or newer (for tomllib).")

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from scripts import config as config_mod  # noqa: E402
from scripts import icons  # noqa: E402
from scripts.check import report  # noqa: E402
from scripts.sections.arcade import levels  # noqa: E402
from scripts.style import accent  # noqa: E402


def build_static(cfg, readme_path: Path, assets_dir: Path) -> None:
    from scripts.readme import build
    result = build(cfg)
    assets_dir.mkdir(parents=True, exist_ok=True)
    keep = set(result.static)
    for old in assets_dir.glob("*.svg"):
        if old.name not in keep:
            old.unlink()
    for name, svg in sorted(result.static.items()):
        path = assets_dir / name
        if not path.exists() or path.read_text(encoding="utf-8") != svg:
            path.write_text(svg, encoding="utf-8")
    readme_path.write_text(result.readme, encoding="utf-8")
    errors = sum(i.level == "error" for i in cfg.issues)
    warns = sum(i.level == "warn" for i in cfg.issues)
    shown = assets_dir.resolve()
    shown = shown.relative_to(ROOT) if shown.is_relative_to(ROOT) else shown
    print(f"wrote {readme_path.name} and {len(result.static)} images in {shown}"
          + (f"  ({errors} error(s), {warns} warning(s): run `python build.py --check`)" if errors or warns else ""))


def fetch_icons(cfg_path: Path) -> None:
    try:
        icons.update_registry()
    except Exception as exc:  # network trouble: keep the vendored registry
        print(f"icons: registry not refreshed ({exc})")
    cfg = config_mod.load(cfg_path)
    for _, items in cfg.skills:
        for slug, _ in items:
            if not icons.available(slug):
                try:
                    print(f"icons: downloaded {icons.fetch(slug).name}")
                except Exception as exc:
                    print(f"icons: could not fetch '{slug}' ({exc}); a placeholder is shown")


def live(cfg, args) -> int:
    from scripts import dynamic
    from scripts.live.refresh import load_cache, refresh, save_cache
    if not cfg.github_username:
        print("live: profile.github_username is empty; nothing to publish")
        return 0
    previous = Path(args.previous) if args.previous else None
    cache_path = Path(args.cache) if args.cache else (previous / "cache" / "live.json" if previous else None)
    now = (datetime.fromisoformat(args.now.replace("Z", "+00:00")) if args.now
           else datetime.now(timezone.utc).replace(microsecond=0))
    print(f"live refresh for {cfg.github_username} ({'offline' if args.offline else 'online'})")
    cache, source = refresh(cfg, load_cache(cache_path), offline=args.offline,
                            token=os.environ.get("GITHUB_TOKEN") or None, now=now)
    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    (out / "cache").mkdir(parents=True)
    files = dynamic.render(cfg, source, arcade_dir=Path(args.arcade_dir) if args.arcade_dir else None,
                           previous=previous)
    for name, svg in files.items():
        (out / name).write_text(svg, encoding="utf-8")
    save_cache(cache, out / "cache" / "live.json")
    (out / "README.md").write_text(dynamic.BRANCH_README, encoding="utf-8")
    print(f"wrote {len(files)} images and cache/live.json to {out}")
    return 0


def print_settings(cfg, keys: str) -> None:
    """key=value lines for the workflow ($GITHUB_OUTPUT)."""
    values = {
        "arcade": cfg.arcade if cfg.github_username else "",
        "username": cfg.github_username,
        "snake_light": accent(cfg.accent, "light"),
        "snake_dark": accent(cfg.accent, "dark"),
        "dots_light": ",".join(levels(cfg.accent, "light")),
        "dots_dark": ",".join(levels(cfg.accent, "dark")),
    }
    for key in keys.split(","):
        print(f"{key.strip()}={values.get(key.strip(), '')}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default=str(ROOT / "profile.toml"), help="profile file (default: profile.toml)")
    parser.add_argument("--check", action="store_true", help="validate the profile and print a checklist")
    parser.add_argument("--fetch-icons", action="store_true", help="download skill icons that are missing")
    parser.add_argument("--live", action="store_true", help="refresh live data and render output-branch images")
    parser.add_argument("--offline", action="store_true", help="with --live: use the cache only, no network")
    parser.add_argument("--previous", help="with --live: previous output branch checkout (cache + images)")
    parser.add_argument("--cache", help="with --live: cache file to read (default: <previous>/cache/live.json)")
    parser.add_argument("--arcade-dir", help="with --live: folder with freshly generated game SVGs")
    parser.add_argument("--out", default=str(ROOT / "out" / "output"), help="with --live: output folder")
    parser.add_argument("--readme", default=str(ROOT / "README.md"), help=argparse.SUPPRESS)
    parser.add_argument("--assets", default=str(ROOT / "assets" / "generated"), help=argparse.SUPPRESS)
    parser.add_argument("--print", dest="print_keys", help=argparse.SUPPRESS)
    parser.add_argument("--now", help=argparse.SUPPRESS)  # fixed clock for previews/tests
    args = parser.parse_args(argv)

    cfg_path = Path(args.config)
    if args.fetch_icons:
        fetch_icons(cfg_path)
    cfg = config_mod.load(cfg_path)
    if args.print_keys:
        print_settings(cfg, args.print_keys)
        return 0
    if args.check:
        text, errors = report(cfg)
        print(text)
        return 1 if errors else 0
    if any(i.field == "file" for i in cfg.issues):
        print(report(cfg)[0])
        return 1
    if args.live:
        return live(cfg, args)
    build_static(cfg, Path(args.readme), Path(args.assets))
    return 0


if __name__ == "__main__":
    sys.exit(main())
