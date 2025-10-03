#!/bin/bash
# compile the python script into a standalone x64 .exe
# exe will appear in ./dist

# clean previous builds
rm -rf ./build ./dist

./resources/generate_ico.sh

# build with PyInstaller
pyinstaller --onefile --windowed BatchSchemEdit.py \
  --add-data "minecraft_blocks.txt;." \
  --add-data "mc-materials.csv;." \
  --icon=resources/BatchSchemEdit.ico
