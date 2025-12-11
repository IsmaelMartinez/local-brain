#!/usr/bin/env python3
"""Sync version across all plugin.json files from local_brain/__init__.py.

This ensures the library version, plugin version, and marketplace version
are always in sync.
"""

import json
import re
from pathlib import Path


def get_version_from_init() -> str:
    """Extract version from local_brain/__init__.py."""
    init_file = Path(__file__).parent.parent / "local_brain" / "__init__.py"
    content = init_file.read_text()
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if not match:
        raise ValueError("Could not find __version__ in __init__.py")
    return match.group(1)


def update_plugin_json(path: Path, version: str) -> None:
    """Update version in a plugin.json file."""
    if not path.exists():
        print(f"⚠️  Skipping {path} (not found)")
        return

    data = json.loads(path.read_text())
    old_version = data.get("version", "unknown")
    data["version"] = version

    path.write_text(json.dumps(data, indent=2) + "\n")

    if old_version != version:
        print(
            f"✓ Updated {path.relative_to(Path.cwd())} from {old_version} to {version}"
        )
    else:
        print(f"✓ {path.relative_to(Path.cwd())} already at {version}")


def main() -> None:
    """Sync version across all plugin.json files."""
    root = Path(__file__).parent.parent
    version = get_version_from_init()

    print(f"Source version: {version} (from local_brain/__init__.py)\n")

    plugin_files = [
        root / "local-brain" / "plugin.json",
        root / "local-brain" / ".claude-plugin" / "plugin.json",
    ]

    for plugin_file in plugin_files:
        update_plugin_json(plugin_file, version)

    print(f"\n✓ All versions synced to {version}")


if __name__ == "__main__":
    main()
