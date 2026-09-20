#!/usr/bin/env python3
import argparse
import logging
import sys
from pathlib import Path
import requests

__APP_NAME__ = "loud-pack"
__VERSION__ = "1.0.0"
__LICENSE__ = """GNU General Public License v3.0

Copyright (C) 2026 TristanGrlt

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

MOJANG_MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"


class LicenseAction(argparse.Action):
    def __init__(
        self,
        option_strings,
        dest=argparse.SUPPRESS,
        default=argparse.SUPPRESS,
        help="Show license information and exit",
    ):
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help,
        )

    def __call__(self, parser, namespace, values, option_string=None):
        print(f"{__APP_NAME__} v{__VERSION__}\n")
        print(__LICENSE__)
        parser.exit()


def send_discord_webhook(webhook_url: str, message: str) -> None:
    """
    Dispatches a plaintext message to a Discord webhook for CI/CD monitoring.
    Fails silently to prevent pipeline interruption on network timeouts.
    """
    if not webhook_url:
        return
    try:
        response = requests.post(webhook_url, json={"content": message}, timeout=5)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        logging.error(f"Failed to dispatch Discord webhook: {err}")


def fetch_mojang_manifest() -> dict:
    """
    Retrieves the global v2 version manifest from Mojang's metadata servers.
    Contains pointers to individual version JSON endpoints.
    """
    logging.info(f"Fetching Mojang version manifest from {MOJANG_MANIFEST_URL}")
    try:
        response = requests.get(MOJANG_MANIFEST_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as err:
        logging.critical(f"Network failure while fetching Mojang manifest: {err}")
        sys.exit(1)


def resolve_version_metadata_url(target_version: str, manifest: dict) -> str:
    """
    Parses the manifest to find the metadata URL for the requested game version.
    Automatically resolves 'latest' and 'snapshot' aliases to their current IDs.
    """
    # Resolve aliases
    if target_version == "latest":
        target_version = manifest["latest"]["release"]
        logging.info(f"Resolved 'latest' to release version: {target_version}")
    elif target_version == "snapshot":
        target_version = manifest["latest"]["snapshot"]
        logging.info(f"Resolved 'snapshot' to latest snapshot: {target_version}")

    # Traverse version array to locate matching ID
    for version_entry in manifest["versions"]:
        if version_entry["id"] == target_version:
            logging.info(
                f"Successfully resolved metadata URL for version {target_version}"
            )
            return version_entry["url"]

    logging.critical(f"Version '{target_version}' not found in the Mojang manifest.")
    sys.exit(1)


def create_parser() -> argparse.ArgumentParser:
    description = (
        f"{__APP_NAME__} - Automated amplified Minecraft resource pack generator."
    )
    epilog = """Usage examples:
  %(prog)s -m latest -v 2.0
  %(prog)s --mc-version 24w14a --volume 3.0 --output-dir ./dist
  %(prog)s -m 1.20.4 --webhook-url "https://discord.com/api/webhooks/..."
  %(prog)s --license
"""

    parser = argparse.ArgumentParser(
        prog=__APP_NAME__,
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=True,
    )

    game_group = parser.add_argument_group("Minecraft & Audio Options")
    game_group.add_argument(
        "-m",
        "--mc-version",
        dest="mc_version",
        type=str,
        default="latest",
        metavar="VERSION",
        help="Target Minecraft version ('latest', 'snapshot', or explicit like '24w14a'). Default: %(default)s.",
    )
    game_group.add_argument(
        "-v",
        "--volume",
        dest="volume",
        type=float,
        default=2.0,
        metavar="FACTOR",
        help="Volume multiplier applied via SoX. Default: %(default)s.",
    )

    io_group = parser.add_argument_group("I/O & Monitoring Options")
    io_group.add_argument(
        "-o",
        "--output-dir",
        dest="output_dir",
        type=Path,
        default=Path("./build"),
        metavar="DIR",
        help="Output directory for the finalized ZIP archive. Default: %(default)s.",
    )
    io_group.add_argument(
        "-w",
        "--webhook-url",
        dest="webhook_url",
        type=str,
        default="",
        metavar="URL",
        help="Discord webhook URL for pipeline status reporting.",
    )
    io_group.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress standard informational logs.",
    )

    info_group = parser.add_argument_group("Information")
    info_group.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__VERSION__}",
        help="Show application version and exit.",
    )
    info_group.add_argument(
        "--license",
        action=LicenseAction,
    )

    return parser


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()

    log_level = logging.WARNING if args.quiet else logging.INFO
    logging.basicConfig(level=log_level, format="[%(levelname)s] %(message)s")

    logging.info(f"Initializing {__APP_NAME__} v{__VERSION__}")

    # 1. Fetch manifest and resolve version
    manifest = fetch_mojang_manifest()
    metadata_url = resolve_version_metadata_url(args.mc_version, manifest)

    send_discord_webhook(
        args.webhook_url,
        f"🚀 **{__APP_NAME__} v{__VERSION__}** pipeline initiated\n"
        f"Target Version: `{args.mc_version}` | Audio Multiplier: `{args.volume}x`\n"
        f"Metadata URL resolved successfully.",
    )


if __name__ == "__main__":
    main()
