from __future__ import annotations

from pathlib import Path

from PIL import Image

try:
    from escpos.printer import Network
except Exception:
    Network = None

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
    if Network is None:
        raise RuntimeError("python-escpos is not installed. Cannot print.")

    printer = Network(host=host, port=port)
    printer.image(
        image,
        high_density_vertical=True,
        high_density_horizontal=True,
        impl="bitImageRaster",
        fragment_height=960,
        center=center,
    )
    printer.cut()
    printer.close()

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
