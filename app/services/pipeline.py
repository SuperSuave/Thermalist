from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.config import AppConfig
from app.api.models.requests import RenderOptions
from app.renderers.label_bitmap import LabelData
from app.renderers.receipt_80mm import Receipt80mmRenderer
from app.services.exceptions import SourceFetchError
from app.services.registry import ModuleRegistry, OutputRegistry, SourceRegistry


class PrintPipeline:
    def __init__(self) -> None:
        self.source_registry = SourceRegistry()
        self.module_registry = ModuleRegistry()
        self.output_registry = OutputRegistry()
        self._label_bitmap_service = None

    def _get_label_bitmap_service(self, theme_name: str | None = None):
        from app.services.label_bitmap_service import LabelBitmapService

        if theme_name is None:
            if self._label_bitmap_service is None:
                self._label_bitmap_service = LabelBitmapService()
            return self._label_bitmap_service

        return LabelBitmapService(theme_name=theme_name)

    def _to_dict(self, value: Any) -> dict[str, Any]:
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        if hasattr(value, "model_dump"):
            return value.model_dump(exclude_none=True)
        return dict(value)

    def _create_renderer(
        self, render_config: dict[str, Any] | None = None
    ) -> Receipt80mmRenderer:
        cfg = self._to_dict(render_config)
        font = cfg.get("font", "A")
        default_width = 48 if font == "A" else 56
        width = cfg.get("width", default_width)
        return Receipt80mmRenderer(width=width)

    async def _resolve_payload(
        self,
        *,
        content: dict[str, Any] | None = None,
        source_name: str | None = None,
        source_config: dict[str, Any] | None = None,
        source_options: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], str | None]:
        if content is not None:
            return content, None
        if not source_name:
            raise ValueError("source_name is required when content is not provided")
        source = self.source_registry.create(source_name, source_config)
        payload = await source.fetch(**(source_options or {}))
        return payload, source_name

    def _use_bitmap_label(
        self,
        module_name: str,
        render_config: dict[str, Any] | Any | None,
        render_options: RenderOptions | dict[str, Any] | Any | None,
    ) -> bool:
        if module_name != "label":
            return False
        render_config_dict = self._to_dict(render_config)
        render_options_dict = self._to_dict(render_options)
        return (
            render_options_dict.get("mode") == "bitmap"
            or render_config_dict.get("renderer") == "label_bitmap"
        )

    async def _build_receipt(
        self,
        *,
        module_name: str,
        content: dict[str, Any] | None = None,
        source_name: str | None = None,
        source_config: dict[str, Any] | None = None,
        source_options: dict[str, Any] | None = None,
        render_config: dict[str, Any] | None = None,
        render_options: dict[str, Any] | None = None,
        timezone: str | None = None,
    ):
        payload, resolved_source = await self._resolve_payload(
            content=content,
            source_name=source_name,
            source_config=source_config,
            source_options=source_options,
        )
        if source_name and not payload.get("ok", True):
            raise SourceFetchError(
                f"Source '{resolved_source}' failed: {payload.get('error', 'unknown error')}"
            )
        module_payload = payload
        if source_name and module_name == "recipe":
            module_payload = {"recipe": payload.get("recipe")}
        module = self.module_registry.create(module_name)
        document = await module.build(
            module_payload,
            timezone=timezone,
            render_options=render_options or {},
        )
        renderer = self._create_renderer(render_config)
        receipt = renderer.render(document)
        return document, receipt, resolved_source

    def _build_label_data_from_content(
        self, content: dict[str, Any] | None
    ) -> LabelData:
        if not content:
            raise ValueError("content is required for bitmap label")
        today = datetime.now().strftime("%m/%d/%y")
        return LabelData(
            verb=content.get("verb", "Opened"),
            date_text=content.get("date", today),
            body=content.get("note") or content.get("text") or "",
            subtext=content.get("subtext"),
        )

    async def _preview_bitmap_label(
        self,
        module_name: str,
        content: dict[str, Any] | None,
        render_config: dict[str, Any] | None,
        render_options: dict[str, Any] | None,
        timezone: str | None,
        theme_name: str | None = None,
    ) -> dict[str, Any]:
        label_data = self._build_label_data_from_content(content)
        service = self._get_label_bitmap_service(theme_name=theme_name)
        render_config = render_config or {}
        label_name = render_config.get(
            "label_name", f"label-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        result = service.render_and_save(label_data, label_name=label_name)
        result.update(
            {"module": module_name, "mode": "bitmap", "label_data": label_data}
        )
        return result

    async def _send_bitmap_label(
        self,
        module_name: str,
        content: dict[str, Any] | None,
        output_kind: str,
        output_config: dict[str, Any] | None,
        render_config: dict[str, Any] | None,
        render_options: dict[str, Any] | None,
        timezone: str | None,
        theme_name: str | None = None,
    ) -> dict[str, Any]:
        label_data = self._build_label_data_from_content(content)
        service = self._get_label_bitmap_service(theme_name=theme_name)
        output_config = output_config or {}
        hostname = output_config.get("host", "192.168.86.9")
        port = output_config.get("port", 9100)
        result = service.render_and_print(label_data, host=hostname, port=port)
        result.update(
            {
                "module": module_name,
                "mode": "bitmap",
                "label_data": label_data,
                "host": hostname,
                "port": port,
            }
        )
        return result

    async def preview(
        self,
        module_name: str,
        content: dict[str, Any] | None = None,
        source_name: str | None = None,
        source_config: dict[str, Any] | None = None,
        source_options: dict[str, Any] | None = None,
        render_config: dict[str, Any] | None = None,
        render_options: dict[str, Any] | None = None,
        theme_name: str | None = None,
        timezone: str | None = None,
    ) -> dict[str, Any]:
        if self._use_bitmap_label(module_name, render_config, render_options):
            return await self._preview_bitmap_label(
                module_name=module_name,
                content=content,
                render_config=render_config,
                render_options=render_options,
                theme_name=theme_name,
                timezone=timezone,
            )
        document, receipt, resolved_source = await self._build_receipt(
            module_name=module_name,
            content=content,
            source_name=source_name,
            source_config=source_config,
            source_options=source_options,
            render_config=render_config,
            render_options=render_options,
            timezone=timezone,
        )
        return {
            "document": document.model_dump(),
            "receipt": receipt.model_dump(mode="json"),
            "source": resolved_source,
            "module": module_name,
        }

    async def send(
        self,
        module_name: str,
        content: dict[str, Any] | None = None,
        source_name: str | None = None,
        source_config: dict[str, Any] | None = None,
        source_options: dict[str, Any] | None = None,
        output_kind: str = "mock",
        output_config: dict[str, Any] | None = None,
        render_config: dict[str, Any] | None = None,
        render_options: dict[str, Any] | None = None,
        theme_name: str | None = None,
        timezone: str | None = None,
    ) -> dict[str, Any]:
        if self._use_bitmap_label(module_name, render_config, render_options):
            return await self._send_bitmap_label(
                module_name=module_name,
                content=content,
                output_kind=output_kind,
                output_config=output_config,
                render_config=render_config or output_config,
                render_options=render_options,
                theme_name=theme_name,
                timezone=timezone,
            )
        document, receipt, resolved_source = await self._build_receipt(
            module_name=module_name,
            content=content,
            source_name=source_name,
            source_config=source_config,
            source_options=source_options,
            render_config=render_config or output_config,
            render_options=render_options,
            timezone=timezone,
        )
        backend, cfg = self.output_registry.create(output_kind, output_config)
        result = backend.send(receipt, **cfg.model_dump(exclude_none=True))
        if isinstance(result, dict):
            result.setdefault("source", resolved_source)
            result.setdefault("module", module_name)
            result.setdefault("document", document.model_dump())
            return result
        return {
            "result": result,
            "source": resolved_source,
            "module": module_name,
            "document": document.model_dump(),
        }

    @staticmethod
    def _effective_output_config(
        app_config: AppConfig,
        body_output_config: dict[str, Any] | None,
    ) -> dict[str, Any]:
        base: dict[str, Any] = {
            "host": app_config.raw_tcp.host,
            "port": app_config.raw_tcp.port,
            "font": app_config.raw_tcp.font,
            "width": app_config.renderer.width,
            "cut": app_config.raw_tcp.cut,
            "initialize": app_config.raw_tcp.initialize,
            "dry_run": app_config.raw_tcp.dry_run,
        }
        if body_output_config:
            base.update(body_output_config)
        return base
