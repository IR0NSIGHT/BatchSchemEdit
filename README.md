# Batch Schem Edit
With this python program, you can load many .schem files at once, replace block types in all of them and the save back to schem.

## Requirements
python installed on system
python dependecy manager like pip

## Start program
```commandline
pip install -r requirements.txt
python SchemBlockReplacer.py
```

1. load .schem files 
2. select which blocks to replace. empty replacements will be ignored
    - copy paste with ctrl+c ctrl+v
    - save and load settings to/from file to be able to reuse the exact replacements
3. run "replace blocks" to edit loaded schematics
4. save to original or as a copy