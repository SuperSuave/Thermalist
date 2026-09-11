from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.config import AppConfig
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
        if not value:
            return {}
        if isinstance(value, dict):
            return value
        if hasattr(value, "model_dump"):
            return value.model_dump(exclude_none=True)
        return dict(value)

    def _use_bitmap_label(
        self,
        module_name: str,
        render_config: Any,
        render_options: Any,
    ) -> bool:
        if module_name != "label":
            return False
        cfg = self._to_dict(render_config)
        opts = self._to_dict(render_options)
        return opts.get("mode") == "bitmap" or cfg.get("renderer") == "label_bitmap"

    def _create_renderer(self, render_config: dict[str, Any] | None = None) -> Receipt80mmRenderer:
        rcfg = self._to_dict(render_config)
        font = rcfg.get("font", "A")
        return Receipt80mmRenderer(width=rcfg.get("width", 48 if font == "A" else 56))

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
            content=content, source_name=source_name, source_config=source_config, source_options=source_options
        )
        if source_name and not payload.get("ok", True):
            raise SourceFetchError(f"Source '{resolved_source}' failed: {payload.get('error', 'unknown error')}")

        module_payload = {"recipe": payload.get("recipe")} if (source_name and module_name == "recipe") else payload
        module = self.module_registry.create(module_name)
        document = await module.build(module_payload, timezone=timezone, render_options=render_options or {})
        renderer = self._create_renderer(render_config)
        receipt = renderer.render(document)
        return document, receipt, resolved_source

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
            cnt = content or {}
            label_data = LabelData(
                verb=cnt.get("verb", "Opened"),
                date_text=cnt.get("date", datetime.now().strftime("%m/%d/%y")),
                body=cnt.get("note") or cnt.get("text") or "",
                subtext=cnt.get("subtext"),
            )
            service = self._get_label_bitmap_service(theme_name=theme_name)
            label_name = (render_config or {}).get("label_name", f"label-{datetime.now().strftime('%Y%m%d%H%M%S')}")
            res = service.render_and_save(label_data, label_name=label_name)
            res.update({"module": module_name, "mode": "bitmap", "label_data": label_data})
            return res

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
        output_kind: str = "raw_tcp",
        output_config: dict[str, Any] | None = None,
        render_config: dict[str, Any] | None = None,
        render_options: dict[str, Any] | None = None,
        theme_name: str | None = None,
        timezone: str | None = None,
    ) -> dict[str, Any]:
        if self._use_bitmap_label(module_name, render_config, render_options):
            cnt = content or {}
            label_data = LabelData(
                verb=cnt.get("verb", "Opened"),
                date_text=cnt.get("date", datetime.now().strftime("%m/%d/%y")),
                body=cnt.get("note") or cnt.get("text") or "",
                subtext=cnt.get("subtext"),
            )
            service = self._get_label_bitmap_service(theme_name=theme_name)
            out_cfg = output_config or {}
            host = out_cfg.get("host", "192.168.86.9")
            port = out_cfg.get("port", 9100)
            res = service.render_and_print(label_data, host=host, port=port)
            res.update({"module": module_name, "mode": "bitmap", "label_data": label_data, "host": host, "port": port})
            return res

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

        if output_kind == "mock":
            return {
                "status": "ok",
                "backend": "mock",
                "preview": receipt.text_preview,
                "source": resolved_source,
                "module": module_name,
                "document": document.model_dump(),
            }

        backend, cfg = self.output_registry.create(output_kind, output_config)
        res = backend.send(receipt, **cfg.model_dump(exclude_none=True))
        if isinstance(res, dict):
            res.setdefault("source", resolved_source)
            res.setdefault("module", module_name)
            res.setdefault("document", document.model_dump())
            return res
        return {"result": res, "source": resolved_source, "module": module_name, "document": document.model_dump()}

    @staticmethod
    def _effective_output_config(app_config: AppConfig, body_output_config: dict[str, Any] | None) -> dict[str, Any]:
        base = {
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
