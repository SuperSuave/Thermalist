from __future__ import annotations

from pathlib import Path
import socket

from PIL import Image

from app.renderers.label_bitmap import (
    FontSet,
    LabelBitmapRenderer,
    LabelData,
    LabelThemeName,
    get_theme,
)

APP_DIR = Path(__file__).resolve().parent.parent
GENERATED_IMAGE_DIR = APP_DIR / "generated_images"


def prepare_for_print(image: Image.Image, threshold: int = 180) -> Image.Image:
    gray = image.convert("L")
    return gray.point(lambda p: 255 if p > threshold else 0, mode="1")


def save_label_preview(
    image: Image.Image, label_name: str, threshold: int = 180
) -> dict:
    safe_name = Path(label_name).name
    if not safe_name or safe_name in (".", ".."):
        safe_name = "label"
    output_base = GENERATED_IMAGE_DIR / safe_name
    output_base.parent.mkdir(parents=True, exist_ok=True)

    gray_path = output_base.with_suffix(".png")
    bw_path = output_base.with_name(output_base.stem + "-bw").with_suffix(".png")

    image.save(gray_path)
    prepare_for_print(image, threshold=threshold).save(bw_path)

    return {
        "gray_path": f"/generated_images/{gray_path.name}",
        "bw_path": f"/generated_images/{bw_path.name}",
        "width": image.width,
        "height": image.height,
    }


def print_label_network(
    image: Image.Image, host: str, port: int = 9100, center: bool = False
) -> dict:
    bw = prepare_for_print(image)
    width, height = bw.size

    width_bytes = (width + 7) // 8
    header = b"\x1d\x76\x30\x00" + width_bytes.to_bytes(2, "little") + height.to_bytes(2, "little")

    raster_data = bytearray()
    for y in range(height):
        row = bytearray(width_bytes)
        for x in range(width):
            pixel = bw.getpixel((x, y))
            if pixel == 0:
                byte_idx = x // 8
                bit_idx = 7 - (x % 8)
                row[byte_idx] |= (1 << bit_idx)
        raster_data.extend(row)

    payload = b"\x1b\x40" + header + bytes(raster_data) + b"\x1d\x56\x00"

    with socket.create_connection((host, port), timeout=10) as sock:
        sock.sendall(payload)

    return {
        "status": "printed",
        "host": host,
        "port": port,
        "width": image.width,
        "height": image.height,
        "module": "label",
    }


class LabelBitmapService:
    def __init__(
        self,
        theme_name: LabelThemeName | str = LabelThemeName.FRAMED_FOOD,
        title_font_path: str | None = None,
        body_font_path: str | None = None,
    ):
        if isinstance(theme_name, str):
            theme_name = LabelThemeName(theme_name)

        self.theme = get_theme(theme_name)
        self.fonts = FontSet(title_path=title_font_path, body_path=body_font_path)
        self.renderer = LabelBitmapRenderer(theme=self.theme, fonts=self.fonts)

    def render_label(self, data: LabelData | dict) -> Image.Image:
        if isinstance(data, dict):
            data = LabelData(**data)
        return self.renderer.render(data)

    def render_and_save(self, data: LabelData, label_name: str) -> dict:
        image = self.render_label(data)
        return save_label_preview(image, label_name, self.theme.threshold)

    def render_and_print(self, data: LabelData | dict, host: str, port: int = 9100) -> dict:
        image = self.render_label(data)
        return print_label_network(image, host=host, port=port)
