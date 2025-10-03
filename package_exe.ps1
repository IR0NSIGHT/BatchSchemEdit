# build.ps1
# compile the python script into a standalone x64 .exe
# exe will appear in .\dist

# clean previous builds (ignore errors if folders don't exist)
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

# build with PyInstaller
pyinstaller --onefile --windowed SchemBlockReplacer.py `
  --add-data "minecraft_blocks.txt;." `
  --add-data "mc-materials.csv;."
