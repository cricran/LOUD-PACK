#!/usr/bin/env python3
import argparse
import logging
import sys
import os
import json
import concurrent.futures
import subprocess
import zipfile
from pathlib import Path
import requests

__APP_NAME__ = "LOUD-PACK"
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
ASSET_DOWNLOAD_BASE_URL = "https://resources.download.minecraft.net"
MODRINTH_API_URL = "https://api.modrinth.com/v2/version"


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
    if not webhook_url:
        return
    try:
        response = requests.post(webhook_url, json={"content": message}, timeout=5)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        logging.error(f"Failed to dispatch Discord webhook: {err}")


def fetch_mojang_manifest() -> dict:
    logging.info(f"Fetching Mojang version manifest from {MOJANG_MANIFEST_URL}")
    try:
        response = requests.get(MOJANG_MANIFEST_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as err:
        logging.critical(f"Network failure while fetching Mojang manifest: {err}")
        sys.exit(1)


def resolve_version_metadata_url(target_version: str, manifest: dict) -> str:
    if target_version == "latest":
        target_version = manifest["latest"]["release"]
        logging.info(f"Resolved 'latest' to release version: {target_version}")
    elif target_version == "snapshot":
        target_version = manifest["latest"]["snapshot"]
        logging.info(f"Resolved 'snapshot' to latest snapshot: {target_version}")

    for version_entry in manifest["versions"]:
        if version_entry["id"] == target_version:
            logging.info(
                f"Successfully resolved metadata URL for version {target_version}"
            )
            return version_entry["url"]

    logging.critical(f"Version '{target_version}' not found in the Mojang manifest.")
    sys.exit(1)


def fetch_version_metadata(metadata_url: str) -> dict:
    logging.info(f"Fetching version metadata from {metadata_url}")
    try:
        response = requests.get(metadata_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as err:
        logging.critical(f"Network failure while fetching version metadata: {err}")
        sys.exit(1)


def fetch_asset_index(asset_index_url: str) -> dict:
    logging.info(f"Fetching asset index from {asset_index_url}")
    try:
        response = requests.get(asset_index_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as err:
        logging.critical(f"Network failure while fetching asset index: {err}")
        sys.exit(1)


def filter_sound_assets(asset_objects: dict) -> dict:
    logging.info("Filtering asset index for sound files")
    sound_assets = {
        path: data["hash"]
        for path, data in asset_objects.items()
        if path.startswith("minecraft/sounds/")
    }
    logging.info(f"Found {len(sound_assets)} sound files to process")
    return sound_assets


def get_asset_url(asset_hash: str) -> str:
    return f"{ASSET_DOWNLOAD_BASE_URL}/{asset_hash[:2]}/{asset_hash}"


def download_single_asset(
    asset_path: str, asset_hash: str, base_output_dir: Path
) -> Path | None:
    target_file = base_output_dir / asset_path

    if target_file.exists():
        return target_file

    target_file.parent.mkdir(parents=True, exist_ok=True)
    url = get_asset_url(asset_hash)

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        target_file.write_bytes(response.content)
        return target_file
    except requests.exceptions.RequestException as err:
        logging.error(f"Failed to download {asset_path}: {err}")
        return None


def download_assets_concurrently(
    sound_assets: dict, output_dir: Path, threads: int = 16
) -> list[Path]:
    logging.info(
        f"Starting concurrent download of {len(sound_assets)} files using {threads} threads..."
    )
    downloaded_files = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {
            executor.submit(download_single_asset, path, hash_val, output_dir): path
            for path, hash_val in sound_assets.items()
        }

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                downloaded_files.append(result)

    return downloaded_files


def process_single_audio(input_file: Path, output_file: Path, volume_db: float) -> bool:
    if output_file.exists():
        return True

    output_file.parent.mkdir(parents=True, exist_ok=True)
    multiplier = 10 ** (volume_db / 20.0)
    multiplier_str = f"{multiplier:.4f}"

    cmd = ["sox", "-v", multiplier_str, str(input_file), str(output_file)]
    try:
        subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )
        return True
    except subprocess.CalledProcessError as err:
        logging.error(f"SoX failed on {input_file.name}: {err}")
        return False
    except FileNotFoundError:
        logging.critical(
            "SoX executable not found. Ensure it is installed and in your PATH."
        )
        sys.exit(1)


def process_audio_concurrently(
    downloaded_files: list[Path], raw_dir: Path, processed_dir: Path, volume_db: float
) -> int:
    logging.info(
        f"Starting audio amplification ({volume_db} dB) on {len(downloaded_files)} files..."
    )
    success_count = 0

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = []
        for input_file in downloaded_files:
            relative_path = input_file.relative_to(raw_dir)
            output_file = processed_dir / relative_path
            futures.append(
                executor.submit(
                    process_single_audio, input_file, output_file, volume_db
                )
            )

        for future in concurrent.futures.as_completed(futures):
            if future.result():
                success_count += 1

    logging.info(
        f"Successfully processed {success_count}/{len(downloaded_files)} audio files."
    )
    return success_count


def package_resource_pack(
    processed_dir: Path, output_zip: Path, repo_root: Path
) -> bool:
    logging.info(f"Packaging resource pack into {output_zip}...")
    try:
        with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in processed_dir.rglob("*"):
                if file_path.is_file():
                    arcname = f"assets/{file_path.relative_to(processed_dir)}"
                    zipf.write(file_path, arcname)

            pack_mcmeta = repo_root / "pack.mcmeta"
            pack_png = repo_root / "pack.png"

            if pack_mcmeta.exists():
                zipf.write(pack_mcmeta, "pack.mcmeta")

            if pack_png.exists():
                zipf.write(pack_png, "pack.png")

        logging.info(f"Successfully created resource pack archive: {output_zip}")
        return True
    except Exception as err:
        logging.error(f"Failed to package resource pack: {err}")
        return False


def upload_to_modrinth(
    zip_path: Path, mc_version: str, project_id: str, token: str
) -> str | None:
    """
    Uploads the finalized ZIP archive to a Modrinth project using the Labrinth API.
    """
    logging.info(f"Uploading {zip_path.name} to Modrinth project '{project_id}'...")

    # Classify as alpha if it's a snapshot (contains 'w' or 'pre' or 'rc')
    version_type = (
        "alpha" if any(x in mc_version for x in ["w", "pre", "rc"]) else "release"
    )

    data_payload = {
        "name": f"{__APP_NAME__} [ {mc_version} ]",
        "version_number": mc_version,
        "game_versions": [mc_version],
        "version_type": version_type,
        "loaders": ["minecraft"],
        "project_id": project_id,
        "file_parts": ["file"],
        "dependencies": [],
    }

    headers = {"Authorization": token}

    try:
        with open(zip_path, "rb") as f:
            files = {"file": (zip_path.name, f, "application/zip")}
            response = requests.post(
                MODRINTH_API_URL,
                headers=headers,
                data={"data": json.dumps(data_payload)},
                files=files,
                timeout=300,
            )

            response.raise_for_status()
            result = response.json()

            modrinth_url = (
                f"https://modrinth.com/project/{project_id}/version/{result['id']}"
            )
            logging.info(
                f"Successfully uploaded to Modrinth! Version URL: {modrinth_url}"
            )
            return modrinth_url

    except requests.exceptions.RequestException as err:
        logging.error(f"Failed to upload to Modrinth: {err}")
        if hasattr(err, "response") and err.response is not None:
            logging.error(f"Modrinth API response: {err.response.text}")
        return None


def create_parser() -> argparse.ArgumentParser:
    description = (
        f"{__APP_NAME__} - Automated amplified Minecraft resource pack generator."
    )
    epilog = """Usage examples:
  %(prog)s -m latest -v 10.0
  %(prog)s --mc-version 24w14a --modrinth-project a1b2c3d4
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
        help="Target Minecraft version ('latest', 'snapshot', or explicit). Default: %(default)s.",
    )
    game_group.add_argument(
        "-v",
        "--volume",
        dest="volume",
        type=float,
        default=10.0,
        metavar="DECIBELS",
        help="Volume adjustment in decibels (dB). Default: %(default)s.",
    )

    io_group = parser.add_argument_group("I/O & Monitoring Options")
    io_group.add_argument(
        "-o",
        "--output-dir",
        dest="output_dir",
        type=Path,
        default=Path("./build"),
        metavar="DIR",
        help="Output directory for files. Default: %(default)s.",
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

    publish_group = parser.add_argument_group("Publishing Options")
    publish_group.add_argument(
        "--modrinth-project",
        dest="modrinth_project",
        type=str,
        default="",
        metavar="ID",
        help="Modrinth Project ID (Requires MODRINTH_TOKEN env variable).",
    )

    misc_group = parser.add_argument_group("Miscellaneous")
    misc_group.add_argument("-q", "--quiet", action="store_true", help="Suppress logs.")
    misc_group.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {__VERSION__}"
    )
    misc_group.add_argument("--license", action=LicenseAction)

    return parser


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()

    log_level = logging.WARNING if args.quiet else logging.INFO
    logging.basicConfig(level=log_level, format="[%(levelname)s] %(message)s")

    logging.info(f"Initializing {__APP_NAME__} v{__VERSION__}")

    manifest = fetch_mojang_manifest()
    metadata_url = resolve_version_metadata_url(args.mc_version, manifest)

    version_metadata = fetch_version_metadata(metadata_url)
    asset_index_url = version_metadata["assetIndex"]["url"]

    asset_index = fetch_asset_index(asset_index_url)
    sound_assets = filter_sound_assets(asset_index["objects"])

    if not sound_assets:
        logging.error("No sound assets found for this version. Aborting.")
        sys.exit(1)

    raw_assets_dir = args.output_dir / "raw_assets"
    processed_assets_dir = args.output_dir / "processed_assets"

    downloaded_files = download_assets_concurrently(sound_assets, raw_assets_dir)

    if downloaded_files:
        process_audio_concurrently(
            downloaded_files, raw_assets_dir, processed_assets_dir, args.volume
        )

        zip_filename = args.output_dir / f"{__APP_NAME__}-{args.mc_version}.zip"
        repo_root = Path.cwd()
        package_success = package_resource_pack(
            processed_assets_dir, zip_filename, repo_root
        )

        modrinth_url = None
        if package_success and args.modrinth_project:
            modrinth_token = os.environ.get("MODRINTH_TOKEN")
            if modrinth_token:
                modrinth_url = upload_to_modrinth(
                    zip_filename, args.mc_version, args.modrinth_project, modrinth_token
                )
            else:
                logging.warning(
                    "Modrinth project ID provided, but MODRINTH_TOKEN environment variable is missing. Skipping Modrinth upload."
                )

        webhook_msg = (
            f"📦 **{__APP_NAME__} v{__VERSION__}** pipeline complete\n"
            f"Target Version: `{args.mc_version}` | Gain: `+{args.volume} dB`"
        )
        if modrinth_url:
            webhook_msg += f"\n✅ Successfully published to Modrinth: {modrinth_url}"

        send_discord_webhook(args.webhook_url, webhook_msg)


if __name__ == "__main__":
    main()
