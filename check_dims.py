from PIL import Image
import os

# Check original source image
src = "/tmp/pixartek_proj_flores-blancas_1.png"
img = Image.open(src)
print(f"Source image: {img.size[0]}x{img.size[1]}, ratio: {img.size[0]/img.size[1]:.3f}")

# Check display file
disp = "/tmp/pixartek_display.png"
if os.path.exists(disp):
    d = Image.open(disp)
    print(f"Display file: {d.size[0]}x{d.size[1]}, ratio: {d.size[0]/d.size[1]:.3f}")

print(f"Projector: 1024x768, ratio: {1024/768:.3f}")
