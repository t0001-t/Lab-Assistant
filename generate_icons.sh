#!/bin/bash
# generate_icons.sh
SOURCE="assets/icon.png"
mkdir -p assets/icons

for size in 72 96 128 144 152 192 384 512; do
  sips -z $size $size "$SOURCE" --out "assets/icon-${size}.png"
  echo "Generated icon-${size}.png"
done

# Für Apple Touch Icons (2x)
for size in 72 96 128 152 192; do
  sips -z $((size*2)) $((size*2)) "$SOURCE" --out "assets/icon-${size}@2x.png"
done

echo "All icons generated in assets/"
