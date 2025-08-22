from nbtschematic import SchematicFile
sf = SchematicFile.load('C:/Users/Max1M/curseforge/minecraft/Instances/neoforge 1.12.1 camboi shaders/config/worldedit/schematics/jerusalem_tower_short.schem')
schematic = sf["Schematic"].schema

print("The block at Y=%d, Z=%d, X=%d has block ID %d" %
(2, 3, 0, sf.blocks[2, 3, 0]))