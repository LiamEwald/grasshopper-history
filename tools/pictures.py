"""Turn the corner captures from capture.py into the version's pictures.

Of the four corners, keep the one that shows the most red (so a change on the north
side is seen from the north), crop to the building, and save at one size as WebP.
"""
import json
import os

from PIL import Image

SIZE = (1200, 900)
PAD = 0.06
SIDES = ["se", "sw", "ne", "nw"]  # se first: it wins ties


def red_pixels(img):
    r, g, b, a = img.split()
    return sum(1 for pr, pg, pb, pa in zip(r.getdata(), g.getdata(), b.getdata(), a.getdata())
               if pa > 0 and pr > 120 and pr > pg + 60 and pr > pb + 60)


def finish(img, out):
    """Crop to the building, centre it on white at SIZE."""
    box = img.split()[3].getbbox() or (0, 0) + img.size
    img = img.crop(box)
    w, h = img.size
    scale = min(SIZE[0] * (1 - 2 * PAD) / w, SIZE[1] * (1 - 2 * PAD) / h)
    img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    canvas = Image.new("RGB", SIZE, (255, 255, 255))
    canvas.paste(img, ((SIZE[0] - img.width) // 2, (SIZE[1] - img.height) // 2), img)
    canvas.save(out, "WEBP", quality=86)


def best(tmp, prefix):
    """(side, image, red count) of the corner showing the most red."""
    found = []
    for side in SIDES:
        path = os.path.join(tmp, "%s-%s.png" % (prefix, side))
        if os.path.exists(path):
            img = Image.open(path).convert("RGBA")
            small = img.resize((img.width // 4, img.height // 4))
            found.append((red_pixels(small), -SIDES.index(side), side, img))
    if not found:
        return None, None, 0
    count, _, side, img = max(found, key=lambda f: (f[0], f[1]))
    return side, img, count


def take(rhino, tmp, folder, red, removed, inside):
    """Capture, then write picture.webp (and inside.webp) into folder.
    Returns {picture, inside, side} with file names or None."""
    for f in os.listdir(tmp):
        if f.startswith("cap-"):
            os.remove(os.path.join(tmp, f))
    with open(os.path.join(tmp, "capture.json"), "w", encoding="utf-8") as f:
        json.dump({"changed": red, "removed": removed, "inside": inside}, f)
    res = rhino.run("capture.py", "capture-result.json") or {}
    out = {"picture": None, "inside": None, "side": None}
    if not res.get("ok"):
        return out
    side, img, count = best(tmp, "cap")
    in_side, in_img, in_count = best(tmp, "cap-inside") if inside else (None, None, 0)
    # The outside picture is kept unless the change only shows from inside.
    if img is not None and (count or not in_count or not red):
        finish(img, os.path.join(folder, "picture.webp"))
        out["picture"], out["side"] = "picture.webp", side
    if in_img is not None and in_count:
        finish(in_img, os.path.join(folder, "inside.webp"))
        out["inside"] = "inside.webp"
        out["side"] = out["side"] or in_side
    return out
