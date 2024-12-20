# Loud Pack Generator

## Description:

The goal of the **Loud Pack Generator** is to create a pack that can generate Minecraft resource packs that embody the volume of all the sounds of the game by doing it totally automatically.

The Python script comes in two versions:

1. `run.py`
2. `run_slow.py`

The first version of the script is optimized by using multithreading and multiprocessing to generate the pack really quickly. The downside is that it uses a lot of RAM, but this script is 4x quicker than the second.

## How to Use:

- The scripts have only been tested on **Windows**.
- Minecraft needs to be installed on your computer (any launcher will do! ;)).
- The desired version of the game needs to be launched at least once.
- To finalize the pack, you need to add the following files to your folder:
  - `pack.mcmeta` (you need to change the version number; use this table to select the right version: https://minecraft.fandom.com/wiki/Pack_format)
  - `pack.png` (a placeholder version is available in this folder).
- Finally, you need to zip the following folders inside your folder:
  - `assets` folder
  - `pack.mcmeta`
  - `pack.png`

## Copyright: This project is open source and is licensed under the *GNU General Public License*.
