from __future__ import annotations

import argparse
import json
import shutil
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Set, Tuple


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src"
MARKET_CONFIG_PATH = ROOT / "market-config.json"
SCAN_SUFFIX = ".market.json"


class MarketError(Exception):
    pass


@dataclass(frozen=True)
class MarketConfig:
    market_name: str
    market_version: str
    index_file: str
    download_root: str


@dataclass(frozen=True)
class PluginEntry:
    name: str
    display_name: str
    author: str
    description: str
    version: str
    required_market_version: str
    channel: str
    targets: List[str]
    download_urls: List[str]
    dependencies: List[str]
    repository_url: str | None
    entry: str | None
    metadata_file: Path

    def is_compatible_with_market(self, market_version: str) -> bool:
        return self.version == market_version and self.required_market_version == market_version

    def as_index_item(self, market_version: str) -> Dict[str, object]:
        return {
            "name": self.name,
            "displayName": self.display_name,
            "author": self.author,
            "description": self.description,
            "version": self.version,
            "requiredMarketVersion": self.required_market_version,
            "currentMarketVersion": market_version,
            "isCompatibleWithCurrentMarket": self.is_compatible_with_market(market_version),
            "channel": self.channel,
            "targets": self.targets,
            "downloadUrls": self.download_urls,
            "dependencies": self.dependencies,
            "repositoryUrl": self.repository_url,
            "entry": self.entry,
        }


