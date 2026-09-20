# LOUD-PACK

LOUD-PACK is a command-line utility and automated CI/CD pipeline designed to dynamically generate amplified Minecraft resource packs. It fetches original game assets directly from Mojang's servers, applies a configurable decibel gain to all audio files using SoX, and automatically publishes the packaged releases to Modrinth and CurseForge.

## Features

* **Dynamic Asset Retrieval:** Automatically resolves target game versions (including the absolute latest snapshots or releases) and downloads required `.ogg` audio assets concurrently, without requiring a local Minecraft client.
* **Multicore Audio Processing:** Utilizes Python's `ProcessPoolExecutor` to distribute audio amplification tasks across all available CPU cores via SoX, drastically reducing processing time.
* **Automated Packaging:** Generates valid Minecraft resource pack archives, dynamically mapping processed files to the `assets/minecraft/sounds/` structure and including repository metadata (`pack.mcmeta` and `pack.png`).
* **Platform Integrations:** Interacts with the Modrinth (Labrinth) and CurseForge APIs to check for existing versions, preventing duplicate work, and performs automated multipart uploads for new releases.
* **CI/CD Ready:** Designed to run statelessly in automated environments like GitHub Actions or Forgejo Runners, complete with Discord webhook monitoring.

## Requirements

* **Python 3.10+**
* **SoX (Sound eXchange):** Must be installed and available in the system PATH.
* **Nix (Optional):** A `flake.nix` is provided for a reproducible development environment.

## Installation

1. Clone the repository:
  ```bash
    git clone [https://github.com/yourusername/loud-pack.git](https://github.com/yourusername/loud-pack.git)
    cd loud-pack
  ```
2. If using Nix, initialize the development environment:
  ```bash
    nix develop
  ```
4. Otherwise, install the required Python dependencies manually:
  ```bash
    pip install requests
  ```

## Usage

LOUD-PACK is executed via the command line. It requires pack.mcmeta and pack.png to be present in the repository root to generate a valid resource pack.

### Basic Commands

Generate a pack for the latest available Minecraft version (snapshot or release) with the default +10.0 dB gain:
```bash
python main.py
```

Target a specific Minecraft version and increase the volume by 15 dB:
```bash
python main.py --mc-version 1.20.4 --volume 15.0
```

### Automated Publishing

To enable automated uploads, provide the respective project IDs via arguments and authenticate using environment variables.
```bash
export MODRINTH_TOKEN="your_modrinth_api_token"
export CURSEFORGE_TOKEN="your_curseforge_api_token"
export DISCORD_WEBHOOK="your_discord_webhook_url"

python main.py \
  --mc-version newest \
  --volume 10.0 \
  --modrinth-project <modrinth_id> \
  --curseforge-project <curseforge_id> \
  --webhook-url $DISCORD_WEBHOOK
```

### CLI Arguments

- `-m, --mc-version` Target Minecraft version (`newest`, `latest`, `snapshot`, or explicit like `1.20.4`). Default is newest.
- `-v, --volume`: Volume adjustment in decibels (dB). Default is `10.0`.
- `-o, --output-dir`: Output directory for downloaded and processed files. Default is `./build`.
- `-w, --webhook-url`: Discord webhook URL for pipeline status reporting.
- `--modrinth-project`: Modrinth Project ID.
- `--curseforge-project`: CurseForge Project ID.
- `-q, --quiet`: Suppress standard informational logs.
- `-V, --version`: Show application version and exit.
- `--license`: Show license information and exit.

## CI/CD Automation

This project includes a workflow file (e.g., `.github/workflows/pipeline.yml`) configured to run daily. It automatically checks Mojang's servers for new versions, compares them against your existing Modrinth and CurseForge releases, and executes the entire download, process, and publish pipeline if a new version is detected.

Ensure that `MODRINTH_TOKEN`, `CURSEFORGE_TOKEN`, and `DISCORD_WEBHOOK`are configured in your repository's CI/CD secrets.

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3).
