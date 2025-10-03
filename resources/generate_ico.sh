#!/bin/bash

# Original PNG
SRC="resources/BatchSchemEdit-Icon_256.png"

# Output folder (same as source)
OUT="resources"

# Sizes to generate
sizes=(16 32 48 64 128 256)

# Loop through sizes and resize
for size in "${sizes[@]}"; do
    magick "$SRC" -resize "${size}x${size}" "$OUT/BatchSchemEdit-Icon_${size}.png"
    echo "Generated $OUT/BatchSchemEdit-Icon_${size}.png"
done

echo "All icon sizes generated."

magick resources/BatchSchemEdit-Icon_16.png \
       resources/BatchSchemEdit-Icon_32.png \
       resources/BatchSchemEdit-Icon_48.png \
       resources/BatchSchemEdit-Icon_64.png \
       resources/BatchSchemEdit-Icon_128.png \
       resources/BatchSchemEdit-Icon_256.png \
       resources/BatchSchemEdit.ico
