# generate_icons.py
from PIL import Image
from pathlib import Path

SOURCE = Path("assets/icon.png")
OUTPUT_DIR = Path("assets")
OUTPUT_DIR.mkdir(exist_ok=True)

sizes = [72, 96, 128, 144, 152, 192, 384, 512]

with Image.open(SOURCE) as img:
    for size in sizes:
        resized = img.resize((size, size), Image.LANCZOS)
        output_path = OUTPUT_DIR / f"icon-{size}.png"
        resized.save(output_path, "PNG", optimize=True)
        print(f"Generated {output_path}")

print("All icons generated!")