def read_json(path: Path) -> Dict[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise MarketError(f"File not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MarketError(f"Invalid JSON in {path}: {exc}") from exc


def normalize_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MarketError(f"{field_name} must be a non-empty string.")
    return value.strip()


def normalize_list(value: object, field_name: str) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise MarketError(f"{field_name} must be a non-empty string or a list of strings.")
    return [item.strip() for item in value]


def load_market_config() -> MarketConfig:
    defaults = {
        "marketName": "mdt Plugin Market",
        "marketVersion": "v1",
        "indexFile": "plugin-market.json",
        "downloadRoot": "downloads",
    }
    if MARKET_CONFIG_PATH.exists():
        data = read_json(MARKET_CONFIG_PATH)
        for key, default_value in defaults.items():
            defaults[key] = normalize_text(data.get(key, default_value), key)

    return MarketConfig(
        market_name=defaults["marketName"],
        market_version=defaults["marketVersion"],
        index_file=defaults["indexFile"],
        download_root=defaults["downloadRoot"],
    )


def validate_download_target(raw: str) -> None:
    value = raw.strip()
    if not value:
        raise MarketError("downloadUrls contains an empty value.")

    parsed = urllib.parse.urlparse(value)
    if parsed.scheme:
        if parsed.scheme not in {"http", "https", "file"}:
            raise MarketError(f"Unsupported download protocol: {parsed.scheme}")
        if not parsed.path or parsed.path.endswith("/"):
            raise MarketError(f"Download URLs must point to a file, not a directory: {value}")
        if parsed.scheme in {"http", "https"} and parsed.path == "/":
            raise MarketError(f"Download URLs cannot point to a site homepage: {value}")
        return

    local_path = Path(value)
    if not local_path.is_absolute():
        raise MarketError(f"Local download paths must be absolute: {value}")
    if value.endswith("\\") or value.endswith("/"):
        raise MarketError(f"Local download paths must point to a file: {value}")


def discover_metadata_files() -> List[Path]:
    if not SOURCE_ROOT.exists():
        return []
    return sorted(path for path in SOURCE_ROOT.rglob(f"*{SCAN_SUFFIX}") if path.is_file())


def load_entry(path: Path) -> PluginEntry:
    data = read_json(path)

    name = normalize_text(data.get("name"), "name")
    display_name = normalize_text(data.get("displayName", name), "displayName")
    author = normalize_text(data.get("author"), "author")
    description = normalize_text(data.get("description"), "description")
    version = normalize_text(data.get("version"), "version")
    required_market_version = normalize_text(data.get("requiredMarketVersion", version), "requiredMarketVersion")
    channel = normalize_text(data.get("channel", path.parent.name), "channel").lower()
    if channel not in {"modded", "native"}:
        raise MarketError(f"{path} channel must be modded or native.")
    if path.parent.name.lower() != channel:
        raise MarketError(f"{path} folder does not match channel {channel}.")

    download_urls = normalize_list(data.get("downloadUrls"), "downloadUrls")
    for item in download_urls:
        validate_download_target(item)

    return PluginEntry(
        name=name,
        display_name=display_name,
        author=author,
        description=description,
        version=version,
        required_market_version=required_market_version,
        channel=channel,
        targets=normalize_list(data.get("targets"), "targets"),
        download_urls=download_urls,
        dependencies=normalize_list(data.get("dependencies"), "dependencies"),
        repository_url=normalize_text(data.get("repositoryUrl"), "repositoryUrl") if data.get("repositoryUrl") else None,
        entry=normalize_text(data.get("entry"), "entry") if data.get("entry") else None,
        metadata_file=path,
    )


def load_market() -> Tuple[MarketConfig, Dict[str, PluginEntry]]:
    market_config = load_market_config()
    entries: Dict[str, PluginEntry] = {}

    for path in discover_metadata_files():
        entry = load_entry(path)
        if entry.name in entries:
            raise MarketError(f"Duplicate plugin name: {entry.name}")
        entries[entry.name] = entry

    for entry in entries.values():
        missing_dependencies = [name for name in entry.dependencies if name not in entries]
        if missing_dependencies:
            raise MarketError(
                f"Plugin {entry.name} has missing dependencies: {', '.join(missing_dependencies)}"
            )

    return market_config, entries


def build_index(market_config: MarketConfig, entries: Dict[str, PluginEntry]) -> Dict[str, object]:
    ordered = [entries[name].as_index_item(market_config.market_version) for name in sorted(entries)]
    return {
        "schemaVersion": 1,
        "marketName": market_config.market_name,
        "marketVersion": market_config.market_version,
        "pluginCount": len(ordered),
        "plugins": ordered,
    }


def resolve_download_root(market_config: MarketConfig) -> Path:
    root = Path(market_config.download_root)
    return root if root.is_absolute() else ROOT / root


def sanitize_filename(url_or_path: str) -> str:
    parsed = urllib.parse.urlparse(url_or_path)
    name = Path(parsed.path).name if parsed.scheme else Path(url_or_path).name
    if not name:
        raise MarketError(f"Could not infer a filename from {url_or_path}")
    return name


def download_file(url_or_path: str, destination: Path) -> Path:
    parsed = urllib.parse.urlparse(url_or_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    if parsed.scheme in {"http", "https"}:
        with urllib.request.urlopen(url_or_path) as response:
            destination.write_bytes(response.read())
        return destination

    source = None
    if parsed.scheme == "file":
        source = Path(urllib.request.url2pathname(parsed.path))
    elif Path(url_or_path).is_absolute():
        source = Path(url_or_path)

    if source is None:
        raise MarketError(f"Could not resolve local download path: {url_or_path}")
    if not source.exists():
        raise MarketError(f"Download source does not exist: {source}")
    if source.is_dir():
        raise MarketError(f"Download source must be a file: {source}")

    shutil.copy2(source, destination)
    return destination


def resolve_dependencies(entries: Dict[str, PluginEntry], name: str, ordered: List[PluginEntry], seen: Set[str]) -> None:
    if name in seen:
        return
    if name not in entries:
        raise MarketError(f"Plugin not found: {name}")
    seen.add(name)
    entry = entries[name]
    for dependency in entry.dependencies:
        resolve_dependencies(entries, dependency, ordered, seen)
    ordered.append(entry)


def validate_installable(entry: PluginEntry, market_config: MarketConfig) -> None:
    if entry.is_compatible_with_market(market_config.market_version):
        return
    raise MarketError(
        f"Plugin {entry.name} requires market version {entry.required_market_version} "
        f"and plugin version {entry.version}, but the current market version is "
        f"{market_config.market_version}. Use --force-install to continue."
    )


def download_entry(entry: PluginEntry, market_config: MarketConfig, force_install: bool) -> List[Path]:
    if not force_install:
        validate_installable(entry, market_config)

    target_dir = resolve_download_root(market_config) / entry.name / entry.version
    saved_files: List[Path] = []
    for url in entry.download_urls:
        saved_files.append(download_file(url, target_dir / sanitize_filename(url)))

    metadata_copy = target_dir / f"{entry.name}.market.json"
    metadata_copy.write_text(
        json.dumps(entry.as_index_item(market_config.market_version), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    saved_files.append(metadata_copy)
    return saved_files


def cmd_scan(market_config: MarketConfig, entries: Dict[str, PluginEntry]) -> int:
    if not entries:
        print("No plugin metadata files were found.")
        return 0

    print(f"Scan complete. Found {len(entries)} plugins for market version {market_config.market_version}:")
    for name in sorted(entries):
        entry = entries[name]
        status = "compatible" if entry.is_compatible_with_market(market_config.market_version) else "incompatible"
        targets = ", ".join(entry.targets) if entry.targets else "-"
        print(f"- {entry.name} | {entry.version} | {entry.channel} | {status} | targets: {targets}")
    return 0


def cmd_build_index(market_config: MarketConfig, entries: Dict[str, PluginEntry]) -> int:
    index_path = ROOT / market_config.index_file
    index_path.write_text(
        json.dumps(build_index(market_config, entries), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Index generated: {index_path}")
    return 0


def cmd_download(market_config: MarketConfig, entries: Dict[str, PluginEntry], plugin_name: str, force_install: bool) -> int:
    order: List[PluginEntry] = []
    resolve_dependencies(entries, plugin_name, order, set())
    for entry in order:
        saved_files = download_entry(entry, market_config, force_install)
        print(f"Downloaded {entry.name} -> {resolve_download_root(market_config) / entry.name / entry.version}")
        for saved in saved_files:
            print(f"  {saved}")
    return 0


def cmd_download_all(market_config: MarketConfig, entries: Dict[str, PluginEntry], force_install: bool) -> int:
    for name in sorted(entries):
        cmd_download(market_config, entries, name, force_install)
    return 0


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="mdt plugin market scanner and downloader")
    parser.add_argument(
        "--force-install",
        "--force",
        action="store_true",
        dest="force_install",
        help="Skip market-version checks and download anyway.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("scan", help="Scan plugin metadata from src/")
    subparsers.add_parser("build-index", help="Generate the market index file")

    download_parser = subparsers.add_parser("download", help="Download one plugin and its dependencies")
    download_parser.add_argument("name", help="Plugin name")

    subparsers.add_parser("download-all", help="Download all plugins")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    market_config, entries = load_market()

    if args.command == "scan":
        return cmd_scan(market_config, entries)
    if args.command == "build-index":
        return cmd_build_index(market_config, entries)
    if args.command == "download":
        return cmd_download(market_config, entries, args.name, args.force_install)
    if args.command == "download-all":
        return cmd_download_all(market_config, entries, args.force_install)
    raise MarketError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MarketError as exc:
        print(f"[plugin-market] {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
