#!/bin/bash
# compile the python script into a standalone x64 .exe
# exe will appear in ./dist

# clean previous builds
rm -rf ./build ./dist

# build with PyInstaller
pyinstaller --onefile --windowed SchemBlockReplacer.py \
  --add-data "minecraft_blocks.txt;." \
  --add-data "mc-materials.csv;."
